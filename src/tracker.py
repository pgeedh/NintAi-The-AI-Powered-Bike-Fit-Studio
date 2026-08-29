"""
NintAi Pose Tracking Module.
Uses Google MediaPipe BlazePose Heavy (33 landmarks + 3D metric coordinates).
"""

import os
import time
import urllib.request
import cv2
import numpy as np

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

DEFAULT_MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'pose_landmarker_heavy.task')

class PoseTracker:
    def __init__(self, model_path: str = None, running_mode=vision.RunningMode.VIDEO):
        if model_path is None:
            model_path = os.path.abspath(DEFAULT_MODEL_PATH)

        if not os.path.exists(model_path):
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            print(f"[NintAi] Downloading pose_landmarker_heavy.task to {model_path}...")
            url = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task"
            urllib.request.urlretrieve(url, model_path)

        self.model_path = model_path
        self.running_mode = running_mode

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=running_mode,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
            output_segmentation_masks=False
        )
        self.landmarker = vision.PoseLandmarker.create_from_options(options)

    def process_frame(self, image: np.ndarray, timestamp_ms: int = None):
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)

        if self.running_mode == vision.RunningMode.VIDEO:
            if timestamp_ms is None:
                timestamp_ms = int(time.time() * 1000)
            return self.landmarker.detect_for_video(mp_image, int(timestamp_ms))
        else:
            return self.landmarker.detect(mp_image)

    def extract_landmarks_2d(self, results, image_shape: tuple) -> dict:
        if not results or not results.pose_landmarks or len(results.pose_landmarks) == 0:
            return {}

        h, w = image_shape[:2]
        lm_dict = {}
        landmarks = results.pose_landmarks[0]

        mapping = {
            0: 'nose',
            2: 'left_eye', 5: 'right_eye',
            7: 'left_ear', 8: 'right_ear',
            11: 'left_shoulder', 12: 'right_shoulder',
            13: 'left_elbow', 14: 'right_elbow',
            15: 'left_wrist', 16: 'right_wrist',
            23: 'left_hip', 24: 'right_hip',
            25: 'left_knee', 26: 'right_knee',
            27: 'left_ankle', 28: 'right_ankle',
            29: 'left_heel', 30: 'right_heel',
            31: 'left_toe', 32: 'right_toe'
        }

        for idx, name in mapping.items():
            if idx < len(landmarks):
                lm = landmarks[idx]
                if lm.visibility > 0.35:
                    lm_dict[name] = [float(lm.x * w), float(lm.y * h)]

        return lm_dict

    def extract_world_landmarks_3d(self, results) -> dict:
        if not results or not results.pose_world_landmarks or len(results.pose_world_landmarks) == 0:
            return {}

        world_lms = results.pose_world_landmarks[0]
        mapping = {
            0: 'nose',
            11: 'left_shoulder', 12: 'right_shoulder',
            13: 'left_elbow', 14: 'right_elbow',
            15: 'left_wrist', 16: 'right_wrist',
            23: 'left_hip', 24: 'right_hip',
            25: 'left_knee', 26: 'right_knee',
            27: 'left_ankle', 28: 'right_ankle',
            29: 'left_heel', 30: 'right_heel',
            31: 'left_toe', 32: 'right_toe'
        }

        world_dict = {}
        for idx, name in mapping.items():
            if idx < len(world_lms):
                lm = world_lms[idx]
                if lm.visibility > 0.35:
                    world_dict[name] = np.array([lm.x, lm.y, lm.z])

        return world_dict
