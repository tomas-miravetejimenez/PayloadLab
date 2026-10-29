from payloadlab.reporting import export_html_report, export_mount_csv
from payloadlab.rigid_body import interface_load
from payloadlab.bolt_group import distribute_mount_loads


def _loads():
    load = interface_load(2, [1, 0, 1], [0, 0, 50])
    return distribute_mount_loads([[-50, -50], [50, -50], [50, 50], [-50, 50]], load.force_n, load.moment_nm).loads


def test_csv_and_printable_report_exports(tmp_path):
    csv_path = tmp_path / "loads.csv"
    report_path = tmp_path / "report.html"
    export_mount_csv(csv_path, _loads())
    export_html_report(report_path, "Test payload", "Drone Payload", {"Status": "PASS"}, _loads(), ["Screening only"])
    assert "combined_n" in csv_path.read_text(encoding="utf-8")
    report = report_path.read_text(encoding="utf-8")
    assert "Test payload" in report
    assert "@media print" in report
