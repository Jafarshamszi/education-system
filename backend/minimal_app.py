from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/test")
async def test():
    return {"message": "Server is working"}