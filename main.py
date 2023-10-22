from fastapi import FastAPI, Response

# I like to launch directly and not use the standard FastAPI startup
import uvicorn

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World. This is Inventory Management Service!"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8012)
