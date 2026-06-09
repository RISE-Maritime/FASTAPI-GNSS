from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from fastapi import Request
import zenoh
import keelson
from keelson.payloads.foxglove.LocationFix_pb2 import LocationFix
from keelson.payloads.Primitives_pb2 import (
    TimestampedFloat,
    TimestampedInt,
    TimestampedBool,
    TimestampedQuaternion,
)
from keelson.payloads.Decomposed3DVector_pb2 import Decomposed3DVector
import json
import logging
import datetime
import math
import os


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
zenoh_connect = os.environ.get("ZENOH_CONNECT", "tcp/zenoh-router:7447")
conf.insert_json5("connect/endpoints", json.dumps([zenoh_connect]))
zenoh_session = zenoh.open(conf)


# if zenoh_session:
#     info = zenoh_session.info
#     logging.info(
#         f"Zenoh session info: zid={info.zid()}, routers={info.routers_zid()}, peers={info.peers_zid()}"
#     )
# else:
#     logging.error("Zenoh session is not initialized.")

logging.info("Zenoh session successfully started.")


# --- Keelson publishing helpers -------------------------------------------
# All pub/sub keys follow the keelson convention rise/@v0/{entity}/pubsub/{subject}/{source}.
# Publishers are declared once and cached: SensorLogger streams IMU at high rate, so
# reusing a declared publisher is cheaper than session.put() per message.
BASE_PATH = "rise"
PUBLISHERS = {}


def get_or_create_publisher(entity_id, subject, source_id):
    cache_key = (entity_id, subject, source_id)
    publisher = PUBLISHERS.get(cache_key)
    if publisher is None:
        key_expr = keelson.construct_pubsub_key(
            base_path=BASE_PATH,
            entity_id=entity_id,
            subject=subject,
            source_id=source_id,
        )
        publisher = zenoh_session.declare_publisher(key_expr)
        PUBLISHERS[cache_key] = publisher
    return publisher


def publish_payload(entity_id, subject, source_id, payload):
    """Enclose a protobuf payload in a keelson envelope and publish it."""
    publisher = get_or_create_publisher(entity_id, subject, source_id)
    publisher.put(keelson.enclose(payload.SerializeToString()))


def publish_float(entity_id, subject, source_id, value, ts_ns):
    payload = TimestampedFloat()
    payload.timestamp.FromNanoseconds(ts_ns)
    payload.value = float(value)
    publish_payload(entity_id, subject, source_id, payload)


def publish_int(entity_id, subject, source_id, value, ts_ns):
    payload = TimestampedInt()
    payload.timestamp.FromNanoseconds(ts_ns)
    payload.value = int(value)
    publish_payload(entity_id, subject, source_id, payload)


def publish_bool(entity_id, subject, source_id, value, ts_ns):
    payload = TimestampedBool()
    payload.timestamp.FromNanoseconds(ts_ns)
    payload.value = bool(value)
    publish_payload(entity_id, subject, source_id, payload)


def publish_vector3(entity_id, subject, source_id, x, y, z, ts_ns, frame_id=None):
    payload = Decomposed3DVector()
    payload.timestamp.FromNanoseconds(ts_ns)
    if frame_id:
        payload.frame_id = frame_id
    payload.vector.x = float(x)
    payload.vector.y = float(y)
    payload.vector.z = float(z)
    publish_payload(entity_id, subject, source_id, payload)


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
    entityid, request: Request, lat: float = None, long: float = None, time: str = None
):

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
        knots =  float(parsed_data.get("spd")) * 1.94384 # convert to knots
        payload_speed.value = float(knots)
        
        # Battery (battery_state_of_charge_pct)
        payload_battery = TimestampedFloat()
        payload_battery.timestamp.FromDatetime(datetime_fix)
        payload_battery.value = float(parsed_data.get("batt"))

        # Battery is charging
        payload_is_charging = TimestampedBool()
        payload_is_charging.timestamp.FromDatetime(datetime_fix)
        if parsed_data.get("ischarging") == "true":
            payload_is_charging.value = True
        else:
            payload_is_charging.value = False


        # Publish data using Zenoh
        if zenoh_session:

            # PositionFix
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

            # Battery is charging
            key_expr_is_charging = keelson.construct_pubsub_key(
                base_path="rise",
                entity_id=entityid,
                subject="battery_is_charging",
                source_id=parsed_data.get("profile"),
            )
            serialized_is_charging = payload_is_charging.SerializeToString()
            envelope = keelson.enclose(serialized_is_charging)
            zenoh_session.put(key_expr=key_expr_is_charging, payload=envelope)
            logging.debug(f"Published battery_is_charging to Zenoh with key: {key_expr_is_charging}")


        else:
            logging.warning("Zenoh session is not initialized.")

        return parsed_data

    except Exception as e:
        logging.error(f"{e}")


