"""
NintAi Unit & Integration Test Suite.
"""
import os
import sys
import numpy as np
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src import core
from src import biomech
from src import fit_profiles as fp
from src import pose_backends as pb
from src import report
from src import ai_report


def test_calculate_angle():
    # 90 degree right angle: (0, 1) -> (0, 0) -> (1, 0)
    ang = core.calculate_angle([0, 1], [0, 0], [1, 0])
    assert abs(ang - 90.0) < 1e-4

    # Straight line 180 degrees: (-1, 0) -> (0, 0) -> (1, 0)
    ang180 = core.calculate_angle([-1, 0], [0, 0], [1, 0])
    assert abs(ang180 - 180.0) < 1e-4


def test_horizontal_angle_folding():
    # Facing right 45 deg slope
    ang_r = core.calculate_angle_horizontal([0, 0], [1, 1])
    assert abs(ang_r - 45.0) < 1e-4

    # Facing left equivalent slope (should be folded into 0-90 acute angle)
    ang_l = core.calculate_angle_horizontal([0, 0], [-1, 1])
    assert abs(ang_l - 45.0) < 1e-4


def test_circle_fit():
    # Known circle at (10, 20) with radius 5
    angles = np.linspace(0, 2 * np.pi, 24, endpoint=False)
    pts = np.column_stack([10 + 5 * np.cos(angles), 20 + 5 * np.sin(angles)])
    fit = biomech.fit_circle(pts)
    assert fit is not None
    cx, cy, r, res = fit
    assert abs(cx - 10.0) < 1e-3
    assert abs(cy - 20.0) < 1e-3
    assert abs(r - 5.0) < 1e-3
    assert res < 1e-3


def test_fit_profiles_and_scoring():
    # Test optimal road endurance values
    metrics_optimal = {
        'knee_ext': 145.0,
        'knee_flex': 72.0,
        'hip_closed': 55.0,
        'torso': 50.0,
        'shoulder': 88.0,
        'elbow': 158.0,
    }
    score = fp.fit_score(metrics_optimal, 'road_endurance')
    assert score is not None and score >= 90

    # Test out of range saddle (low knee extension)
    metrics_low_saddle = dict(metrics_optimal, knee_ext=125.0)
    recs = fp.build_recommendations(metrics_low_saddle, 'road_endurance')
    assert any("Raise your saddle" in r['title'] for r in recs)


def test_pose_backends_available():
    avail = pb.available()
    assert 'mediapipe' in avail
    assert 'rtmpose' in avail


def test_offline_coach_fallback():
    metrics = {'knee_ext': 145.0, 'torso': 48.0}
    recs = [{'title': 'Raise saddle ~5 mm', 'detail': 'Low knee angle'}]
    text, src = ai_report.generate_ai_analysis(metrics, recs, api_key=None)
    assert src == 'offline'
    assert "Golden rule" in text or "Raise saddle" in text


def test_pdf_generation_bytes():
    result = {
        'mode': 'video',
        'profile': 'road_endurance',
        'score': 85,
        'metrics': {'knee_ext': 146.0, 'torso': 48.0, 'shoulder': 88.0},
        'statuses': {'knee_ext': 'ok', 'torso': 'ok', 'shoulder': 'ok'},
        'recommendations': [{'title': 'Fit looks great', 'detail': 'All in range'}],
        'warnings': [],
    }
    pdf_bytes = report.generate_fit_report(result, snapshot_paths={})
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b'%PDF')
