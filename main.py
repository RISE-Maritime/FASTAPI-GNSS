from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from fastapi import Request
from urllib.parse import parse_qs

app = FastAPI(
    title="FastAPI",
)

# Allow external GET requests from 192.168.0.5
origins = [
    "http://192.168.0.5",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/log")
async def log(request: Request, lat: float = None, long: float = None, time: str = None):
    print(f"Received lat: {lat}, long {long}, time: {time}")
    try:
        body = await request.json()
        print(f"Received body: {body}")
    except Exception as e:
        print(f"No JSON body received: {e}")
    return {
        "lat": lat,
        "longitude": long,
    }

@app.post("/logg")
async def log_post(request: Request, lat: float = None, long: float = None, time: str = None):
    print(f"Received POST lat: {lat}, long {long}, time: {time}")
    try:
        #body = await request.body()
        #print(f"Received POST request body: {body}")
        #body = await request.json()
        #print(f"Received body: {body}")

        body = await request.body()
        print(f"Received POST request body: {body}")
        parsed_body = parse_qs(body.decode())
        print(f"Parsed body: {parsed_body}")
        print(f"Parsed body LAT: {parsed_body.get('lat')}")
    except Exception as e:
        print(f"No JSON body received: {e}")
    return {
        "lat": lat,
        "longitude": long,
    }
if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8000)