from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Server is working!"}

if __name__ == "__main__":
    print("Starting test server...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
