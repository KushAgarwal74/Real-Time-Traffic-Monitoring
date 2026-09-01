class VehicleStateManager:

    def __init__(
        self,
        exit_after_frames=90,
        update_interval_frames=30
    ):

        # Stores state for every known vehicle track
        self.vehicles = {}

        # Number of missing frames before declaring
        # that a vehicle has exited
        self.exit_after_frames = exit_after_frames

        # Generate vehicle_updated events
        # at this interval
        self.update_interval_frames = update_interval_frames


    def update(
        self,
        tracked_objects,
        frame_number,
        timestamp,
        camera_gps=None
    ):

        events = []

        # ======================================
        # PROCESS CURRENTLY VISIBLE VEHICLES
        # ======================================

        for obj in tracked_objects:

            track_id = obj["track_id"]

            # ----------------------------------
            # NEW VEHICLE
            # ----------------------------------

            if track_id not in self.vehicles:

                # Store vehicle type ONCE.
                # This becomes stable for this track.
                stable_vehicle_type = obj["class_name"]

                self.vehicles[track_id] = {

                    "track_id": track_id,

                    "vehicle_type": stable_vehicle_type,

                    "first_frame": frame_number,

                    "last_frame": frame_number,

                    "first_timestamp": timestamp,

                    "last_timestamp": timestamp,

                    "last_bbox": obj["bbox"],

                    "confidence": obj.get(
                        "confidence",
                        0.0
                    ),

                    "camera_gps": camera_gps,

                    "observations": 1,

                    "active": True,

                    # Used to control update events
                    "last_update_event_frame": frame_number
                }

                # ----------------------------------
                # VEHICLE DETECTED EVENT
                # ----------------------------------

                events.append({

                    "event_type": "vehicle_detected",

                    "track_id": int(track_id),

                    "vehicle_type": stable_vehicle_type,

                    "frame_number": int(frame_number),

                    "timestamp": timestamp.isoformat(),

                    "bbox": obj["bbox"],

                    "confidence": float(
                        obj.get("confidence", 0.0)
                    ),

                    "camera_gps": camera_gps
                })


            # ----------------------------------
            # EXISTING VEHICLE
            # ----------------------------------

            else:

                vehicle = self.vehicles[track_id]

                # IMPORTANT:
                # Do not change vehicle_type.
                # We use the original type detected
                # for this track.
                stable_vehicle_type = vehicle[
                    "vehicle_type"
                ]

                vehicle["last_frame"] = frame_number

                vehicle["last_timestamp"] = timestamp

                vehicle["last_bbox"] = obj["bbox"]

                vehicle["confidence"] = obj.get(
                    "confidence",
                    0.0
                )

                vehicle["camera_gps"] = camera_gps

                vehicle["observations"] += 1

                vehicle["active"] = True

                # ----------------------------------
                # VEHICLE UPDATED EVENT
                # ----------------------------------

                frames_since_last_update = (

                    frame_number
                    - vehicle[
                        "last_update_event_frame"
                    ]

                )

                if (
                    frames_since_last_update
                    >= self.update_interval_frames
                ):

                    events.append({

                        "event_type": "vehicle_updated",

                        "track_id": int(track_id),

                        "vehicle_type": stable_vehicle_type,

                        "frame_number": int(frame_number),

                        "timestamp": timestamp.isoformat(),

                        "bbox": obj["bbox"],

                        "confidence": float(
                            obj.get(
                                "confidence",
                                0.0
                            )
                        ),

                        "camera_gps": camera_gps
                    })

                    vehicle[
                        "last_update_event_frame"
                    ] = frame_number


        # ======================================
        # DETECT EXITED VEHICLES
        # ======================================

        for track_id, vehicle in self.vehicles.items():

            if not vehicle["active"]:
                continue

            frames_missing = (

                frame_number
                - vehicle["last_frame"]

            )

            if frames_missing >= self.exit_after_frames:

                vehicle["active"] = False

                events.append({

                    "event_type": "vehicle_exited",

                    "track_id": int(track_id),

                    "vehicle_type": vehicle[
                        "vehicle_type"
                    ],

                    "frame_number": int(frame_number),

                    "timestamp": timestamp.isoformat(),

                    "last_seen_frame": int(
                        vehicle["last_frame"]
                    ),

                    "camera_gps": vehicle[
                        "camera_gps"
                    ]
                })

        return events