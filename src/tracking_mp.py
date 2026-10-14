import mediapipe as mp
import cv2
import numpy as np
import os
import time

# New Tasks API
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class PoseDetectorMP:
    def __init__(self, model_path='src/models/pose_landmarker_heavy.task', model_complexity=2, mode='video'):
        """
        Initializes MediaPipe Pose Landmarker (Tasks API).
        mode: 'video' for frame sequences, 'image' for single photos.
        """
        # Ensure model exists
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at {model_path}. Please download it.")

        base_options = python.BaseOptions(model_asset_path=model_path)
        self.mode = mode
        running_mode = vision.RunningMode.IMAGE if mode == 'image' else vision.RunningMode.VIDEO
        
        # Video mode for consistent tracking
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

    def close(self):
        try:
            self.landmarker.close()
        except Exception:
            pass

    def predict(self, image, timestamp_ms=None):
        """
        Runs MP Pose. Image must be RGB.
        timestamp_ms: Required for VIDEO/LIVE_STREAM mode.
        """
        # Convert BGR to RGB and MediaPipe Image
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)

        if self.mode == 'image':
            return self.landmarker.detect(mp_image)

        if timestamp_ms is None:
            timestamp_ms = int(time.time() * 1000)
        
        # Process (detect_for_video)
        detection_result = self.landmarker.detect_for_video(mp_image, int(timestamp_ms))
        
        return detection_result

    def get_landmarks_dict(self, results, image_shape):
        """
        Extracts MP landmarks and maps to NintAi keys.
        """
        if not results.pose_landmarks or len(results.pose_landmarks) == 0:
            return {}

        h, w = image_shape[:2]
        lm_dict = {}
        
        # Take first detection
        landmarks = results.pose_landmarks[0]
        
        # Mapping 0-32 (Standard Blazepose)
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
                # MP Task API landmarks have x, y, z, visibility, presence
                if lm.visibility > 0.5:
                    lm_dict[name] = [lm.x * w, lm.y * h]
                
        return lm_dict
