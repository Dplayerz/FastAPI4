import os
import threading
from fastapi import FastAPI
from psycopg2 import OperationalError
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from contextlib import asynccontextmanager
import json
import pytz
from paho.mqtt.client import Client as MQTTClient
from fastapi.middleware.cors import CORSMiddleware



# Database configuration
DATABASE_URL = "postgresql://Omniscient:1234@127.0.0.1:5432/postgres"
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define Tag model
class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    event_num = Column(Integer)
    format = Column(String)
    id_hex = Column(String)
    timestamp = Column(DateTime)
    event_type = Column(String)

class Test(Base):
    __tablename__ = "test"
    month_Name = Column(String, primary_key=True, index=True)
    # Add your columns here, for example:
    sales = Column(Integer)

# Create tables
Base.metadata.create_all(bind=engine)

# MQTT settings
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "/FX7500FCCD18_ssl/tevents"
MQTT_USERNAME = "your_username"
MQTT_PASSWORD = "1234"

mqtt_client = None  # Global reference for cleanup

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with result code", rc, flush=True)
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    print(f"Received message on topic {msg.topic}: {payload}", flush=True)
    if not payload:
        print("Empty payload received", flush=True)
        return
    try:
        tag_data_array = json.loads(payload)
        print(f"Raw parsed data: {tag_data_array}", flush=True)
        
        if isinstance(tag_data_array, list) and tag_data_array:
            tag_data = tag_data_array[0]
        elif isinstance(tag_data_array, dict):
            tag_data = tag_data_array
        else:
            print("Invalid message format: not a list or dict", flush=True)
            return
        
        print(f"Parsed tag_data: {tag_data}", flush=True)
        try:
            timestamp = datetime.strptime(tag_data["timestamp"], "%Y-%m-%dT%H:%M:%S.%f%z")
            print(f"Parsed timestamp: {timestamp}", flush=True)
        except ValueError as e:
            print(f"Timestamp parsing error: {e}", flush=True)
            return
        
        new_tag = Tag(
            event_num=tag_data["data"]["eventNum"],
            format=tag_data["data"]["format"],
            id_hex=tag_data["data"]["idHex"],
            timestamp=timestamp,
            event_type=tag_data["type"]
        )
        print(f"Tag to insert: {new_tag.__dict__}", flush=True)
        
        db = SessionLocal()
        try:
            db.add(new_tag)
            db.commit()
            print("Successfully inserted tag into database", flush=True)
        except Exception as e:
            print(f"Error saving to database: {e}", flush=True)
            db.rollback()
        finally:
            db.close()
    except json.JSONDecodeError as e:
        print(f"Invalid JSON format: {e}", flush=True)
    except Exception as e:
        print(f"Error parsing message: {e}", flush=True)



@asynccontextmanager
async def lifespan(app: FastAPI):
    global mqtt_client

    print(" Starting FastAPI and MQTT client", flush=True)

    print(f"Using database URL: {os.getenv('DATABASE_URL')}", flush=True)


    # ✅ TEST DB CONNECTION
    try:
        with engine.connect() as conn:
            print(" Connected to the database")
    except OperationalError as e:
        print(f" Database connection failed: {e}")
        return  # Or use `yield` with caution if you still want the app to run

    # ✅ SETUP MQTT
    mqtt_client = MQTTClient()
    mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    def mqtt_connect():
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()

    threading.Thread(target=mqtt_connect).start()

    yield

    print(" Shutting down MQTT client", flush=True)
    mqtt_client.loop_stop()
    mqtt_client.disconnect()

app = FastAPI(lifespan=lifespan)

app.add_middleware( # type: ignore
    CORSMiddleware,
    allow_origins=["http://localhost:3039"],  # Or ["*"] to allow all origins (for development)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/tags")
def get_tags():
    db = SessionLocal()
    try:
        tags = db.query(Tag).all()
        return [
            {
                "event_num": tag.event_num,
                "format": tag.format,
                "id_hex": tag.id_hex,
                "timestamp": tag.timestamp.isoformat(),
                "event_type": tag.event_type
            }
            for tag in tags
        ]
    finally:
        db.close()

@app.post("/test_insert")
def test_insert():
    db = SessionLocal()
    try:
        test_tag = Tag(
            event_num=999,
            format="epc",
            id_hex="TEST1234567890",
            timestamp=datetime.now(pytz.UTC),
            event_type="TEST"
        )
        db.add(test_tag)
        db.commit()
        return {"status": "Test record inserted"}
    except Exception as e:
        db.rollback()
        return {"status": "Error", "detail": str(e)}
    finally:
        db.close()

@app.get("/test")
def get_tags():
    db = SessionLocal()
    try:
        tags = db.query(Test).all()
        return [
            {
                "sales": tag.sales,
                "month_Name": tag.month_Name,
            }
            for tag in tags
        ]
    finally:
        db.close()