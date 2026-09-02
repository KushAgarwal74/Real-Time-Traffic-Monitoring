class VehicleStateManager:

    def __init__(
        self,
        exit_after_frames=90,
        update_interval_frames=30
    ):

        # ----------------------------------
        # Stores all vehicle states
        # ----------------------------------

        self.vehicles = {}

        # ----------------------------------
        # Exit configuration
        # ----------------------------------

        self.exit_after_frames = (
            exit_after_frames
        )

        # ----------------------------------
        # Update event configuration
        # ----------------------------------

        self.update_interval_frames = (
            update_interval_frames
        )

    def get_plate_score(self, plate):

        if plate is None:
            return -1.0

        best_ocr = plate.get(
            "best_ocr"
        )

        if best_ocr is None:
            return -1.0

        return float(
            best_ocr.get(
                "final_score",
                -1.0
            )
        )


    def update(
        self,
        tracked_objects,
        frame_number,
        timestamp,
        camera_gps=None
    ):

        events = []

        # ======================================
        # PROCESS CURRENT VEHICLES
        # ======================================

        for obj in tracked_objects:

            track_id = obj["track_id"]

            current_plate = obj.get(
                "license_plate"
            )

            # ----------------------------------
            # NEW VEHICLE
            # ----------------------------------

            if track_id not in self.vehicles:

                stable_vehicle_type = (
                    obj["class_name"]
                )

                self.vehicles[track_id] = {

                    "track_id": track_id,

                    "vehicle_type": (
                        stable_vehicle_type
                    ),

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

                    "last_update_event_frame": (
                        frame_number
                    ),

                    # ----------------------------------
                    # Best plate detected so far
                    # ----------------------------------

                    "best_license_plate": (
                        current_plate
                    )
                }

                events.append({

                    "event_type": (
                        "vehicle_detected"
                    ),

                    "track_id": int(track_id),

                    "vehicle_type": (
                        stable_vehicle_type
                    ),

                    "frame_number": int(
                        frame_number
                    ),

                    "timestamp": (
                        timestamp.isoformat()
                    ),

                    "bbox": obj["bbox"],

                    "confidence": float(
                        obj.get(
                            "confidence",
                            0.0
                        )
                    ),

                    "camera_gps": camera_gps,

                    "license_plate": (
                        current_plate
                    )
                })

            # ----------------------------------
            # EXISTING VEHICLE
            # ----------------------------------

            else:

                vehicle = self.vehicles[
                    track_id
                ]

                # ----------------------------------
                # Stable vehicle type
                # ----------------------------------

                stable_vehicle_type = (
                    vehicle["vehicle_type"]
                )

                vehicle["last_frame"] = (
                    frame_number
                )

                vehicle["last_timestamp"] = (
                    timestamp
                )

                vehicle["last_bbox"] = (
                    obj["bbox"]
                )

                vehicle["confidence"] = (
                    obj.get(
                        "confidence",
                        0.0
                    )
                )

                vehicle["camera_gps"] = (
                    camera_gps
                )

                vehicle["observations"] += 1

                vehicle["active"] = True

                # ----------------------------------
                # Update best plate
                # ----------------------------------

                if current_plate is not None:

                    best_plate = vehicle[
                        "best_license_plate"
                    ]

                    current_score = self.get_plate_score(
                        current_plate
                    )

                    best_score = self.get_plate_score(
                        best_plate
                    )

                    # ----------------------------------
                    # No previous plate
                    # ----------------------------------

                    if best_plate is None:

                        vehicle[
                            "best_license_plate"
                        ] = current_plate


                    # ----------------------------------
                    # Replace only with better plate
                    # ----------------------------------

                    elif current_score > best_score:

                        vehicle[
                            "best_license_plate"
                        ] = current_plate
                # ----------------------------------
                # Generate periodic update event
                # ----------------------------------

                frames_since_last_update = (

                    frame_number
                    -
                    vehicle[
                        "last_update_event_frame"
                    ]

                )

                if (
                    frames_since_last_update
                    >=
                    self.update_interval_frames
                ):

                    events.append({

                        "event_type": (
                            "vehicle_updated"
                        ),

                        "track_id": int(
                            track_id
                        ),

                        "vehicle_type": (
                            stable_vehicle_type
                        ),

                        "frame_number": int(
                            frame_number
                        ),

                        "timestamp": (
                            timestamp.isoformat()
                        ),

                        "bbox": obj["bbox"],

                        "confidence": float(
                            obj.get(
                                "confidence",
                                0.0
                            )
                        ),

                        "camera_gps": camera_gps,

                        # ----------------------------------
                        # Best plate found so far
                        # ----------------------------------

                        "license_plate": (
                            vehicle[
                                "best_license_plate"
                            ]
                        )
                    })

                    vehicle[
                        "last_update_event_frame"
                    ] = frame_number


        # ======================================
        # DETECT EXITED VEHICLES
        # ======================================

        for track_id, vehicle in (
            self.vehicles.items()
        ):

            if not vehicle["active"]:

                continue

            frames_missing = (

                frame_number
                -
                vehicle["last_frame"]

            )

            if (
                frames_missing
                >=
                self.exit_after_frames
            ):

                vehicle["active"] = False

                events.append({

                    "event_type": (
                        "vehicle_exited"
                    ),

                    "track_id": int(
                        track_id
                    ),

                    "vehicle_type": (
                        vehicle[
                            "vehicle_type"
                        ]
                    ),

                    "frame_number": int(
                        frame_number
                    ),

                    "timestamp": (
                        timestamp.isoformat()
                    ),

                    "last_seen_frame": int(
                        vehicle["last_frame"]
                    ),

                    "camera_gps": (
                        vehicle[
                            "camera_gps"
                        ]
                    ),

                    # ----------------------------------
                    # Best plate found during
                    # the entire track lifetime
                    # ----------------------------------

                    "license_plate": (
                        vehicle[
                            "best_license_plate"
                        ]
                    )
                })

        return events