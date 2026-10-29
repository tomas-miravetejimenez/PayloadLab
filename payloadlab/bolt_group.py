"""Equal-stiffness rigid bolt-group load distribution."""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class BoltGroupResult:
    loads: pd.DataFrame
    recovered_force_n: np.ndarray
    recovered_moment_nm: np.ndarray
    force_error_n: np.ndarray
    moment_error_nm: np.ndarray
    equilibrium_ok: bool
    governing_mount: int


def _require_pattern(points_m: np.ndarray) -> None:
    if points_m.ndim != 2 or points_m.shape[1] != 2 or len(points_m) < 2:
        raise ValueError("At least two x-y mounting points are required.")
    if np.max(np.linalg.norm(points_m - points_m.mean(axis=0), axis=1)) < 1e-12:
        raise ValueError("Mounting points must not all be coincident.")


def distribute_mount_loads(
    points_mm,
    interface_force_n,
    interface_moment_nm,
    tensile_allowable_n: float | None = None,
    shear_allowable_n: float | None = None,
    safety_factor: float = 1.0,
    tolerance: float = 1e-7,
) -> BoltGroupResult:
    """Calculate mount reactions that balance a payload interface load.

    All fasteners are assigned equal translational stiffness. Axial reactions use
    the minimum-norm linear distribution that balances Fz, Mx and My. In-plane
    reactions combine equal direct shear with tangential shear about the mount
    centroid to balance Fx, Fy and Mz.
    """
    points_m = np.asarray(points_mm, dtype=float) * 1e-3
    _require_pattern(points_m)
    force = np.asarray(interface_force_n, dtype=float)
    moment = np.asarray(interface_moment_nm, dtype=float)
    if force.shape != (3,) or moment.shape != (3,):
        raise ValueError("Interface force and moment must each have three components.")
    if safety_factor <= 0:
        raise ValueError("Safety factor must be positive.")

    x, y = points_m[:, 0], points_m[:, 1]
    n = len(points_m)

    # Minimum-norm axial solution for exact force/moment equilibrium.
    axial_map = np.vstack((np.ones(n), y, -x))
    axial_target = np.array([-force[2], -moment[0], -moment[1]])
    axial = np.linalg.pinv(axial_map) @ axial_target

    xc, yc = points_m.mean(axis=0)
    dx, dy = x - xc, y - yc
    direct_x = np.full(n, -force[0] / n)
    direct_y = np.full(n, -force[1] / n)
    direct_mz = np.sum(x * direct_y - y * direct_x)
    polar = np.sum(dx**2 + dy**2)
    residual_mz = -moment[2] - direct_mz
    if polar < 1e-18 and abs(residual_mz) > tolerance:
        raise ValueError("Mounting pattern cannot react the applied torsional moment.")
    scale = residual_mz / polar if polar else 0.0
    shear_x = direct_x - scale * dy
    shear_y = direct_y + scale * dx
    shear = np.hypot(shear_x, shear_y)
    combined = np.sqrt(axial**2 + shear**2)

    recovered_force = np.array([shear_x.sum(), shear_y.sum(), axial.sum()])
    recovered_moment = np.array(
        [np.sum(y * axial), np.sum(-x * axial), np.sum(x * shear_y - y * shear_x)]
    )
    force_error = recovered_force + force
    moment_error = recovered_moment + moment
    scale_f = max(1.0, np.linalg.norm(force))
    scale_m = max(1.0, np.linalg.norm(moment))
    equilibrium_ok = bool(
        np.linalg.norm(force_error) <= tolerance * scale_f
        and np.linalg.norm(moment_error) <= tolerance * scale_m
    )

    data = {
        "mount": np.arange(1, n + 1),
        "mount_id": [f"MP-{index:02d}" for index in range(1, n + 1)],
        "x_mm": points_m[:, 0] * 1e3,
        "y_mm": points_m[:, 1] * 1e3,
        "axial_n": axial,
        "shear_x_n": shear_x,
        "shear_y_n": shear_y,
        "shear_n": shear,
        "combined_n": combined,
    }
    axial_util = np.zeros(n)
    shear_util = np.zeros(n)
    if tensile_allowable_n and tensile_allowable_n > 0:
        axial_util = np.maximum(axial, 0.0) * safety_factor / tensile_allowable_n
        data["axial_util"] = axial_util
    if shear_allowable_n and shear_allowable_n > 0:
        shear_util = shear * safety_factor / shear_allowable_n
        data["shear_util"] = shear_util
    if (tensile_allowable_n and tensile_allowable_n > 0) or (
        shear_allowable_n and shear_allowable_n > 0
    ):
        # Simple quadratic interaction for preliminary screening only.
        combined_util = np.sqrt(axial_util**2 + shear_util**2)
        data["combined_util"] = combined_util
        governing = int(np.argmax(combined_util))
    else:
        governing = int(np.argmax(combined))
    return BoltGroupResult(
        loads=pd.DataFrame(data),
        recovered_force_n=recovered_force,
        recovered_moment_nm=recovered_moment,
        force_error_n=force_error,
        moment_error_nm=moment_error,
        equilibrium_ok=equilibrium_ok,
        governing_mount=governing + 1,
    )
