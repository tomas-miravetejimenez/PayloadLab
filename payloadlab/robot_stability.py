"""Quasi-static stability of a rigid robot on a rectangular support polygon."""

from dataclasses import dataclass

import numpy as np

from .units import G0


@dataclass(frozen=True)
class StabilityResult:
    total_mass_kg: float
    combined_cg_m: np.ndarray
    effective_acceleration_mps2: np.ndarray
    load_point_m: np.ndarray
    margins_m: dict[str, float]
    governing_edge: str
    governing_margin_m: float
    passes: bool
    critical_longitudinal_accel_mps2: float
    critical_lateral_accel_mps2: float
    critical_longitudinal_slope_deg: float
    critical_lateral_slope_deg: float


def evaluate_stability(
    robot_mass_kg: float,
    robot_cg_m,
    payload_mass_kg: float,
    payload_cg_robot_m,
    support_length_m: float,
    support_width_m: float,
    longitudinal_accel_mps2: float = 0.0,
    lateral_accel_mps2: float = 0.0,
    longitudinal_slope_deg: float = 0.0,
    lateral_slope_deg: float = 0.0,
    required_margin_m: float = 0.0,
) -> StabilityResult:
    if min(robot_mass_kg, payload_mass_kg, support_length_m, support_width_m) <= 0:
        raise ValueError("Masses and support-polygon dimensions must be positive.")
    robot_cg = np.asarray(robot_cg_m, dtype=float)
    payload_cg = np.asarray(payload_cg_robot_m, dtype=float)
    total_mass = robot_mass_kg + payload_mass_kg
    combined = (robot_mass_kg * robot_cg + payload_mass_kg * payload_cg) / total_mass
    if combined[2] <= 0:
        raise ValueError("Combined CG height must be above the support plane.")

    pitch = np.deg2rad(longitudinal_slope_deg)
    roll = np.deg2rad(lateral_slope_deg)
    gravity_body = np.array(
        [-G0 * np.sin(pitch), G0 * np.sin(roll) * np.cos(pitch), -G0 * np.cos(roll) * np.cos(pitch)]
    )
    effective = gravity_body + np.array([-longitudinal_accel_mps2, -lateral_accel_mps2, 0.0])
    if effective[2] >= -1e-9:
        raise ValueError("Effective load vector does not intersect the support plane.")
    t = -combined[2] / effective[2]
    load_point = combined + t * effective
    hx, hy = support_length_m / 2.0, support_width_m / 2.0
    margins = {
        "+X (front)": hx - load_point[0],
        "−X (rear)": hx + load_point[0],
        "+Y (left)": hy - load_point[1],
        "−Y (right)": hy + load_point[1],
    }
    governing_edge = min(margins, key=margins.get)
    governing_margin = margins[governing_edge]
    longitudinal_clearance = max(0.0, hx - abs(combined[0]))
    lateral_clearance = max(0.0, hy - abs(combined[1]))
    return StabilityResult(
        total_mass_kg=total_mass,
        combined_cg_m=combined,
        effective_acceleration_mps2=effective,
        load_point_m=load_point,
        margins_m=margins,
        governing_edge=governing_edge,
        governing_margin_m=governing_margin,
        passes=bool(governing_margin >= required_margin_m),
        critical_longitudinal_accel_mps2=G0 * longitudinal_clearance / combined[2],
        critical_lateral_accel_mps2=G0 * lateral_clearance / combined[2],
        critical_longitudinal_slope_deg=float(np.rad2deg(np.arctan2(longitudinal_clearance, combined[2]))),
        critical_lateral_slope_deg=float(np.rad2deg(np.arctan2(lateral_clearance, combined[2]))),
    )
