import numpy as np

from payloadlab.bolt_group import distribute_mount_loads


POINTS = [[-100, -50], [100, -50], [100, 50], [-100, 50]]


def test_symmetric_vertical_load_is_equal():
    result = distribute_mount_loads(POINTS, [0, 0, -400], [0, 0, 0])
    np.testing.assert_allclose(result.loads.axial_n, 100)
    assert result.loads.mount_id.tolist() == ["MP-01", "MP-02", "MP-03", "MP-04"]
    assert result.equilibrium_ok


def test_full_six_component_equilibrium():
    result = distribute_mount_loads(POINTS, [120, -85, 450], [12, -8, 5])
    np.testing.assert_allclose(result.recovered_force_n, [-120, 85, -450], atol=1e-10)
    np.testing.assert_allclose(result.recovered_moment_nm, [-12, 8, -5], atol=1e-10)
    assert result.equilibrium_ok


def test_tensile_utilization_ignores_compression():
    result = distribute_mount_loads(POINTS, [0, 0, 400], [0, 0, 0], tensile_allowable_n=1000)
    np.testing.assert_allclose(result.loads.axial_util, 0)
