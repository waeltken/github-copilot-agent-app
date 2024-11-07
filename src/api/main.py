import uvicorn
from fastapi import FastAPI, Header
from fastapi.responses import StreamingResponse
from typing import Annotated
from openai import OpenAI
import json

from api.models import RootModel
from api.verify import verify_request_by_key_id

app = FastAPI()


@app.get("/")
async def dummy_200():
    return {"ready": "Ok!"}


@app.post("/")
async def request(
    payload: RootModel,
    x_github_token: Annotated[str, Header()],
    github_public_key_signature: Annotated[str, Header()],
    github_public_key_identifier: Annotated[str, Header()],
):
    verify_request_by_key_id(
        raw_body=payload.model_dump_json(),
        signature=github_public_key_signature,
        key_id=github_public_key_identifier,
    )
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


@app.post("/callback/")
async def callback(request):
    return {"created": "Ok!"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
