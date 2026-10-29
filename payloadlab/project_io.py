"""Versioned project serialization for the native desktop application."""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_FORMAT = "payloadlab-project"
PROJECT_VERSION = 1


def save_project(path: str | Path, mode: str, values: dict[str, str], mount_points_text: str) -> None:
    data = {
        "format": PROJECT_FORMAT,
        "version": PROJECT_VERSION,
        "mode": mode,
        "values": dict(values),
        "mount_points": mount_points_text.strip(),
    }
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_project(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("format") == PROJECT_FORMAT:
        if data.get("version") != PROJECT_VERSION:
            raise ValueError(f"Unsupported PayloadLab project version: {data.get('version')}")
        if data.get("mode") not in {"space", "robot", "drone"}:
            raise ValueError("Project mode must be space, robot or drone.")
        if not isinstance(data.get("values"), dict):
            raise ValueError("Project values are missing or invalid.")
        return data
    return _convert_example(data)


def _convert_example(data: dict) -> dict:
    """Convert the bundled illustrative example format into a project."""
    if "robot_mass_kg" in data:
        payload_position = data.get("payload_position_m", [0.22, 0.0, 0.72])
        robot_cg = data.get("robot_cg_m", [0.0, 0.0, 0.31])
        support = data.get("support_polygon_m", [0.9, 0.62])
        return {
            "format": PROJECT_FORMAT,
            "version": PROJECT_VERSION,
            "mode": "robot",
            "mount_points": "-125, -85\n125, -85\n125, 85\n-125, 85",
            "values": {
                "payload_name": str(data.get("payload_name", "Illustrative sensor pod")),
                "mass": str(data.get("payload_mass_kg", 12.0)),
                "robot_mass": str(data["robot_mass_kg"]),
                "robot_cg_x": str(robot_cg[0]), "robot_cg_y": str(robot_cg[1]), "robot_cg_z": str(robot_cg[2]),
                "payload_x": str(payload_position[0]), "payload_y": str(payload_position[1]), "payload_z": str(payload_position[2]),
                "support_l": str(support[0]), "support_w": str(support[1]),
                "long_accel": str(data.get("longitudinal_acceleration_mps2", 2.5)),
                "lat_accel": str(data.get("lateral_acceleration_mps2", 1.8)),
            },
        }
    if "dimensions_mm" in data and "mount_points_mm" in data:
        dimensions, cg, acceleration = data["dimensions_mm"], data.get("cg_mm", [0, 0, 100]), data.get("acceleration_g", [0, 0, 1])
        return {
            "format": PROJECT_FORMAT,
            "version": PROJECT_VERSION,
            "mode": "space",
            "mount_points": "\n".join(f"{p[0]}, {p[1]}" for p in data["mount_points_mm"]),
            "values": {
                "payload_name": str(data.get("payload_name", "Illustrative hosted payload")),
                "length": str(dimensions[0]), "width": str(dimensions[1]), "height": str(dimensions[2]),
                "mass": str(data.get("mass_kg", 18.0)),
                "cg_x": str(cg[0]), "cg_y": str(cg[1]), "cg_z": str(cg[2]),
                "accel_x": str(acceleration[0]), "accel_y": str(acceleration[1]), "accel_z": str(acceleration[2]),
                "safety_factor": str(data.get("safety_factor", 1.5)),
            },
        }
    raise ValueError("The selected JSON file is not a PayloadLab project or recognized example.")
