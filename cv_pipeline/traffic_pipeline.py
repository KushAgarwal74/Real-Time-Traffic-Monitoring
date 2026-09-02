from cv_pipeline.traffic_tracker import (
    TrafficTracker
)

from cv_pipeline.vehicle_plate_pipeline import (
    VehiclePlatePipeline
)

from cv_pipeline.vehicle_state_manager import (
    VehicleStateManager
)


class TrafficPipeline:

    def __init__(
        self,
        plate_model_path="models/license-plate-finetune-v1s.pt",
        exit_after_frames=90,
        update_interval_frames=30
    ):

        # ==========================================
        # VEHICLE TRACKER
        # ==========================================

        self.tracker = TrafficTracker()


        # ==========================================
        # LICENSE PLATE PIPELINE
        # ==========================================

        self.plate_pipeline = (
            VehiclePlatePipeline(
                model_path=plate_model_path
            )
        )


        # ==========================================
        # VEHICLE STATE MANAGER
        # ==========================================

        self.state_manager = (
            VehicleStateManager(
                exit_after_frames=exit_after_frames,
                update_interval_frames=update_interval_frames
            )
        )


    # ==================================================
    # PROCESS ONE FRAME
    # ==================================================

    def process_frame(
        self,
        frame,
        frame_number,
        timestamp,
        camera_gps=None
    ):

        # ==========================================
        # STEP 1: TRACK VEHICLES
        # ==========================================

        tracked_objects = (
            self.tracker.track(
                frame
            )
        )


        # ==========================================
        # STEP 2: DETECT PLATES + OCR
        # ==========================================

        plates_by_track = (
            self.plate_pipeline.process_frame(
                frame=frame,
                tracked_objects=tracked_objects
            )
        )


        # ==========================================
        # STEP 3: ATTACH PLATE DATA
        # ==========================================

        for vehicle in tracked_objects:

            track_id = vehicle[
                "track_id"
            ]

            vehicle[
                "license_plate"
            ] = plates_by_track.get(
                track_id
            )


        # ==========================================
        # STEP 4: UPDATE VEHICLE STATES
        # ==========================================

        events = (
            self.state_manager.update(

                tracked_objects=tracked_objects,

                frame_number=frame_number,

                timestamp=timestamp,

                camera_gps=camera_gps
            )
        )


        # ==========================================
        # STEP 5: CLEAR OCR MEMORY
        # AFTER VEHICLE EXIT
        # ==========================================

        for event in events:

            if event["event_type"] == "vehicle_exited":

                self.plate_pipeline.clear_track(
                    event["track_id"]
                )


        # ==========================================
        # RETURN COMPLETE FRAME RESULT
        # ==========================================

        return {

            "frame_number": frame_number,

            "tracked_objects": tracked_objects,

            "plates_by_track": plates_by_track,

            "events": events
        }