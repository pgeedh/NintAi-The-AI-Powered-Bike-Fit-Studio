"""
NintAi Biomechanical Kinematics Engine.
"""

from src.tracker import PoseTracker
from src.kinematics import (
    OneEuroFilter,
    BoneLengthEnforcer,
    FIT_TARGETS,
    calculate_angle_2d,
    calculate_angle_3d,
    calculate_torso_angle,
    calculate_ankling_angle,
    compute_postural_angles
)
from src.ai_fitter import generate_consultation, generate_rule_based_breakdown
from src.pdf_generator import build_clinical_pdf
from src.analyzer import process_cycling_video

__all__ = [
    "PoseTracker",
    "OneEuroFilter",
    "BoneLengthEnforcer",
    "FIT_TARGETS",
    "calculate_angle_2d",
    "calculate_angle_3d",
    "calculate_torso_angle",
    "calculate_ankling_angle",
    "compute_postural_angles",
    "generate_consultation",
    "generate_rule_based_breakdown",
    "build_clinical_pdf",
    "process_cycling_video"
]
