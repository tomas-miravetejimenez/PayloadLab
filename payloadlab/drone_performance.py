"""Preliminary multirotor payload mass-property and thrust screening."""

from dataclasses import dataclass

import numpy as np

from .units import G0


@dataclass(frozen=True)
class DroneScreenResult:
    total_mass_kg: float
    combined_cg_m: np.ndarray
    weight_n: float
    hover_thrust_per_rotor_n: float
    hover_thrust_utilization: float
    thrust_margin: float
    max_vertical_accel_mps2: float
    max_lateral_accel_mps2: float
    max_tilt_deg: float
    payload_mass_fraction: float
    gross_mass_margin_kg: float | None
    cg_offset_m: float
    mass_passes: bool
    thrust_passes: bool
    cg_passes: bool
    passes: bool


def evaluate_drone_payload(
    drone_mass_kg: float,
    drone_cg_m,
    payload_mass_kg: float,
    payload_cg_drone_m,
    rotor_count: int,
    maximum_total_thrust_n: float,
    maximum_gross_mass_kg: float | None = None,
    allowable_cg_offset_m: float | None = None,
    required_thrust_margin: float = 0.2,
) -> DroneScreenResult:
    """Screen a payload on a generic multirotor using simple thrust limits.

    Maximum accelerations assume the stated total thrust is available and that
    thrust can be redirected without aerodynamic, motor-transient or controller
    limitations. This is an early screening model, not a flight-dynamics model.
    """
    drone_cg = np.asarray(drone_cg_m, dtype=float)
    payload_cg = np.asarray(payload_cg_drone_m, dtype=float)
    if drone_cg.shape != (3,) or payload_cg.shape != (3,):
        raise ValueError("Drone and payload CG positions must each contain x, y and z.")
    if drone_mass_kg <= 0 or payload_mass_kg <= 0:
        raise ValueError("Drone and payload masses must be positive.")
    if rotor_count < 1:
        raise ValueError("Rotor count must be at least one.")
    if maximum_total_thrust_n <= 0:
        raise ValueError("Maximum total thrust must be positive.")
    if required_thrust_margin < 0:
        raise ValueError("Required thrust margin cannot be negative.")

    total_mass = drone_mass_kg + payload_mass_kg
    combined = (drone_mass_kg * drone_cg + payload_mass_kg * payload_cg) / total_mass
    weight = total_mass * G0
    utilization = weight / maximum_total_thrust_n
    thrust_margin = maximum_total_thrust_n / weight - 1.0
    specific_thrust = maximum_total_thrust_n / total_mass
    vertical_accel = max(0.0, specific_thrust - G0)
    lateral_accel = float(np.sqrt(max(0.0, specific_thrust**2 - G0**2)))
    max_tilt = float(np.rad2deg(np.arccos(np.clip(weight / maximum_total_thrust_n, 0.0, 1.0)))) if maximum_total_thrust_n >= weight else 0.0

    gross_margin = None
    mass_passes = True
    if maximum_gross_mass_kg is not None and maximum_gross_mass_kg > 0:
        gross_margin = maximum_gross_mass_kg - total_mass
        mass_passes = gross_margin >= 0
    cg_offset = float(np.linalg.norm(combined[:2]))
    cg_passes = True
    if allowable_cg_offset_m is not None and allowable_cg_offset_m > 0:
        cg_passes = cg_offset <= allowable_cg_offset_m
    thrust_passes = thrust_margin >= required_thrust_margin

    return DroneScreenResult(
        total_mass_kg=total_mass,
        combined_cg_m=combined,
        weight_n=weight,
        hover_thrust_per_rotor_n=weight / rotor_count,
        hover_thrust_utilization=utilization,
        thrust_margin=thrust_margin,
        max_vertical_accel_mps2=vertical_accel,
        max_lateral_accel_mps2=lateral_accel,
        max_tilt_deg=max_tilt,
        payload_mass_fraction=payload_mass_kg / total_mass,
        gross_mass_margin_kg=gross_margin,
        cg_offset_m=cg_offset,
        mass_passes=mass_passes,
        thrust_passes=thrust_passes,
        cg_passes=cg_passes,
        passes=mass_passes and thrust_passes and cg_passes,
    )
