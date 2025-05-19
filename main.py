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
import argparse
import logging
import datetime

app = FastAPI(
    title="FastAPI",
)

# Allow external GET requests from 192.168.0.5
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger("fastapi")


# Initialize Zenoh session
zenoh_session = None
args = None


# @app.on_event("startup")
# async def startup_event():´´


# @app.on_event("shutdown")
# async def shutdown_event():
#     global zenoh_session
#     if zenoh_session:
#         try:
#             zenoh_session.close()
#             print("Zenoh session successfully closed.")
#         except Exception as e:
#             print(f"Failed to close Zenoh session: {e}")


def get_config_from_args(args) -> zenoh.Config:
    conf = (
        zenoh.Config.from_file(args.config)
        if args.config is not None
        else zenoh.Config()
    )
    if args.mode is not None:
        conf.insert_json5("mode", json.dumps(args.mode))
    if args.connect is not None:
        conf.insert_json5("connect/endpoints", json.dumps(args.connect))
    if args.listen is not None:
        conf.insert_json5("listen/endpoints", json.dumps(args.listen))
    if args.no_multicast_scouting:
        conf.insert_json5("scouting/multicast/enabled", json.dumps(False))
    return conf


def add_config_arguments(parser: argparse.ArgumentParser):

    parser.add_argument(
        "--log-level",
        dest="log_level",
        default=30,
        type=int,
        help="The zenoh log level.",
    )

    parser.add_argument(
        "--mode",
        "-m",
        dest="mode",
        choices=["peer", "client"],
        type=str,
        help="The zenoh session mode.",
    )
    parser.add_argument(
        "--connect",
        "-e",
        dest="connect",
        metavar="ENDPOINT",
        action="append",
        type=str,
        help="Endpoints to connect to.",
    )
    parser.add_argument(
        "--listen",
        "-l",
        dest="listen",
        metavar="ENDPOINT",
        action="append",
        type=str,
        help="Endpoints to listen on.",
    )
    parser.add_argument(
        "--config",
        "-c",
        dest="config",
        metavar="FILE",
        type=str,
        help="A configuration file.",
    )
    parser.add_argument(
        "--no-multicast-scouting",
        dest="no_multicast_scouting",
        default=False,
        action="store_true",
        help="Disable multicast scouting.",
    )
    parser.add_argument(
        "--cfg",
        dest="cfg",
        metavar="CFG",
        default=[],
        action="append",
        type=str,
        help="Allows arbitrary configuration changes as column-separated KEY:VALUE pairs. Where KEY must be a valid config path and VALUE must be a valid JSON5 string that can be deserialized to the expected type for the KEY field. Example: --cfg='transport/unicast/max_links:2'.",
    )
    parser.add_argument(
        "--live",
        dest="live",
        default=False,
        action="store_true",
        help="Enable live mode, only sending data received within 30sec.",
    )


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


