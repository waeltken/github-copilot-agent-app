import uvicorn
from fastapi import FastAPI

from api.models import RootModel

app = FastAPI()

@app.get("/")
async def dummy_200():
    return {"ready": "Ok!"}


@app.post("/")
async def request(model: RootModel):
    return {"created": "Ok!"}


@app.post("/callback/")
async def callback(request):
    return {"created": "Ok!"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
