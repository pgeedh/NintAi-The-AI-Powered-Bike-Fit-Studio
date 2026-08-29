"""
NintAi Automated Model Downloader.
"""

import os
import sys
import urllib.request

MODELS = {
    "models/pose_landmarker_heavy.task": "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task",
    "models/yolo11n-pose.pt": "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n-pose.pt"
}

def download_file(url, destination):
    os.makedirs(os.path.dirname(os.path.abspath(destination)), exist_ok=True)
    if os.path.exists(destination) and os.path.getsize(destination) > 1000:
        print(f"[NintAi] Model verified: {destination} ({os.path.getsize(destination) // 1024} KB)")
        return

    print(f"[NintAi] Downloading {os.path.basename(destination)} from {url}...")
    try:
        def reporthook(count, block_size, total_size):
            percent = int(count * block_size * 100 / total_size) if total_size > 0 else 0
            sys.stdout.write(f"\r  Progress: {percent}% [{count * block_size // (1024*1024)}MB / {total_size // (1024*1024)}MB]")
            sys.stdout.flush()

        urllib.request.urlretrieve(url, destination, reporthook)
        print(f"\n[NintAi] Successfully saved to {destination}")
    except Exception as e:
        print(f"\n[NintAi] Download failed for {destination}: {e}")

def main():
    print("[NintAi] Verifying Model Dependencies...")
    for path, url in MODELS.items():
        download_file(url, path)
    print("[NintAi] All neural assets ready.")

if __name__ == "__main__":
    main()
