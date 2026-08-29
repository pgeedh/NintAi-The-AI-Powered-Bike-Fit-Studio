"""
Automated Model Downloader for NintAi Bike Fit Studio.
Downloads MediaPipe Pose Landmarker (Heavy) and YOLO pose models if not present.
"""

import os
import sys
import urllib.request

MODELS = {
    "src/models/pose_landmarker_heavy.task": "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task",
    "yolo11n-pose.pt": "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n-pose.pt"
}

def download_file(url, destination):
    os.makedirs(os.path.dirname(os.path.abspath(destination)), exist_ok=True)
    if os.path.exists(destination) and os.path.getsize(destination) > 1000:
        print(f"✅ {destination} already exists ({os.path.getsize(destination) // 1024} KB).")
        return

    print(f"📥 Downloading {os.path.basename(destination)} from {url}...")
    try:
        def reporthook(count, block_size, total_size):
            percent = int(count * block_size * 100 / total_size) if total_size > 0 else 0
            sys.stdout.write(f"\r  -> Progress: {percent}% [{count * block_size // (1024*1024)}MB / {total_size // (1024*1024)}MB]")
            sys.stdout.flush()

        urllib.request.urlretrieve(url, destination, reporthook)
        print(f"\n✅ Successfully saved to {destination}")
    except Exception as e:
        print(f"\n❌ Error downloading {destination}: {e}")

def main():
    print("🚴 NintAi Model Setup & Downloader")
    print("=" * 45)
    for path, url in MODELS.items():
        download_file(url, path)
    print("=" * 45)
    print("🎉 All models verified and ready for AI fitting!")

if __name__ == "__main__":
    main()
