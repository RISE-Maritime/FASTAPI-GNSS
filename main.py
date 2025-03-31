from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from fastapi import Request
import zenoh
import keelson
from keelson.payloads.LocationFix_pb2 import (
    PositionFix,
    PositionSourceSatellites,
    TraveledDistance,
)
from keelson.payloads.Log_pb2 import Log
from keelson.payloads.Navigation_pb2 import TrajectoryOverGround
from keelson.payloads.Battery_pb2 import BatteryState

app = FastAPI(
    title="FastAPI",
)

# Allow external GET requests from 192.168.0.5
origins = ["http://192.168.0.5", "*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Zenoh session
zenoh_session = None


# @app.on_event("startup")
# async def startup_event():
    

# @app.on_event("shutdown")
# async def shutdown_event():
#     global zenoh_session
#     if zenoh_session:
#         try:
#             zenoh_session.close()
#             print("Zenoh session successfully closed.")
#         except Exception as e:
#             print(f"Failed to close Zenoh session: {e}")


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/log")
async def log(
    request: Request, lat: float = None, long: float = None, time: str = None
):
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
async def log_post(
    request: Request, lat: float = None, long: float = None, time: str = None
):
    global zenoh_session
    print(f"Received POST LOGG at time: {time}")
    try:
        body = await request.body()
        data = body.decode("utf-8").split("&")
        parsed_data = {}
        for item in data:
            if "=" in item:
                key, value = item.split("=", 1)
                parsed_data[key] = value

        print(f"Parsed data: {parsed_data}")

        print(f"LAT: {parsed_data.get('lat')}")

        # PositionFix
        position_fix = PositionFix(
            latitude_degrees=float(parsed_data.get("lat",0.0)),
            longitude_degrees=float(parsed_data.get("lon",0.0)),
            altitude_meters=float(parsed_data.get("alt",0.0)),
            accuracy_meters=float(parsed_data.get("acc",0.0)),
        )

        # Publish data using Zenoh
        if zenoh_session:
            key_expr_pos_fix = keelson.construct_pubsub_key(
                realm="rise",
                entity_id="web",
                subject="position_fix",
                source_id=parsed_data.get("profile"),
            )
            pub = zenoh_session.declare_publisher(key_expr_pos_fix)
            # Publish the target
            serialized_position_fix = position_fix.SerializeToString()
            envelope = keelson.enclose(serialized_position_fix)
            pub.put(envelope)
            print(f"Published PositionFix to Zenoh with key: {key_expr_pos_fix}")
        else:
            print("Zenoh session is not initialized.")

        return parsed_data

    except Exception as e:
        print(f"No JSON body received: {e}")


def main():
    global zenoh_session
    
    # Setup logger
    logging.basicConfig(
        format="%(asctime)s %(levelname)s [%(lineno)d]: %(message)s", level=logging.DEBUG
    )
    
    logging.captureWarnings(True)
    

    try:

        # Construct session
        logging.info("Opening Zenoh session...")
        conf = zenoh.Config()


        with zenoh.open(conf) as zenoh_session:
            info = zenoh_session.info
            logging.info(f"zid: {info.zid()}")
            logging.info(f"routers: {info.routers_zid()}")
            logging.info(f"peers: {info.peers_zid()}")

            print("Zenoh session successfully started.")

            uvicorn.run(app, host="0.0.0.0", port=8000)
          
    except Exception as e:
        print(f"Failed to start Zenoh session: {e}")


if __name__ == "__main__":
    main()