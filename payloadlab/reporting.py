"""Portable result exports for PayloadLab."""

from __future__ import annotations

import csv
import html
from pathlib import Path

import pandas as pd


def export_mount_csv(path: str | Path, loads: pd.DataFrame) -> None:
    loads.to_csv(path, index=False, quoting=csv.QUOTE_MINIMAL)


def export_html_report(path: str | Path, title: str, mode_label: str, summary: dict[str, str], loads: pd.DataFrame, notes: list[str]) -> None:
    rows = "".join(
        "<tr>" + "".join(f"<td>{html.escape(str(value))}</td>" for value in row) + "</tr>"
        for row in loads.round(3).itertuples(index=False, name=None)
    )
    headings = "".join(f"<th>{html.escape(str(column))}</th>" for column in loads.columns)
    summary_html = "".join(
        f"<div class='card'><span>{html.escape(label)}</span><strong>{html.escape(value)}</strong></div>"
        for label, value in summary.items()
    )
    notes_html = "".join(f"<li>{html.escape(note)}</li>" for note in notes)
    document = f"""<!doctype html>
<html><head><meta charset='utf-8'><title>{html.escape(title)}</title>
<style>
body{{font:14px Arial,sans-serif;color:#1d2935;margin:38px}} h1{{margin-bottom:4px}} .mode{{color:#647482;margin-bottom:24px}}
.summary{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:18px 0}} .card{{border:1px solid #d7dee3;padding:12px}}
.card span{{display:block;color:#647482;font-size:11px;text-transform:uppercase}} .card strong{{display:block;font-size:18px;margin-top:6px}}
table{{border-collapse:collapse;width:100%;font-size:12px}} th,td{{border:1px solid #d7dee3;padding:6px;text-align:right}} th{{background:#eef1f3}}
@media print{{body{{margin:12mm}} .summary{{break-inside:avoid}}}}
</style></head><body>
<h1>{html.escape(title)}</h1><div class='mode'>{html.escape(mode_label)} · Preliminary screening report</div>
<div class='summary'>{summary_html}</div><h2>Mounting-point reactions</h2><table><thead><tr>{headings}</tr></thead><tbody>{rows}</tbody></table>
<h2>Assumptions and limitations</h2><ul>{notes_html}</ul></body></html>"""
    Path(path).write_text(document, encoding="utf-8")
