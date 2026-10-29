"""Rigid-body load transfer from payload CG to the mounting plane."""

from dataclasses import dataclass

import numpy as np

from .units import G0, MM_TO_M


@dataclass(frozen=True)
class InterfaceLoad:
    force_n: np.ndarray
    moment_nm: np.ndarray


def interface_load(mass_kg: float, acceleration_g, cg_mm) -> InterfaceLoad:
    """Return inertial force and r×F moment at the mounting-plane origin.

    Acceleration components are signed multiples of standard gravity. CG input is
    in millimetres and output is SI (N and N·m).
    """
    if mass_kg <= 0:
        raise ValueError("Payload mass must be positive.")
    acceleration_g = np.asarray(acceleration_g, dtype=float)
    cg_m = np.asarray(cg_mm, dtype=float) * MM_TO_M
    if acceleration_g.shape != (3,) or cg_m.shape != (3,):
        raise ValueError("Acceleration and CG must each contain x, y and z.")
    force = mass_kg * G0 * acceleration_g
    return InterfaceLoad(force_n=force, moment_nm=np.cross(cg_m, force))
