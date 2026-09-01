import cv2

VIDEO_FILE = "data/raw/city/traffic_1.mp4"
# VIDEO_FILE = "data/raw/city/traffic_2.mp4"


def main():

    cap = cv2.VideoCapture(VIDEO_FILE)

    if not cap.isOpened():
        print("ERROR: Could not open video")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)

    frame_count = int(
        cap.get(cv2.CAP_PROP_FRAME_COUNT)
    )

    width = int(
        cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    )

    height = int(
        cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    )

    duration_seconds = frame_count / fps

    print("\nVIDEO INFORMATION")
    print("=" * 50)

    print(f"FPS: {fps}")
    print(f"Frame Count: {frame_count}")
    print(f"Resolution: {width}x{height}")
    print(f"Duration: {duration_seconds:.2f} seconds")

    cap.release()


if __name__ == "__main__":
    main()