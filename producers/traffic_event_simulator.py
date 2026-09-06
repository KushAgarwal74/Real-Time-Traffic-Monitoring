import json
import random
import time
from datetime import datetime, timezone


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

OUTPUT_FILE = "simulated_events.jsonl"

# Camera location from the uploaded data
CAMERA_LATITUDE = 18.496326066159856
CAMERA_LONGITUDE = 73.95019103166328
CAMERA_ELEVATION = 521.4362566

# How often an event is generated
EVENT_INTERVAL = 0.5       # seconds

# Maximum vehicles simultaneously tracked
MAX_VEHICLES = 20

# Probability of a new vehicle entering
NEW_VEHICLE_PROBABILITY = 0.35

# Probability of detecting a license plate
LICENSE_PLATE_PROBABILITY = 0.15


VEHICLE_TYPES = [
    "car",
    "motorcycle",
    "truck",
    "bus"
]


# ---------------------------------------------------------
# Vehicle
# ---------------------------------------------------------

class Vehicle:

    def __init__(self, track_id):

        self.track_id = track_id

        self.vehicle_type = random.choice(VEHICLE_TYPES)

        self.latitude = CAMERA_LATITUDE
        self.longitude = CAMERA_LONGITUDE

        # Random initial position around camera
        self.latitude += random.uniform(-0.00005, 0.00005)
        self.longitude += random.uniform(-0.00005, 0.00005)

        self.bbox = self.generate_bbox()

        self.confidence = random.uniform(0.35, 0.95)

        # Number of frames this vehicle has existed
        self.age = 0

        # Vehicle will eventually leave
        self.max_age = random.randint(10, 40)

        self.plate_detected = False


    def generate_bbox(self):

        x1 = random.randint(300, 1200)
        y1 = random.randint(700, 1100)

        width = random.randint(50, 200)
        height = random.randint(50, 220)

        return [
            x1,
            y1,
            x1 + width,
            y1 + height
        ]


    def move(self):

        # Simulate vehicle movement

        self.latitude += random.uniform(-0.000003, 0.000003)
        self.longitude += random.uniform(-0.000003, 0.000003)

        # Bounding box changes slightly
        x1, y1, x2, y2 = self.bbox

        dx = random.randint(-10, 10)
        dy = random.randint(-10, 10)

        self.bbox = [
            x1 + dx,
            y1 + dy,
            x2 + dx,
            y2 + dy
        ]


# ---------------------------------------------------------
# Timestamp
# ---------------------------------------------------------

def current_timestamp():

    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------
# Camera GPS
# ---------------------------------------------------------

def camera_gps(timestamp):

    return {
        "timestamp": timestamp,
        "latitude": CAMERA_LATITUDE,
        "longitude": CAMERA_LONGITUDE,
        "elevation": CAMERA_ELEVATION
    }


# ---------------------------------------------------------
# Generate license plate
# ---------------------------------------------------------

def generate_license_plate(vehicle):

    if random.random() > LICENSE_PLATE_PROBABILITY:
        return None

    # Generate a bbox somewhere inside the vehicle bbox

    x1, y1, x2, y2 = vehicle.bbox

    plate_x1 = random.randint(x1, max(x1, x2 - 30))
    plate_y1 = random.randint(y1, max(y1, y2 - 20))

    plate_width = random.randint(20, 60)
    plate_height = random.randint(5, 20)

    return {
        "track_id": vehicle.track_id,
        "bbox": [
            plate_x1,
            plate_y1,
            plate_x1 + plate_width,
            plate_y1 + plate_height
        ],
        "confidence": random.uniform(0.4, 0.95)
    }


# ---------------------------------------------------------
# Generate vehicle event
# ---------------------------------------------------------

def generate_event(vehicle, event_type, frame_number):

    timestamp = current_timestamp()

    event = {
        "event_type": event_type,
        "track_id": vehicle.track_id,
        "vehicle_type": vehicle.vehicle_type,
        "frame_number": frame_number,
        "timestamp": timestamp,
        "bbox": vehicle.bbox,
        "confidence": vehicle.confidence,
        "camera_gps": camera_gps(timestamp),
        "license_plate": None
    }

    # License plate detection can happen on
    # detected/updated events
    if event_type in ("vehicle_detected", "vehicle_updated"):

        plate = generate_license_plate(vehicle)

        if plate is not None:
            event["license_plate"] = plate
            vehicle.plate_detected = True

    return event


# ---------------------------------------------------------
# Main simulator
# ---------------------------------------------------------

def run_simulator():

    vehicles = {}

    next_track_id = 1
    frame_number = 0

    print("Traffic event simulator started")
    print(f"Writing events to: {OUTPUT_FILE}")
    print("Press Ctrl+C to stop.\n")

    with open(OUTPUT_FILE, "a") as output:

        try:

            while True:

                # -----------------------------------------
                # Add new vehicle
                # -----------------------------------------

                if (
                    len(vehicles) < MAX_VEHICLES
                    and random.random() < NEW_VEHICLE_PROBABILITY
                ):

                    vehicle = Vehicle(next_track_id)

                    vehicles[next_track_id] = vehicle

                    event = generate_event(
                        vehicle,
                        "vehicle_detected",
                        frame_number
                    )

                    output.write(
                        json.dumps(event) + "\n"
                    )

                    output.flush()

                    print(
                        f"[DETECTED] "
                        f"track={vehicle.track_id} "
                        f"type={vehicle.vehicle_type}"
                    )

                    next_track_id += 1


                # -----------------------------------------
                # Update existing vehicles
                # -----------------------------------------

                vehicles_to_remove = []

                for track_id, vehicle in list(vehicles.items()):

                    vehicle.age += 1

                    # Vehicle leaves the camera view
                    if vehicle.age >= vehicle.max_age:

                        event = generate_event(
                            vehicle,
                            "vehicle_exited",
                            frame_number
                        )

                        # Don't generate a new plate
                        event["license_plate"] = None

                        output.write(
                            json.dumps(event) + "\n"
                        )

                        output.flush()

                        print(
                            f"[EXITED] "
                            f"track={vehicle.track_id}"
                        )

                        vehicles_to_remove.append(track_id)

                    else:

                        vehicle.move()

                        event = generate_event(
                            vehicle,
                            "vehicle_updated",
                            frame_number
                        )

                        output.write(
                            json.dumps(event) + "\n"
                        )

                        output.flush()

                        print(
                            f"[UPDATED] "
                            f"track={vehicle.track_id} "
                            f"lat={vehicle.latitude:.8f} "
                            f"lon={vehicle.longitude:.8f}"
                        )


                # -----------------------------------------
                # Remove exited vehicles
                # -----------------------------------------

                for track_id in vehicles_to_remove:
                    del vehicles[track_id]


                frame_number += 1

                time.sleep(EVENT_INTERVAL)


        except KeyboardInterrupt:

            print("\nSimulator stopped.")


# ---------------------------------------------------------
# Entry point
# ---------------------------------------------------------

if __name__ == "__main__":
    run_simulator()