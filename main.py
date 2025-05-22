from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from fastapi import Request
import zenoh
import keelson
from keelson.payloads.foxglove.LocationFix_pb2 import LocationFix
from keelson.payloads.Primitives_pb2 import TimestampedFloat, TimestampedInt
import json
import logging
import datetime


# Initialize Zenoh session
args = None
zenoh_session = None


# Setup logger
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s [%(lineno)d] : %(message)s",
    level=10,
)
logging.captureWarnings(True)


# Construct session
logging.info("Opening Zenoh session...")
conf = zenoh.Config()
# conf.insert_json5("mode", json.dumps("client"))
conf.insert_json5("connect/endpoints", json.dumps(["tcp/zenoh-router:7447"]))
zenoh_session = zenoh.open(conf)


# if zenoh_session:
#     info = zenoh_session.info
#     logging.info(
#         f"Zenoh session info: zid={info.zid()}, routers={info.routers_zid()}, peers={info.peers_zid()}"
#     )
# else:
#     logging.error("Zenoh session is not initialized.")

logging.info("Zenoh session successfully started.")


app = FastAPI( title="FastAPI")

# Allow external GET requests from 192.168.0.5
origins = ["*", "192.168.0.5"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger("fastapi")


@app.get(
    "/",
    summary="Test endpoint",
    description="""
         This is a test endpoint that returns a welcome message.
         """,
)
async def root():
    return {"message": "Hello World"}


@app.get("/log_minimal", summary="Minimal log endpoint", description="Logs minimal data")
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


@app.post("/log_all/{entityid}")
async def log_post(
    request: Request, entityid: str
):


    try:
        body = await request.body()
        data = body.decode("utf-8").split("&")
        parsed_data = {}
        for item in data:
            if "=" in item:
                key, value = item.split("=", 1)
                parsed_data[key] = value

        logging.debug(f"Parsed data: {parsed_data}")

        datetime_fix = datetime.datetime.strptime(
            parsed_data.get("time"), "%Y-%m-%dT%H:%M:%S.%fZ"
        )


        # Satellites

        # course_over_ground_deg


        # speed_over_ground_knots

        
 

        # TODO: Battery is charging


        # Publish data using Zenoh
        if zenoh_session:

            # PositionFix
            if parsed_data.get("lat") or parsed_data.get("lon"):
                payload_fix = LocationFix()
                payload_fix.timestamp.FromDatetime(datetime_fix)
                payload_fix.latitude = float(parsed_data.get("lat"))
                payload_fix.longitude = float(parsed_data.get("lon"))
                payload_fix.altitude = float(parsed_data.get("alt"))
                key_expr_location_fix = keelson.construct_pubsub_key(
                    base_path="rise",
                    entity_id=entityid,
                    subject="location_fix",
                    source_id=parsed_data.get("profile"),
                )
                serialized_position_fix = payload_fix.SerializeToString()
                envelope = keelson.enclose(serialized_position_fix)
                zenoh_session.put(key_expr=key_expr_location_fix,payload=envelope)
                logging.debug(f"Published PositionFix to Zenoh with key: {key_expr_location_fix}")


            # Accuracy
            if parsed_data.get("acc"):
                payload_accuracy = TimestampedFloat()   
                payload_accuracy.timestamp.FromDatetime(datetime_fix)
                payload_accuracy.value = float(parsed_data.get("acc"))
                key_expr_accuracy = keelson.construct_pubsub_key(
                    base_path="rise",
                    entity_id=entityid,
                    subject="location_fix_accuracy_horizontal_m",
                    source_id=parsed_data.get("profile"),
                )
                serialized_accuracy = payload_accuracy.SerializeToString()
                envelope = keelson.enclose(serialized_accuracy)
                zenoh_session.put(key_expr=key_expr_accuracy, payload=envelope)
                logging.debug(f"Published Accuracy to Zenoh with key: {key_expr_accuracy}")

            # HDOP
            if parsed_data.get("hdop"):
                payload_hdop = TimestampedFloat()
                payload_hdop.timestamp.FromDatetime(datetime_fix)
                payload_hdop.value = float(parsed_data.get("hdop"))
                key_expr_hdop = keelson.construct_pubsub_key(
                    base_path="rise",
                    entity_id=entityid,
                    subject="location_fix_hdop",
                    source_id=parsed_data.get("profile"),
                )
                serialized_hdop = payload_hdop.SerializeToString()
                envelope = keelson.enclose(serialized_hdop)
                zenoh_session.put(key_expr=key_expr_hdop, payload=envelope)
                logging.debug(f"Published HDOP to Zenoh with key: {key_expr_hdop}")

            # VDOP
            if parsed_data.get("vdop"):
                payload_vdop = TimestampedFloat()
                payload_vdop.timestamp.FromDatetime(datetime_fix)
                payload_vdop.value = float(parsed_data.get("vdop"))
                key_expr_vdop = keelson.construct_pubsub_key(
                    base_path="rise",
                    entity_id=entityid,
                    subject="location_fix_vdop",
                    source_id=parsed_data.get("profile"),
                )
                serialized_vdop = payload_vdop.SerializeToString()
                envelope = keelson.enclose(serialized_vdop)
                zenoh_session.put(key_expr=key_expr_vdop, payload=envelope)
                logging.debug(f"Published VDOP to Zenoh with key: {key_expr_vdop}")

            # PDOP 
            if parsed_data.get("pdop"):
                payload_pdop = TimestampedFloat()
                payload_pdop.timestamp.FromDatetime(datetime_fix)
                payload_pdop.value = float(parsed_data.get("pdop"))
                key_expr_pdop = keelson.construct_pubsub_key(
                    base_path="rise",
                    entity_id=entityid,
                    subject="location_fix_pdop",
                    source_id=parsed_data.get("profile"),
                )
                serialized_pdop = payload_pdop.SerializeToString()
                envelope = keelson.enclose(serialized_pdop)
                zenoh_session.put(key_expr=key_expr_pdop, payload=envelope)
                logging.debug(f"Published PDOP to Zenoh with key: {key_expr_pdop}")

            # Satellites
            if parsed_data.get("sat"):
                payload_satellites = TimestampedInt()
                payload_satellites.timestamp.FromDatetime(datetime_fix)
                payload_satellites.value = int(parsed_data.get("sat"))
                key_expr_satellites = keelson.construct_pubsub_key(
                    base_path="rise",
                    entity_id=entityid,
                    subject="location_fix_satellites_used",
                    source_id=parsed_data.get("profile"),
                )
                serialized_satellites = payload_satellites.SerializeToString()
                envelope = keelson.enclose(serialized_satellites)
                zenoh_session.put(key_expr=key_expr_satellites, payload=envelope)
                logging.debug(f"Published Satellites to Zenoh with key: {key_expr_satellites}")

            # course_over_ground_deg
            if parsed_data.get("dir"):
                payload_heading = TimestampedFloat()
                payload_heading.timestamp.FromDatetime(datetime_fix)
                payload_heading.value = float(parsed_data.get("dir"))
                key_expr_heading = keelson.construct_pubsub_key(    
                    base_path="rise",
                    entity_id=entityid,
                    subject="course_over_ground_deg",
                    source_id=parsed_data.get("profile"),
                )
                serialized_heading = payload_heading.SerializeToString()
                envelope = keelson.enclose(serialized_heading)
                zenoh_session.put(key_expr=key_expr_heading, payload=envelope)
                logging.debug(f"Published course_over_ground_deg to Zenoh with key: {key_expr_heading}")

            # speed_over_ground_knots
            if parsed_data.get("spd"):
                payload_speed = TimestampedFloat()
                payload_speed.timestamp.FromDatetime(datetime_fix)
                knots =  float(parsed_data.get("spd")) * 1.94384 # convert to knots
                payload_speed.value = float(knots)
                key_expr_speed = keelson.construct_pubsub_key(
                    base_path="rise",
                    entity_id=entityid,
                    subject="speed_over_ground_knots",
                    source_id=parsed_data.get("profile"),
                )
                serialized_speed = payload_speed.SerializeToString()
                envelope = keelson.enclose(serialized_speed)
                zenoh_session.put(key_expr=key_expr_speed, payload=envelope)
                logging.debug(f"Published speed_over_ground_knots to Zenoh with key: {key_expr_speed}")
            
            # Battery
            if parsed_data.get("batt"):
                payload_battery = TimestampedFloat()
                payload_battery.timestamp.FromDatetime(datetime_fix)
                payload_battery.value = float(parsed_data.get("batt"))
                key_expr_battery = keelson.construct_pubsub_key(
                    base_path="rise",
                    entity_id=entityid,
                    subject="battery_state_of_charge_pct",
                    source_id=parsed_data.get("profile"),
                )
                serialized_battery = payload_battery.SerializeToString()
                envelope = keelson.enclose(serialized_battery)
                zenoh_session.put(key_expr=key_expr_battery, payload=envelope)
                logging.debug(f"Published battery_state_of_charge_pct to Zenoh with key: {key_expr_battery}")


        else:
            logging.warning("Zenoh session is not initialized.")

        return parsed_data

    except Exception as e:
        logging.error(f"{e}")


def main():

    try:
        uvicorn.run(app, host="0.0.0.0", port=8001)

    except Exception as e:
        logging.error(f"Failed to start Zenoh session: {e}")


if __name__ == "__main__":
    main()
