import json
import hmac
import hashlib
import base64
import requests
from typing import Annotated

import uvicorn
from fastapi import FastAPI, Header, Depends, Request, HTTPException
from fastapi.responses import StreamingResponse
from openai import OpenAI

from api.models import RootModel

app = FastAPI()


@app.get("/")
async def dummy_200():
    return {"ready": "Ok!"}


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
    public_key = get_github_public_key(key_id)
    decoded_signature = base64.b64decode(signature)
    hmac_obj = hmac.new(public_key.encode(), raw_body, hashlib.sha256)
    return hmac.compare_digest(hmac_obj.digest(), decoded_signature)


@app.middleware("http")
async def verify_signature_middleware(request: Request, call_next):
    raw_body = await request.body()
    github_public_key_signature = request.headers.get("Github-Public-Key-Signature")
    github_public_key_identifier = request.headers.get("Github-Public-Key-Identifier")

    if not verify_request_by_key_id(
        raw_body=raw_body,
        signature=github_public_key_signature,
        key_id=github_public_key_identifier,
    ):
        raise HTTPException(status_code=403, detail="Invalid signature")

    response = await call_next(request)
    return response


@app.post("/", dependencies=[Depends(verify_signature_middleware)])
async def request(
    payload: RootModel,
    x_github_token: Annotated[str, Header()],
):
    openai = OpenAI(base_url="https://api.githubcopilot.com", api_key=x_github_token)
    response = openai.chat.completions.create(
        stream=True,
        model="gpt-4o",
        messages=payload.messages,
    )

    async def event_generator():
        for chunk in response:
            chunk_dict = chunk.to_dict()
            chunk_str = "data: " + json.dumps(chunk_dict) + "\n\n"
            yield chunk_str
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
