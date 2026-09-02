import os

from cv_pipeline.traffic_pipeline import (
    TrafficPipeline
)

from producers.video_runner import (
    VideoRunner
)


def main():

    # ==========================================
    # INPUT VIDEO
    # ==========================================

    input_video = (
        "data/raw/city/traffic_1.mp4"
    )


    # ==========================================
    # OUTPUT VIDEO
    # ==========================================

    output_video = (
        "outputs/videos/traffic_1_output.mp4"
    )


    # ==========================================
    # LICENSE PLATE MODEL
    # ==========================================

    plate_model = (
        "models/license-plate-finetune-v1s.pt"
    )


    # ==========================================
    # CREATE OUTPUT DIRECTORY
    # ==========================================

    os.makedirs(

        "outputs/videos",

        exist_ok=True
    )


    # ==========================================
    # CREATE TRAFFIC PIPELINE
    # ==========================================

    pipeline = TrafficPipeline(

        plate_model_path=plate_model,

        exit_after_frames=90,

        update_interval_frames=30
    )


    # ==========================================
    # CREATE VIDEO RUNNER
    # ==========================================

    runner = VideoRunner(

        pipeline=pipeline
    )


    # ==========================================
    # RUN VIDEO
    # ==========================================

    runner.run(

        input_path=input_video,

        output_path=output_video,

        events_path="data/processed/traffic_1/events.jsonl",

        summary_path="data/processed/traffic_1/summary.json",

        camera_gps=None
    )


if __name__ == "__main__":

    main()