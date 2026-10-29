import numpy as np

from payloadlab.rigid_body import interface_load
from payloadlab.units import G0


def test_force_and_cross_product_moment():
    result = interface_load(10.0, [2.0, 0.0, 0.0], [0.0, 0.0, 100.0])
    np.testing.assert_allclose(result.force_n, [20 * G0, 0, 0])
    np.testing.assert_allclose(result.moment_nm, [0, 2 * G0, 0])


def test_zero_offset_has_zero_moment():
    result = interface_load(5.0, [1, 2, 3], [0, 0, 0])
    np.testing.assert_allclose(result.moment_nm, 0)
