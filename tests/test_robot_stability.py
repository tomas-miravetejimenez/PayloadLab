import numpy as np

from payloadlab.robot_stability import evaluate_stability


def test_centered_level_system_projects_to_origin():
    result = evaluate_stability(80, [0, 0, .3], 20, [0, 0, .7], 1.0, .6)
    np.testing.assert_allclose(result.load_point_m[:2], [0, 0], atol=1e-12)
    assert result.governing_margin_m == .3
    assert result.passes


def test_forward_cg_reduces_front_margin():
    result = evaluate_stability(80, [0, 0, .3], 20, [.5, 0, .7], 1.0, .6)
    assert result.margins_m["+X (front)"] < result.margins_m["−X (rear)"]


def test_acceleration_moves_load_line():
    result = evaluate_stability(80, [0, 0, .3], 20, [0, 0, .7], 1.0, .6, longitudinal_accel_mps2=2)
    assert result.load_point_m[0] < 0