@app.post("/log_all")
async def log_post(
    request: Request, lat: float = None, long: float = None, time: str = None
):
    global zenoh_session

    logging.debug(f"Received POST LOGG at time: {time}")

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

        datetime_fix = datetime.datetime.strptime(
            parsed_data.get("time"), "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        # Make datetime_fix offset-aware
        datetime_fix = datetime_fix.replace(tzinfo=datetime.timezone.utc)

        now = datetime.datetime.now(datetime.timezone.utc)
        if ((now - datetime_fix).total_seconds() > 30) and args.live:
            logging.warning("Received data is older than 30 seconds. Ignoring.")
            return {"error": "DATA TO OLD!"}

        # PositionFix
        payload_fix = LocationFix()
        payload_fix.timestamp.FromDatetime(datetime_fix)
        payload_fix.latitude = float(parsed_data.get("lat"))
        payload_fix.longitude = float(parsed_data.get("lon"))
        payload_fix.altitude = float(parsed_data.get("alt"))

        # Accuracy
        payload_accuracy = TimestampedFloat()
        payload_accuracy.timestamp.FromDatetime(datetime_fix)
        payload_accuracy.value = float(parsed_data.get("acc"))

        # HDOP
        payload_hdop = TimestampedFloat()
        payload_hdop.timestamp.FromDatetime(datetime_fix)
        payload_hdop.value = float(parsed_data.get("hdop"))

        # VDOP
        payload_vdop = TimestampedFloat()
        payload_vdop.timestamp.FromDatetime(datetime_fix)
        payload_vdop.value = float(parsed_data.get("vdop"))
        
        # PDOP
        payload_pdop = TimestampedFloat()
        payload_pdop.timestamp.FromDatetime(datetime_fix)
        payload_pdop.value = float(parsed_data.get("pdop"))
        
        # Satellites
        payload_satellites = TimestampedInt()
        payload_satellites.timestamp.FromDatetime(datetime_fix)
        payload_satellites.value = int(parsed_data.get("sat"))
        
        # course_over_ground_deg
        payload_heading = TimestampedFloat()
        payload_heading.timestamp.FromDatetime(datetime_fix)
        payload_heading.value = float(parsed_data.get("dir"))

        # speed_over_ground_knots
        payload_speed = TimestampedFloat()
        payload_speed.timestamp.FromDatetime(datetime_fix)
        knots =  float(parsed_data.get("spd")) * 1,94384 # convert to knots
        payload_speed.value = float(parsed_data.get("spd"))
        
        # Battery (battery_state_of_charge_pct)
        payload_battery = TimestampedFloat()
        payload_battery.timestamp.FromDatetime(datetime_fix)
        payload_battery.value = float(parsed_data.get("batt"))

        # TODO: Battery is charging


        # Publish data using Zenoh
        if zenoh_session:

            # PositionFix
            key_expr_location_fix = keelson.construct_pubsub_key(
                base_path="rise",
                entity_id="web",
                subject="location_fix",
                source_id=parsed_data.get("profile"),
            )
            serialized_position_fix = payload_fix.SerializeToString()
            envelope = keelson.enclose(serialized_position_fix)
            zenoh_session.put(key_expr=key_expr_location_fix,payload=envelope)
            logging.debug(f"Published PositionFix to Zenoh with key: {key_expr_location_fix}")


            # Accuracy
            key_expr_accuracy = keelson.construct_pubsub_key(
                base_path="rise",
                entity_id="web",
                subject="location_fix_accuracy_horizontal_m",
                source_id=parsed_data.get("profile"),
            )
            serialized_accuracy = payload_accuracy.SerializeToString()
            envelope = keelson.enclose(serialized_accuracy)
            zenoh_session.put(key_expr=key_expr_accuracy, payload=envelope)
            logging.debug(f"Published Accuracy to Zenoh with key: {key_expr_accuracy}")

            # HDOP
            key_expr_hdop = keelson.construct_pubsub_key(
                base_path="rise",
                entity_id="web",
                subject="location_fix_hdop",
                source_id=parsed_data.get("profile"),
            )
            serialized_hdop = payload_hdop.SerializeToString()
            envelope = keelson.enclose(serialized_hdop)
            zenoh_session.put(key_expr=key_expr_hdop, payload=envelope)
            logging.debug(f"Published HDOP to Zenoh with key: {key_expr_hdop}")

            # VDOP
            key_expr_vdop = keelson.construct_pubsub_key(
                base_path="rise",
                entity_id="web",
                subject="location_fix_vdop",
                source_id=parsed_data.get("profile"),
            )
            serialized_vdop = payload_vdop.SerializeToString()
            envelope = keelson.enclose(serialized_vdop)
            zenoh_session.put(key_expr=key_expr_vdop, payload=envelope)
            logging.debug(f"Published VDOP to Zenoh with key: {key_expr_vdop}")

            # PDOP  
            key_expr_pdop = keelson.construct_pubsub_key(
                base_path="rise",
                entity_id="web",
                subject="location_fix_pdop",
                source_id=parsed_data.get("profile"),
            )
            serialized_pdop = payload_pdop.SerializeToString()
            envelope = keelson.enclose(serialized_pdop)
            zenoh_session.put(key_expr=key_expr_pdop, payload=envelope)
            logging.debug(f"Published PDOP to Zenoh with key: {key_expr_pdop}")

            # Satellites
            key_expr_satellites = keelson.construct_pubsub_key(
                base_path="rise",
                entity_id="web",
                subject="location_fix_satellites_used",
                source_id=parsed_data.get("profile"),
            )
            serialized_satellites = payload_satellites.SerializeToString()
            envelope = keelson.enclose(serialized_satellites)
            zenoh_session.put(key_expr=key_expr_satellites, payload=envelope)
            logging.debug(f"Published Satellites to Zenoh with key: {key_expr_satellites}")

            # course_over_ground_deg
            key_expr_heading = keelson.construct_pubsub_key(    
                base_path="rise",
                entity_id="web",
                subject="course_over_ground_deg",
                source_id=parsed_data.get("profile"),
            )
            serialized_heading = payload_heading.SerializeToString()
            envelope = keelson.enclose(serialized_heading)
            zenoh_session.put(key_expr=key_expr_heading, payload=envelope)
            logging.debug(f"Published course_over_ground_deg to Zenoh with key: {key_expr_heading}")

            # speed_over_ground_knots
            key_expr_speed = keelson.construct_pubsub_key(
                base_path="rise",
                entity_id="web",
                subject="speed_over_ground_knots",
                source_id=parsed_data.get("profile"),
            )
            serialized_speed = payload_speed.SerializeToString()
            envelope = keelson.enclose(serialized_speed)
            zenoh_session.put(key_expr=key_expr_speed, payload=envelope)
            logging.debug(f"Published speed_over_ground_knots to Zenoh with key: {key_expr_speed}")
            
            # Battery
            key_expr_battery = keelson.construct_pubsub_key(
                base_path="rise",
                entity_id="web",
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
    global zenoh_session, args

    # Setup logger
    logging.basicConfig(
        format="%(asctime)s %(levelname)s [%(lineno)d]: %(message)s",
        level=logging.DEBUG,
    )

    logging.captureWarnings(True)

    try:

        # Construct session
        logging.info("Opening Zenoh session...")
        parser = argparse.ArgumentParser(prog="z_pub", description="zenoh pub example")
        add_config_arguments(parser)
        args = parser.parse_args()
        # Setup logger
        logging.basicConfig(
            format="%(asctime)s %(levelname)s %(name)s [%(lineno)d] : %(message)s",
            level=args.log_level,
        )
        logging.captureWarnings(True)

        conf = get_config_from_args(args)

        zenoh_session = zenoh.open(conf)

        if zenoh_session:
            info = zenoh_session.info
            logging.info(
                f"Zenoh session info: zid={info.zid()}, routers={info.routers_zid()}, peers={info.peers_zid()}"
            )
        else:
            logging.error("Zenoh session is not initialized.")

        logging.info("Zenoh session successfully started.")

        uvicorn.run(app, host="0.0.0.0", port=8001)

    except Exception as e:
        logging.error(f"Failed to start Zenoh session: {e}")


if __name__ == "__main__":
    main()
