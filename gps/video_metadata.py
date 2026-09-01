import ffmpeg


def print_video_metadata(video_path):

    probe = ffmpeg.probe(video_path)

    print("\nFORMAT TAGS")
    print("=" * 60)

    tags = probe.get("format",{}).get("tags",{})

    for key, value in tags.items():

        print(f"{key}: {value}")


    print("\nSTREAM TAGS")
    print("=" * 60)

    for stream in probe.get("streams", []):

        print(
            f"\nStream Type: {stream.get('codec_type')}"
        )

        stream_tags = stream.get(
            "tags",
            {}
        )

        for key, value in stream_tags.items():

            print(f"{key}: {value}")

def main():
    
    video_path = "data/raw/city/traffic_1.mp4"

    print_video_metadata(video_path)

if __name__ == "__main__":
    main()