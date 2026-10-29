import tkinter as tk

import pytest

from app import PayloadLabApp


@pytest.fixture(scope="module")
def desktop_app():
    try:
        app = PayloadLabApp()
    except tk.TclError as exc:
        pytest.skip(f"Tk desktop is unavailable: {exc}")
    app.withdraw()
    app.update_idletasks()
    yield app
    app.destroy()


def test_space_mode_calculates_constraints(desktop_app):
    desktop_app.calculate()
    assert desktop_app.last_mounts is not None
    assert desktop_app.summary_values["status"].cget("text") == "PASS"
    assert "PASS" in desktop_app.mode_metrics[0][1].cget("text")
    assert "PASS" in desktop_app.mode_metrics[1][1].cget("text")


def test_robot_and_drone_modes_rebuild_and_calculate(desktop_app):
    for mode in ("robot", "drone"):
        desktop_app.mode.set(mode)
        desktop_app._build_inputs()
        desktop_app.calculate()
        assert desktop_app.last_mounts is not None
        assert desktop_app.summary_values["status"].cget("text") == "PASS"
    assert "HOVER" in desktop_app.mode_metrics[1][0].cget("text")
