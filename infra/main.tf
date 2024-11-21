locals {
  tags                = { azd-env-name : var.environment_name }
  location            = var.location
  resource_group_name = "${var.environment_name}-rg"
}

resource "random_string" "random" {
  length  = 4
  special = false
  lower   = true
  upper   = false
}

# Deploy resource group
resource "azurerm_resource_group" "default" {
  name     = local.resource_group_name
  location = local.location
  // Tag the resource group with the azd environment name
  // This should also be applied to all resources created in this module
  tags = local.tags
}

resource "azurerm_virtual_network" "default" {
  name                = "${var.environment_name}-vnet"
  location            = azurerm_resource_group.default.location
  resource_group_name = azurerm_resource_group.default.name
  address_space       = ["10.0.0.0/16"]
}

resource "azurerm_subnet" "default" {
  name                 = "${var.environment_name}-subnet"
  resource_group_name  = azurerm_resource_group.default.name
  virtual_network_name = azurerm_virtual_network.default.name
  address_prefixes     = ["10.0.0.0/21"]
}

resource "azurerm_network_security_group" "default" {
  name                = "${var.environment_name}-nsg"
  location            = azurerm_resource_group.default.location
  resource_group_name = azurerm_resource_group.default.name
}

resource "azurerm_network_security_rule" "https" {
  name                        = "${var.environment_name}-https"
  priority                    = 100
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_port_range           = "*"
  destination_port_range      = "443"
  source_address_prefix       = "*"
  destination_address_prefix  = "*"
  resource_group_name         = azurerm_resource_group.default.name
  network_security_group_name = azurerm_network_security_group.default.name
}

resource "azurerm_network_security_rule" "http" {
  name                        = "${var.environment_name}-http"
  priority                    = 101
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_port_range           = "*"
  destination_port_range      = "80"
  source_address_prefix       = "*"
  destination_address_prefix  = "*"
  resource_group_name         = azurerm_resource_group.default.name
  network_security_group_name = azurerm_network_security_group.default.name
}

# resource "azurerm_subnet_network_security_group_association" "default" {
#   subnet_id                 = azurerm_subnet.default.id
#   network_security_group_id = azurerm_network_security_group.default.id
# }

resource "azurerm_log_analytics_workspace" "default" {
  name                = "${var.environment_name}-log-analytics"
  location            = azurerm_resource_group.default.location
  resource_group_name = azurerm_resource_group.default.name
}

resource "azurerm_container_app_environment" "default" {
  name                     = "${var.environment_name}-aca-env"
  location                 = azurerm_resource_group.default.location
  resource_group_name      = azurerm_resource_group.default.name
  infrastructure_subnet_id = azurerm_subnet.default.id

  log_analytics_workspace_id = azurerm_log_analytics_workspace.default.id
}

resource "azurerm_container_registry" "acr" {
  name                = "${var.environment_name}${random_string.random.result}acr"
  resource_group_name = azurerm_resource_group.default.name
  location            = azurerm_resource_group.default.location
  sku                 = "Basic"
}

resource "azurerm_user_assigned_identity" "acr" {
  name                = "${var.environment_name}-acr-identity"
  resource_group_name = azurerm_resource_group.default.name
  location            = azurerm_resource_group.default.location
}

resource "azurerm_role_assignment" "acr_reader" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.acr.principal_id
}

resource "azurerm_container_app" "default" {
  name                         = "${var.environment_name}-app"
  container_app_environment_id = azurerm_container_app_environment.default.id
  resource_group_name          = azurerm_resource_group.default.name
  revision_mode                = "Single"

  identity {
    type = "UserAssigned"
    identity_ids = [
      azurerm_user_assigned_identity.acr.id
    ]
  }

  template {
    container {
      name   = "github-copilot-agent"
      image  = "ghcr.io/waeltken/azure-account-show/main:latest"
      cpu    = 2
      memory = "4Gi"
      readiness_probe {
        transport = "TCP"
        port      = 8000
      }
    }
  }

  # Allow public ingress traffic
  ingress {
    external_enabled = true
    target_port      = 8000

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  registry {
    server   = azurerm_container_registry.acr.login_server
    identity = azurerm_user_assigned_identity.acr.id
  }

  lifecycle {
    ignore_changes = [template.0.container.0.image]
  }

  tags = { azd-service-name : "python-api" }
}

output "subnet_id" {
  value = azurerm_subnet.default.id
}
