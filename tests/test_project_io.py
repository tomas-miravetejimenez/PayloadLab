import json

from payloadlab.project_io import load_project, save_project


def test_project_round_trip(tmp_path):
    target = tmp_path / "case.json"
    save_project(target, "drone", {"mass": "2.5", "rotor_count": "4"}, "-1, -1\n1, 1")
    loaded = load_project(target)
    assert loaded["mode"] == "drone"
    assert loaded["values"]["mass"] == "2.5"


def test_hosted_example_conversion(tmp_path):
    target = tmp_path / "example.json"
    target.write_text(json.dumps({"dimensions_mm": [3, 4, 5], "mount_points_mm": [[0, 0], [1, 1]], "mass_kg": 2}), encoding="utf-8")
    loaded = load_project(target)
    assert loaded["mode"] == "space"
    assert loaded["values"]["height"] == "5"
