# Configure desired versions of terraform, azurerm provider
terraform {
  required_version = ">= 1.1.7, < 2.0.0"
  backend "azurerm" {
    use_azuread_auth = true
  }
  required_providers {
    azurerm = {
      version = "~>4.9.0"
      source  = "hashicorp/azurerm"
    }
  }
}

# Enable features for azurerm
provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy = false
    }
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
}

# Access client_id, tenant_id, subscription_id and object_id configuration values
data "azurerm_client_config" "current" {}
