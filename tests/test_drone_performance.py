import numpy as np

from payloadlab.drone_performance import evaluate_drone_payload


def test_combined_cg_and_hover_thrust():
    result = evaluate_drone_payload(8, [0, 0, .12], 2, [.2, 0, .05], 4, 180)
    np.testing.assert_allclose(result.combined_cg_m, [.04, 0, .106])
    assert result.hover_thrust_per_rotor_n > 0
    assert result.thrust_passes


def test_gross_mass_and_cg_limits_can_fail():
    result = evaluate_drone_payload(8, [0, 0, .12], 3, [.5, 0, .05], 4, 150, maximum_gross_mass_kg=10, allowable_cg_offset_m=.05)
    assert not result.mass_passes
    assert not result.cg_passes
    assert not result.passes
