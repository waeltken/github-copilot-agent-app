import requests
import hashlib
import hmac
import base64
from typing import Dict, Any, Tuple, Optional


def assert_valid_string(value: str, message: str):
    if not isinstance(value, str) or not value:
        raise ValueError(f"[@copilot-extensions/preview-sdk] {message}")


def verify_request(raw_body: str, signature: str, key: str) -> bool:
    # Verify arguments
    assert_valid_string(raw_body, "Invalid payload")
    assert_valid_string(signature, "Invalid signature")
    assert_valid_string(key, "Invalid key")

    # Verify signature
    try:
        signature_bytes = base64.b64decode(signature)
        key_bytes = key.encode()
        raw_body_bytes = raw_body.encode()

        digest = hmac.new(key_bytes, raw_body_bytes, hashlib.sha256).digest()

        return hmac.compare_digest(digest, signature_bytes)
    except Exception:
        return False


def fetch_verification_keys(
    token: str = "",
    request: Any = requests.get,
    cache: Dict[str, Any] = {"id": "", "keys": []},
) -> Tuple[str, Any]:
    try:
        headers = {}
        if token:
            headers["Authorization"] = f"token {token}"
        if cache["id"]:
            headers["if-none-match"] = cache["id"]

        response = request(
            "https://api.github.com/meta/public_keys/copilot_api", headers=headers
        )
        response.raise_for_status()

        cache_id = response.headers.get("etag", "")
        return cache_id, response.json()["public_keys"]
    except requests.HTTPError as error:
        if error.response.status_code == 304:
            return cache["id"], cache["keys"]
        raise error


def verify_request_by_key_id(
    raw_body: str,
    signature: str,
    key_id: str,
    request_options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if request_options is None:
        request_options = {}

    # Verify arguments
    assert_valid_string(raw_body, "Invalid payload")
    assert_valid_string(signature, "Invalid signature")
    assert_valid_string(key_id, "Invalid keyId")

    # Fetch valid public keys from GitHub
    id, keys = fetch_verification_keys(**request_options)

    # Verify provided key Id
    public_key = next((key for key in keys if key["key_identifier"] == key_id), None)

    if not public_key:
        key_not_found_error = ValueError(
            "[@copilot-extensions/preview-sdk] No public key found matching key identifier"
        )
        key_not_found_error.key_id = key_id
        key_not_found_error.keys = keys
        raise key_not_found_error

    is_valid = verify_request(raw_body, signature, public_key["key"])
    return {"isValid": is_valid, "cache": {"id": id, "keys": keys}}


# Example usage
if __name__ == "__main__":
    raw_body = "example_raw_body"
    signature = "example_signature"
    key_id = "example_key_id"

    request_options = {
        "token": "your_github_token",
    }

    try:
        result = verify_request_by_key_id(raw_body, signature, key_id, request_options)
        print(result)
    except ValueError as e:
        print(str(e))
