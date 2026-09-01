class EventFactory:

    @staticmethod
    def serialize_gps(camera_gps):

        if camera_gps is None:
            return None

        return {
            "timestamp": (
                camera_gps["timestamp"].isoformat()
                if camera_gps.get("timestamp")
                else None
            ),
            "latitude": float(camera_gps["latitude"]),
            "longitude": float(camera_gps["longitude"]),
            "elevation": (
                float(camera_gps["elevation"])
                if camera_gps.get("elevation") is not None
                else None
            )
        }

    @staticmethod
    def vehicle_detected(
        track_id,
        vehicle_type,
        confidence,
        bbox,
        frame_number,
        timestamp,
        camera_gps=None
    ):

        return {
            "event_type": "vehicle_detected",

            "track_id": int(track_id),

            "vehicle_type": vehicle_type,

            "confidence": round(
                float(confidence),
                4
            ),

            "frame_number": int(frame_number),

            "timestamp": timestamp.isoformat(),

            "bounding_box": {
                "x1": int(bbox[0]),
                "y1": int(bbox[1]),
                "x2": int(bbox[2]),
                "y2": int(bbox[3])
            },

            "camera_gps": EventFactory.serialize_gps(
                camera_gps
            )
        }

    @staticmethod
    def vehicle_updated(
        track_id,
        vehicle_type,
        confidence,
        bbox,
        frame_number,
        timestamp,
        camera_gps=None
    ):

        return {
            "event_type": "vehicle_updated",

            "track_id": int(track_id),

            "vehicle_type": vehicle_type,

            "confidence": round(
                float(confidence),
                4
            ),

            "frame_number": int(frame_number),

            "timestamp": timestamp.isoformat(),

            "bounding_box": {
                "x1": int(bbox[0]),
                "y1": int(bbox[1]),
                "x2": int(bbox[2]),
                "y2": int(bbox[3])
            },

            "camera_gps": EventFactory.serialize_gps(
                camera_gps
            )
        }

    @staticmethod
    def vehicle_exited(
        track_id,
        vehicle_type,
        frame_number,
        timestamp,
        camera_gps=None
    ):

        return {
            "event_type": "vehicle_exited",

            "track_id": int(track_id),

            "vehicle_type": vehicle_type,

            "frame_number": int(frame_number),

            "timestamp": timestamp.isoformat(),

            "camera_gps": EventFactory.serialize_gps(
                camera_gps
            )
        }