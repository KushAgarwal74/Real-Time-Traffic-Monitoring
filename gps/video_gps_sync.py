import cv2
import ffmpeg

from datetime import datetime, timedelta
from dateutil import parser as date_parser

from gps.gpx_parser import GPXParser
from gps.synchronizer import GPSSynchronizer


class VideoGPSSynchronizer:

    def __init__(
        self,
        video_path,
        gpx_path,
        metadata_represents="end"
    ):

        self.video_path = video_path
        self.gpx_path = gpx_path
        self.metadata_represents = metadata_represents

        # ----------------------------------------
        # 1. Read video properties
        # ----------------------------------------

        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise ValueError(
                f"Could not open video: {video_path}"
            )

        self.fps = cap.get(cv2.CAP_PROP_FPS)

        self.frame_count = int(
            cap.get(cv2.CAP_PROP_FRAME_COUNT)
        )

        self.width = int(
            cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        )

        self.height = int(
            cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        )

        cap.release()

        if self.fps <= 0:
            raise ValueError("Invalid FPS")

        self.duration_seconds = (
            self.frame_count / self.fps
        )

        # ----------------------------------------
        # 2. Extract metadata timestamp
        # ----------------------------------------

        self.metadata_time = (
            self._extract_metadata_time()
        )

        # ----------------------------------------
        # 3. Calculate video start/end times
        # ----------------------------------------

        if metadata_represents == "end":

            self.video_end_time = (
                self.metadata_time
            )

            self.video_start_time = (
                self.video_end_time
                - timedelta(
                    seconds=self.duration_seconds
                )
            )

        elif metadata_represents == "start":

            self.video_start_time = (
                self.metadata_time
            )

            self.video_end_time = (
                self.video_start_time
                + timedelta(
                    seconds=self.duration_seconds
                )
            )

        else:

            raise ValueError(
                "metadata_represents must be "
                "'start' or 'end'"
            )

        # ----------------------------------------
        # 4. Load GPS timeline
        # ----------------------------------------

        parser = GPXParser(self.gpx_path)

        gps_points = parser.parse()

        if not gps_points:
            raise ValueError(
                "No GPS points found"
            )

        self.gps_synchronizer = (
            GPSSynchronizer(gps_points)
        )

        self.gps_start_time = (
            gps_points[0]["timestamp"]
        )

        self.gps_end_time = (
            gps_points[-1]["timestamp"]
        )


    def _extract_metadata_time(self):

        probe = ffmpeg.probe(
            self.video_path
        )

        # Try format tags first
        tags = (
            probe
            .get("format", {})
            .get("tags", {})
        )

        creation_time = tags.get(
            "creation_time"
        )

        # If missing, try streams
        if creation_time is None:

            for stream in probe.get(
                "streams",
                []
            ):

                stream_tags = stream.get(
                    "tags",
                    {}
                )

                creation_time = (
                    stream_tags.get(
                        "creation_time"
                    )
                )

                if creation_time:
                    break

        if creation_time is None:

            raise ValueError(
                "Video creation_time metadata "
                "not found"
            )

        return date_parser.parse(
            creation_time
        )


    def get_frame_timestamp(
        self,
        frame_number
    ):

        if (
            frame_number < 0
            or frame_number >= self.frame_count
        ):
            raise ValueError(
                f"Invalid frame number: {frame_number}"
            )

        elapsed_seconds = (
            frame_number / self.fps
        )

        return (
            self.video_start_time
            + timedelta(
                seconds=elapsed_seconds
            )
        )


    def get_location_for_frame(
        self,
        frame_number
    ):

        frame_timestamp = (
            self.get_frame_timestamp(
                frame_number
            )
        )

        # Check GPS coverage
        if (
            frame_timestamp
            < self.gps_start_time
            or frame_timestamp
            > self.gps_end_time
        ):

            return None

        return (
            self.gps_synchronizer.get_location(
                frame_timestamp
            )
        )


    def get_frame_telemetry(
        self,
        frame_number
    ):

        timestamp = (
            self.get_frame_timestamp(
                frame_number
            )
        )

        location = (
            self.get_location_for_frame(
                frame_number
            )
        )

        return {
            "frame_number": frame_number,

            "timestamp": timestamp,

            "gps": location
        }