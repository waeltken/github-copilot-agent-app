import json

import uvicorn
from fastapi import FastAPI, Header, Depends
from typing import Annotated
from fastapi.responses import StreamingResponse

from api.models import RootModel
from openai import OpenAI
from verify_signature import verify_signature

app = FastAPI()


@app.get("/")
async def dummy_200():
    return {"ready": "Ok!"}


@app.post("/", dependencies=[Depends(verify_signature)])
async def request(
    payload: RootModel,
    x_github_token: Annotated[str, Header()],
):
    openai = OpenAI(base_url="https://api.githubcopilot.com", api_key=x_github_token)

    messages = payload.messages

    messages.insert(
        0,
        {
            "role": "system",
            "content": "You are a helpful assistant that replies to user messages as if you were Joda from StarWars.",
        },
    )

    response = openai.chat.completions.create(
        stream=True,
        model="gpt-4o",
        messages=messages,
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