@app.post("/sensorlogger/{entityid}")
async def sensorlogger_post(entityid, request: Request, source_id: str = None):
    """Ingest a Sensor Logger (tszheichoi) real-time HTTP Push batch and republish to keelson.

    Body is JSON: {messageId, sessionId, deviceId, userId?, payload: [{name, time(ns), values}]}.
    Each payload entry is mapped to one or more well-known keelson subjects. Per-entry errors
    are isolated so a single bad reading never drops the rest of the batch.
    """
    if zenoh_session is None:
        logging.warning("Zenoh session is not initialized.")
        return {"received": 0}

    try:
        body = await request.json()
    except Exception as e:
        logging.error(f"SensorLogger: invalid JSON body: {e}")
        return {"received": 0}

    # Sensor Logger has no "profile"; identify the source by deviceId (override via ?source_id=).
    source = source_id or body.get("deviceId") or "sensorlogger"
    entries = body.get("payload", []) or []
    received = 0

    for entry in entries:
        name = entry.get("name")
        try:
            ts = int(entry["time"])  # UTC epoch nanoseconds
            values = entry.get("values", {}) or {}

            if name == "location":
                fix = LocationFix()
                fix.timestamp.FromNanoseconds(ts)
                fix.latitude = float(values["latitude"])
                fix.longitude = float(values["longitude"])
                if values.get("altitude") is not None:
                    fix.altitude = float(values["altitude"])
                publish_payload(entityid, "location_fix", source, fix)

                if values.get("horizontalAccuracy") is not None:
                    publish_float(entityid, "location_fix_accuracy_horizontal_m", source, values["horizontalAccuracy"], ts)
                if values.get("verticalAccuracy") is not None:
                    publish_float(entityid, "location_fix_accuracy_vertical_m", source, values["verticalAccuracy"], ts)
                if values.get("speed") is not None:
                    # Sensor Logger speed is m/s -> knots
                    publish_float(entityid, "speed_over_ground_knots", source, float(values["speed"]) * 1.94384, ts)
                if values.get("bearing") is not None:
                    publish_float(entityid, "course_over_ground_deg", source, values["bearing"], ts)
                if values.get("altitudeAboveMeanSeaLevel") is not None:
                    publish_float(entityid, "altitude_above_msl_m", source, values["altitudeAboveMeanSeaLevel"], ts)

            elif name == "accelerometer":
                publish_vector3(entityid, "linear_acceleration_mpss", source, values["x"], values["y"], values["z"], ts, frame_id=source)

            elif name == "gyroscope":
                publish_vector3(entityid, "angular_velocity_radps", source, values["x"], values["y"], values["z"], ts, frame_id=source)

            elif name == "magnetometer":
                # Sensor Logger magnetometer is microtesla; keelson wants gauss (1 G = 100 uT)
                publish_vector3(entityid, "magnetic_field_gauss", source, values["x"] / 100.0, values["y"] / 100.0, values["z"] / 100.0, ts, frame_id=source)

            elif name == "orientation":
                if all(k in values for k in ("qx", "qy", "qz", "qw")):
                    quat = TimestampedQuaternion()
                    quat.timestamp.FromNanoseconds(ts)
                    quat.value.x = float(values["qx"])
                    quat.value.y = float(values["qy"])
                    quat.value.z = float(values["qz"])
                    quat.value.w = float(values["qw"])
                    publish_payload(entityid, "orientation_quaternion", source, quat)
                # Sensor Logger roll/pitch/yaw are radians -> degrees
                if values.get("roll") is not None:
                    publish_float(entityid, "roll_deg", source, math.degrees(values["roll"]), ts)
                if values.get("pitch") is not None:
                    publish_float(entityid, "pitch_deg", source, math.degrees(values["pitch"]), ts)
                if values.get("yaw") is not None:
                    publish_float(entityid, "yaw_deg", source, math.degrees(values["yaw"]), ts)

            elif name == "barometer":
                # Sensor Logger barometer pressure is hPa; keelson wants Pa (x100)
                if values.get("pressure") is not None:
                    publish_float(entityid, "air_pressure_pa", source, float(values["pressure"]) * 100.0, ts)

            elif name == "battery":
                # Best-effort; confirm field names/units against a real capture.
                if values.get("level") is not None:
                    level = float(values["level"])
                    publish_float(entityid, "battery_state_of_charge_pct", source, level * 100.0 if level <= 1.0 else level, ts)
                if values.get("state") is not None:
                    publish_bool(entityid, "battery_is_charging", source, str(values["state"]).lower() in ("charging", "full", "2"), ts)

            else:
                logging.debug(f"SensorLogger: unmapped sensor '{name}' skipped")
                continue

            received += 1
        except Exception as e:
            logging.error(f"SensorLogger: failed to process entry '{name}': {e}")

    logging.debug(f"SensorLogger: published {received}/{len(entries)} entries for {entityid}/{source}")
    return {"received": received}


def main():

    try:
        uvicorn.run(app, host="0.0.0.0", port=8001)

    except Exception as e:
        logging.error(f"Failed to start Zenoh session: {e}")


if __name__ == "__main__":
    main()
