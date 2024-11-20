from base64 import b64decode
from hashlib import sha256
from functools import lru_cache

import requests
from ecdsa import VerifyingKey, BadSignatureError, NIST256p
from ecdsa.util import sigdecode_der
from fastapi import Request, HTTPException


@lru_cache()
def get_github_public_key(key_id: str) -> str:
    # Fetch the public key from GitHub's API
    response = requests.get("https://api.github.com/meta/public_keys/copilot_api")
    response.raise_for_status()
    keys = response.json().get("public_keys", [])
    for key in keys:
        if key["key_identifier"] == key_id:
            return key["key"]
    raise HTTPException(status_code=403, detail="Public key not found")


def verify_request_by_key_id(raw_body: bytes, signature: str, key_id: str) -> bool:
    public_key_pem = get_github_public_key(key_id)
    raw_sig = b64decode(signature)
    ecdsa_verifier = VerifyingKey.from_pem(string=public_key_pem, hashfunc=sha256)
    try:
        ecdsa_verifier.verify(signature=raw_sig, data=raw_body, sigdecode=sigdecode_der)
        return True
    except (BadSignatureError, ValueError) as e:
        print(f"Verification failed: {e}")
        return False


async def verify_signature(request: Request):
    raw_body = await request.body()
    github_public_key_signature = request.headers.get("Github-Public-Key-Signature")
    github_public_key_identifier = request.headers.get("Github-Public-Key-Identifier")

    if not github_public_key_signature or not github_public_key_identifier:
        raise HTTPException(
            status_code=403,
            detail="Missing signature or key identifier",
        )

    if not verify_request_by_key_id(
        raw_body=raw_body,
        signature=github_public_key_signature,
        key_id=github_public_key_identifier,
    ):
        raise HTTPException(status_code=403, detail="Invalid signature")
