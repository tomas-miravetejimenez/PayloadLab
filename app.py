"""PayloadLab native desktop workbench. Run with: python app.py"""

from __future__ import annotations

import math
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import numpy as np

from payloadlab.bolt_group import BoltGroupResult, distribute_mount_loads
from payloadlab.drone_performance import DroneScreenResult, evaluate_drone_payload
from payloadlab.project_io import load_project, save_project as save_project_file
from payloadlab.reporting import export_html_report, export_mount_csv
from payloadlab.rigid_body import InterfaceLoad, interface_load
from payloadlab.robot_stability import StabilityResult, evaluate_stability
from payloadlab.validation import envelope_status, optional_limit_status


APP_BG = "#f4f6f7"
PANEL_BG = "#ffffff"
SIDEBAR_BG = "#eef1f3"
INK = "#1d2935"
MUTED = "#647482"
LINE = "#d7dee3"
ACCENT = "#315e7d"
PASS = "#267052"
FAIL = "#a43f3f"
WARNING = "#896a24"


class ScrollableFrame(ttk.Frame):
    """Vertically scrollable frame used for the input deck."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)
        self.canvas = tk.Canvas(self, background=SIDEBAR_BG, highlightthickness=0, width=410)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.body = ttk.Frame(self.canvas, style="Sidebar.TFrame", padding=(14, 10, 14, 18))
        self.window_id = self.canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.body.bind("<Configure>", lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self.window_id, width=e.width))
        self.canvas.bind("<Enter>", lambda _e: self.canvas.bind_all("<MouseWheel>", self._mousewheel))
        self.canvas.bind("<Leave>", lambda _e: self.canvas.unbind_all("<MouseWheel>"))

    def _mousewheel(self, event: tk.Event) -> None:
        self.canvas.yview_scroll(int(-event.delta / 120), "units")


class PayloadLabApp(tk.Tk):
    """Native PayloadLab application backed by the deterministic engine."""

    def __init__(self) -> None:
        super().__init__()
        self.title("PayloadLab — Mechanical Payload Integration Workbench")
        self.geometry("1450x900")
        self.minsize(1180, 720)
        self.configure(background=APP_BG)
        self.mode = tk.StringVar(value="space")
        self.values: dict[str, tk.StringVar] = {}
        self.mount_text: tk.Text | None = None
        self.summary_values: dict[str, ttk.Label] = {}
        self.mode_metrics: list[tuple[ttk.Label, ttk.Label]] = []
        self.cached_draw: tuple | None = None
        self.last_mounts: BoltGroupResult | None = None
        self.last_summary: dict[str, str] = {}
        self._configure_styles()
        self._build_shell()
        self._build_inputs()
        self.after(150, self.calculate)

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure(".", font=("Segoe UI", 10), foreground=INK)
        style.configure("TFrame", background=APP_BG)
        style.configure("Panel.TFrame", background=PANEL_BG)
        style.configure("Sidebar.TFrame", background=SIDEBAR_BG)
        style.configure("Header.TFrame", background="#243746")
        style.configure("HeaderTitle.TLabel", background="#243746", foreground="#ffffff", font=("Segoe UI Semibold", 17))
        style.configure("HeaderSub.TLabel", background="#243746", foreground="#ced8df", font=("Segoe UI", 9))
        style.configure("Section.TLabelframe", background=SIDEBAR_BG, bordercolor=LINE, relief="solid")
        style.configure("Section.TLabelframe.Label", background=SIDEBAR_BG, foreground=ACCENT, font=("Segoe UI Semibold", 10))
        style.configure("Sidebar.TLabel", background=SIDEBAR_BG, foreground=INK)
        style.configure("Help.TLabel", background=SIDEBAR_BG, foreground=MUTED, font=("Segoe UI", 8))
        style.configure("Unit.TLabel", background=SIDEBAR_BG, foreground=MUTED, font=("Segoe UI", 9))
        style.configure("Panel.TLabel", background=PANEL_BG, foreground=INK)
        style.configure("Muted.Panel.TLabel", background=PANEL_BG, foreground=MUTED, font=("Segoe UI", 9))
        style.configure("Card.TFrame", background=PANEL_BG, bordercolor=LINE, relief="solid")
        style.configure("CardLabel.TLabel", background=PANEL_BG, foreground=MUTED, font=("Segoe UI Semibold", 8))
        style.configure("CardValue.TLabel", background=PANEL_BG, foreground=INK, font=("Segoe UI Semibold", 15))
        style.configure("Primary.TButton", background=ACCENT, foreground="#ffffff", padding=(14, 9), font=("Segoe UI Semibold", 10))
        style.map("Primary.TButton", background=[("active", "#274f6b")])
        style.configure("Mode.TRadiobutton", background="#243746", foreground="#dce5eb", padding=(12, 8), font=("Segoe UI Semibold", 9))
        style.map("Mode.TRadiobutton", background=[("selected", "#ffffff")], foreground=[("selected", ACCENT)])
        style.configure("Treeview", rowheight=27, background="#ffffff", fieldbackground="#ffffff", bordercolor=LINE)
        style.configure("Treeview.Heading", background="#e9eef1", foreground=INK, font=("Segoe UI Semibold", 9))
        style.configure("TNotebook", background=APP_BG, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(13, 8), font=("Segoe UI Semibold", 9))

    def _build_shell(self) -> None:
        header = ttk.Frame(self, style="Header.TFrame", padding=(22, 12))
        header.pack(fill="x")
        title_block = ttk.Frame(header, style="Header.TFrame")
        title_block.pack(side="left")
        ttk.Label(title_block, text="PayloadLab", style="HeaderTitle.TLabel").pack(anchor="w")
        ttk.Label(title_block, text="Mechanical Payload Integration Workbench", style="HeaderSub.TLabel").pack(anchor="w")
        mode_box = ttk.Frame(header, style="Header.TFrame")
        mode_box.pack(side="right")
        ttk.Radiobutton(mode_box, text="Hosted Space Payload", variable=self.mode, value="space", style="Mode.TRadiobutton", command=self._mode_changed).pack(side="left", padx=3)
        ttk.Radiobutton(mode_box, text="Mobile Robot Payload", variable=self.mode, value="robot", style="Mode.TRadiobutton", command=self._mode_changed).pack(side="left", padx=3)
        ttk.Radiobutton(mode_box, text="Drone Payload", variable=self.mode, value="drone", style="Mode.TRadiobutton", command=self._mode_changed).pack(side="left", padx=3)

        main = ttk.Panedwindow(self, orient="horizontal")
        main.pack(fill="both", expand=True)
        self.input_panel = ScrollableFrame(main)
        self.output_panel = ttk.Frame(main, style="Panel.TFrame", padding=(20, 16))
        main.add(self.input_panel, weight=0)
        main.add(self.output_panel, weight=1)
        self._build_output_panel()

    def _build_output_panel(self) -> None:
        heading = ttk.Frame(self.output_panel, style="Panel.TFrame")
        heading.pack(fill="x", pady=(0, 12))
        self.result_title = ttk.Label(heading, text="Analysis results", style="Panel.TLabel", font=("Segoe UI Semibold", 17))
        self.result_title.pack(side="left")
        heading_right = ttk.Frame(heading, style="Panel.TFrame")
        heading_right.pack(side="right")
        actions = ttk.Frame(heading_right, style="Panel.TFrame")
        actions.pack(anchor="e")
        ttk.Button(actions, text="Open…", command=self.open_project).pack(side="left", padx=2)
        ttk.Button(actions, text="Save…", command=self.save_project).pack(side="left", padx=2)
        ttk.Button(actions, text="Export CSV", command=self.export_csv).pack(side="left", padx=2)
        ttk.Button(actions, text="Report…", command=self.export_report).pack(side="left", padx=2)
        self.equilibrium_label = ttk.Label(heading_right, text="Ready", style="Muted.Panel.TLabel")
        self.equilibrium_label.pack(anchor="e", pady=(5, 0))

        cards = ttk.Frame(self.output_panel, style="Panel.TFrame")
        cards.pack(fill="x", pady=(0, 12))
        for index, key in enumerate(("force", "moment", "governing", "status")):
            cards.columnconfigure(index, weight=1, uniform="card")
            card = ttk.Frame(cards, style="Card.TFrame", padding=(12, 10))
            card.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 5, 0 if index == 3 else 5))
            ttk.Label(card, text=key.upper(), style="CardLabel.TLabel").pack(anchor="w")
            value = ttk.Label(card, text="—", style="CardValue.TLabel")
            value.pack(anchor="w", pady=(5, 1))
            sub = ttk.Label(card, text="", style="Muted.Panel.TLabel", wraplength=210)
            sub.pack(anchor="w")
            self.summary_values[key] = value
            self.summary_values[f"{key}_sub"] = sub

        facts = ttk.Frame(self.output_panel, style="Panel.TFrame")
        facts.pack(fill="x", pady=(0, 12))
        for index in range(4):
            facts.columnconfigure(index, weight=1, uniform="fact")
            item = ttk.Frame(facts, style="Panel.TFrame", padding=(8, 5))
            item.grid(row=0, column=index, sticky="ew")
            label = ttk.Label(item, text="—", style="CardLabel.TLabel")
            label.pack(anchor="w")
            value = ttk.Label(item, text="—", style="Panel.TLabel", font=("Segoe UI Semibold", 10))
            value.pack(anchor="w", pady=(2, 0))
            self.mode_metrics.append((label, value))

        self.notebook = ttk.Notebook(self.output_panel)
        self.notebook.pack(fill="both", expand=True)
        overview = ttk.Frame(self.notebook, style="Panel.TFrame", padding=10)
        loads = ttk.Frame(self.notebook, style="Panel.TFrame", padding=10)
        method = ttk.Frame(self.notebook, style="Panel.TFrame", padding=10)
        self.notebook.add(overview, text="Overview")
        self.notebook.add(loads, text="Mounting-point loads")
        self.notebook.add(method, text="Method and limits")

        overview.columnconfigure((0, 1), weight=1)
        overview.rowconfigure(0, weight=1)
        self.geometry_canvas = tk.Canvas(overview, background="#ffffff", highlightbackground=LINE, highlightthickness=1)
        self.geometry_canvas.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.sensitivity_canvas = tk.Canvas(overview, background="#ffffff", highlightbackground=LINE, highlightthickness=1)
        self.sensitivity_canvas.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self.geometry_canvas.bind("<Configure>", lambda _event: self._redraw_cached())
        self.sensitivity_canvas.bind("<Configure>", lambda _event: self._redraw_cached())

        columns = ("mount", "x", "y", "axial", "sx", "sy", "shear", "resultant", "util")
        self.load_table = ttk.Treeview(loads, columns=columns, show="headings")
        headings = {
            "mount": "Point ID", "x": "X [mm]", "y": "Y [mm]", "axial": "Axial [N]",
            "sx": "Shear X [N]", "sy": "Shear Y [N]", "shear": "Shear [N]",
            "resultant": "Resultant [N]", "util": "Combined util.",
        }
        for key, text in headings.items():
            self.load_table.heading(key, text=text)
            self.load_table.column(key, width=105 if key != "mount" else 65, anchor="center")
        table_scroll = ttk.Scrollbar(loads, orient="vertical", command=self.load_table.yview)
        self.load_table.configure(yscrollcommand=table_scroll.set)
        self.load_table.pack(side="left", fill="both", expand=True)
        table_scroll.pack(side="right", fill="y")

        self.method_text = tk.Text(method, wrap="word", background="#ffffff", foreground=INK, relief="flat", padx=14, pady=12, font=("Segoe UI", 10))
        self.method_text.pack(fill="both", expand=True)
        self.method_text.insert("1.0", self._method_copy())
        self.method_text.configure(state="disabled")

    def _mode_changed(self) -> None:
        self._build_inputs()
        self.after(50, self.calculate)

    def _clear_inputs(self) -> None:
        for child in self.input_panel.body.winfo_children():
            child.destroy()
        self.values.clear()
        self.mount_text = None

    def _build_inputs(self) -> None:
        self._clear_inputs()
        body = self.input_panel.body
        mode_name = {
            "space": "Hosted Space Payload",
            "robot": "Mobile Robot Payload",
            "drone": "Drone Payload",
        }[self.mode.get()]
        ttk.Label(body, text=mode_name, style="Sidebar.TLabel", font=("Segoe UI Semibold", 13)).pack(anchor="w")
        ttk.Label(body, text="Enter numerical values, then select Calculate.", style="Help.TLabel").pack(anchor="w", pady=(2, 10))

        payload = self._section(body, "1  PAYLOAD PROPERTIES")
        payload_defaults = {
            "space": ("Optical payload", "18"),
            "robot": ("Sensor pod", "12"),
            "drone": ("Aerial sensor payload", "2"),
        }
        default_name, default_mass = payload_defaults[self.mode.get()]
        self._field(payload, "payload_name", "Payload name", default_name, "text")
        self._field(payload, "length", "Envelope length", "320", "mm")
        self._field(payload, "width", "Envelope width", "240", "mm")
        self._field(payload, "height", "Envelope height", "180", "mm")
        self._field(payload, "mass", "Payload mass", default_mass, "kg")
        self._subheading(payload, "CG FROM MOUNTING-PLANE CENTRE")
        self._field(payload, "cg_x", "CG X coordinate", "18", "mm")
        self._field(payload, "cg_y", "CG Y coordinate", "-9", "mm")
        self._field(payload, "cg_z", "CG Z coordinate", "105", "mm")

        mounts = self._section(body, "2  MOUNTING INTERFACE")
        ttk.Label(mounts, text="Mount coordinates", style="Sidebar.TLabel", font=("Segoe UI Semibold", 9)).grid(row=0, column=0, sticky="w", columnspan=3)
        ttk.Label(mounts, text="One X, Y pair per line · millimetres", style="Help.TLabel").grid(row=1, column=0, sticky="w", columnspan=3, pady=(0, 4))
        self.mount_text = tk.Text(mounts, height=5, width=24, font=("Consolas", 10), background="#ffffff", foreground=INK, relief="solid", borderwidth=1)
        self.mount_text.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(0, 8))
        self.mount_text.insert("1.0", "-125, -85\n125, -85\n125, 85\n-125, 85")
        self._field(mounts, "safety_factor", "Safety factor", "1.5", "—", start_row=3)
        self._field(mounts, "bolt_diameter", "Nominal bolt diameter", "6", "mm")
        self._field(mounts, "tensile_allowable", "Bolt tensile allowable", "8000", "N")
        self._field(mounts, "shear_allowable", "Bolt shear allowable", "6000", "N")
        ttk.Label(mounts, text="Diameter is recorded for reporting only. Set an allowable to 0 to omit that utilization term.", style="Help.TLabel", wraplength=340).grid(row=7, column=0, columnspan=3, sticky="w", pady=(2, 0))

        load = self._section(body, "3  INTERFACE LOAD CASE")
        self._field(load, "load_name", "Load-case name", "Combined screening case", "text")
        self._field(load, "accel_x", "Acceleration X", "2.0", "g")
        self._field(load, "accel_y", "Acceleration Y", "-1.5", "g")
        self._field(load, "accel_z", "Acceleration Z", "6.0" if self.mode.get() == "space" else "1.0", "g")
        ttk.Label(load, text="Signs follow the right-handed convention shown below.", style="Help.TLabel", wraplength=340).grid(row=4, column=0, columnspan=3, sticky="w", pady=(3, 0))

        if self.mode.get() == "space":
            limits = self._section(body, "4  HOST CONSTRAINTS")
            self._field(limits, "mass_limit", "Payload mass limit", "25", "kg")
            self._field(limits, "env_l", "Available length", "400", "mm")
            self._field(limits, "env_w", "Available width", "300", "mm")
            self._field(limits, "env_h", "Available height", "250", "mm")
            ttk.Label(limits, text="Use 0 to disable a constraint.", style="Help.TLabel").grid(row=4, column=0, columnspan=3, sticky="w", pady=(3, 0))
        elif self.mode.get() == "robot":
            robot = self._section(body, "4  ROBOT AND SUPPORT")
            fields = [
                ("robot_mass", "Robot mass", "85", "kg"),
                ("robot_cg_x", "Robot CG X", "0", "m"), ("robot_cg_y", "Robot CG Y", "0", "m"), ("robot_cg_z", "Robot CG Z", "0.31", "m"),
                ("payload_x", "Payload position X", "0.22", "m"), ("payload_y", "Payload position Y", "0", "m"), ("payload_z", "Payload position Z", "0.72", "m"),
                ("support_l", "Support-polygon length", "0.90", "m"), ("support_w", "Support-polygon width", "0.62", "m"),
                ("long_slope", "Longitudinal slope", "5", "deg"), ("lat_slope", "Lateral slope", "3", "deg"),
                ("long_accel", "Longitudinal acceleration", "2.5", "m/s²"), ("lat_accel", "Lateral acceleration", "1.8", "m/s²"),
                ("required_margin", "Required stability margin", "50", "mm"),
            ]
            for key, label, default, unit in fields:
                self._field(robot, key, label, default, unit)
        else:
            drone = self._section(body, "4  DRONE AND PROPULSION")
            fields = [
                ("drone_mass", "Drone mass without payload", "8", "kg"),
                ("drone_cg_x", "Drone CG X", "0", "m"), ("drone_cg_y", "Drone CG Y", "0", "m"), ("drone_cg_z", "Drone CG Z", "0.12", "m"),
                ("payload_x", "Payload position X", "0.10", "m"), ("payload_y", "Payload position Y", "0", "m"), ("payload_z", "Payload position Z", "0.04", "m"),
                ("rotor_count", "Rotor count", "4", "—"),
                ("max_total_thrust", "Maximum total thrust", "180", "N"),
                ("max_gross_mass", "Maximum gross mass", "12", "kg"),
                ("allowable_cg_offset", "Allowable horizontal CG offset", "0.08", "m"),
                ("required_thrust_margin", "Required thrust margin", "20", "%"),
            ]
            for key, label, default, unit in fields:
                self._field(drone, key, label, default, unit)
            ttk.Label(drone, text="Thrust limits are user-entered aircraft data; the model does not infer motor or propeller performance.", style="Help.TLabel", wraplength=340).grid(row=len(fields), column=0, columnspan=3, sticky="w", pady=(3, 0))

        convention = ttk.Frame(body, style="Sidebar.TFrame", padding=(2, 7))
        convention.pack(fill="x")
        ttk.Label(convention, text="COORDINATE CONVENTION", style="Help.TLabel", font=("Segoe UI Semibold", 8)).pack(anchor="w")
        ttk.Label(convention, text="+X forward · +Y left · +Z away from mounting plane", style="Help.TLabel", wraplength=350).pack(anchor="w", pady=(2, 0))
        ttk.Button(body, text="Calculate", style="Primary.TButton", command=self.calculate).pack(fill="x", pady=(6, 12))

    def _section(self, parent: ttk.Frame, title: str) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent, text=title, style="Section.TLabelframe", padding=(11, 9))
        frame.pack(fill="x", pady=(0, 9))
        frame.columnconfigure(1, weight=1)
        return frame

    def _field(self, parent: ttk.LabelFrame, key: str, label: str, default: str, unit: str, start_row: int | None = None) -> tk.StringVar:
        row = start_row if start_row is not None else max((int(child.grid_info().get("row", -1)) for child in parent.grid_slaves()), default=-1) + 1
        var = tk.StringVar(value=default)
        self.values[key] = var
        ttk.Label(parent, text=label, style="Sidebar.TLabel").grid(row=row, column=0, sticky="w", padx=(0, 8), pady=3)
        ttk.Entry(parent, textvariable=var, width=15).grid(row=row, column=1, sticky="ew", pady=3)
        ttk.Label(parent, text=unit, style="Unit.TLabel", width=6).grid(row=row, column=2, sticky="w", padx=(7, 0), pady=3)
        return var

    def _subheading(self, parent: ttk.LabelFrame, text: str) -> None:
        row = max((int(child.grid_info().get("row", -1)) for child in parent.grid_slaves()), default=-1) + 1
        ttk.Separator(parent).grid(row=row, column=0, columnspan=3, sticky="ew", pady=(7, 5))
        ttk.Label(parent, text=text, style="Help.TLabel", font=("Segoe UI Semibold", 8)).grid(row=row + 1, column=0, columnspan=3, sticky="w", pady=(0, 2))

    def open_project(self) -> None:
        path = filedialog.askopenfilename(
            parent=self,
            title="Open PayloadLab project or example",
            initialdir=str(Path(__file__).with_name("examples")),
            filetypes=[("PayloadLab / JSON", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            project = load_project(path)
            self.mode.set(project["mode"])
            self._build_inputs()
            for key, value in project.get("values", {}).items():
                if key in self.values:
                    self.values[key].set(str(value))
            if self.mount_text is not None and project.get("mount_points"):
                self.mount_text.delete("1.0", "end")
                self.mount_text.insert("1.0", project["mount_points"])
            self.calculate()
        except (OSError, ValueError, TypeError) as exc:
            messagebox.showerror("Could not open project", str(exc), parent=self)

    def save_project(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Save PayloadLab project",
            defaultextension=".json",
            filetypes=[("PayloadLab project", "*.json")],
        )
        if not path:
            return
        assert self.mount_text is not None
        try:
            save_project_file(path, self.mode.get(), {key: var.get() for key, var in self.values.items()}, self.mount_text.get("1.0", "end"))
        except OSError as exc:
            messagebox.showerror("Could not save project", str(exc), parent=self)

    def export_csv(self) -> None:
        if self.last_mounts is None:
            messagebox.showinfo("No results", "Calculate a valid case before exporting.", parent=self)
            return
        path = filedialog.asksaveasfilename(parent=self, title="Export mount reactions", defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not path:
            return
        try:
            export_mount_csv(path, self.last_mounts.loads)
        except OSError as exc:
            messagebox.showerror("Could not export CSV", str(exc), parent=self)

    def export_report(self) -> None:
        if self.last_mounts is None:
            messagebox.showinfo("No results", "Calculate a valid case before exporting.", parent=self)
            return
        path = filedialog.asksaveasfilename(parent=self, title="Export printable report", defaultextension=".html", filetypes=[("Printable HTML", "*.html")])
        if not path:
            return
        notes = [
            "Equal-fastener-stiffness rigid-body mount model; not a complete bolted-joint analysis.",
            "No enclosure stress, preload, bearing, pull-through, thread, fatigue, shock or vibration assessment.",
            "Robot and drone results are quasi-static early-screening estimates, not dynamic or controller-aware simulations.",
            f"Nominal bolt diameter recorded as {self._number('bolt_diameter'):.1f} mm; diameter is not used to derive allowables.",
        ]
        try:
            export_html_report(path, self.result_title.cget("text"), self._mode_label(), self.last_summary, self.last_mounts.loads, notes)
        except OSError as exc:
            messagebox.showerror("Could not export report", str(exc), parent=self)

    def _mode_label(self) -> str:
        return {"space": "Hosted Space Payload", "robot": "Mobile Robot Payload", "drone": "Drone Payload"}[self.mode.get()]

    def _number(self, key: str) -> float:
        try:
            return float(self.values[key].get().strip().replace(",", "."))
        except ValueError as exc:
            raise ValueError(f"{key.replace('_', ' ').title()} must be a number.") from exc

    def _mount_points(self) -> np.ndarray:
        assert self.mount_text is not None
        rows = []
        for line_number, line in enumerate(self.mount_text.get("1.0", "end").splitlines(), start=1):
            if not line.strip():
                continue
            parts = [part.strip() for part in line.replace(";", ",").split(",")]
            if len(parts) != 2:
                parts = line.split()
            try:
                rows.append([float(parts[0]), float(parts[1])])
            except (ValueError, IndexError) as exc:
                raise ValueError(f"Mount line {line_number} must contain X and Y, for example: -125, -85") from exc
        if len(rows) < 2:
            raise ValueError("Enter at least two mounting points.")
        return np.asarray(rows, dtype=float)

    def calculate(self) -> None:
        """Run the deterministic engine using the visible numerical inputs."""
        try:
            dimensions = [self._number("length"), self._number("width"), self._number("height")]
            mass = self._number("mass")
            cg = [self._number("cg_x"), self._number("cg_y"), self._number("cg_z")]
            acceleration = [self._number("accel_x"), self._number("accel_y"), self._number("accel_z")]
            points = self._mount_points()
            load = interface_load(mass, acceleration, cg)
            tensile, shear = self._number("tensile_allowable"), self._number("shear_allowable")
            mounts = distribute_mount_loads(
                points, load.force_n, load.moment_nm,
                tensile_allowable_n=tensile if tensile > 0 else None,
                shear_allowable_n=shear if shear > 0 else None,
                safety_factor=self._number("safety_factor"),
            )
            stability = self._calculate_robot_stability(mass) if self.mode.get() == "robot" else None
            drone = self._calculate_drone_payload(mass) if self.mode.get() == "drone" else None
            self._update_results(load, mounts, dimensions, cg, points, stability, drone)
        except (ValueError, TypeError) as exc:
            messagebox.showerror("Input error", str(exc), parent=self)

    def _calculate_robot_stability(self, payload_mass: float) -> StabilityResult:
        return evaluate_stability(
            self._number("robot_mass"), [self._number("robot_cg_x"), self._number("robot_cg_y"), self._number("robot_cg_z")],
            payload_mass, [self._number("payload_x"), self._number("payload_y"), self._number("payload_z")],
            self._number("support_l"), self._number("support_w"), self._number("long_accel"), self._number("lat_accel"),
            self._number("long_slope"), self._number("lat_slope"), self._number("required_margin") / 1000.0,
        )

    def _calculate_drone_payload(self, payload_mass: float) -> DroneScreenResult:
        rotor_value = self._number("rotor_count")
        if not rotor_value.is_integer():
            raise ValueError("Rotor count must be a whole number.")
        return evaluate_drone_payload(
            self._number("drone_mass"), [self._number("drone_cg_x"), self._number("drone_cg_y"), self._number("drone_cg_z")],
            payload_mass, [self._number("payload_x"), self._number("payload_y"), self._number("payload_z")],
            int(rotor_value), self._number("max_total_thrust"), self._number("max_gross_mass"),
            self._number("allowable_cg_offset"), self._number("required_thrust_margin") / 100.0,
        )

    def _update_results(
        self,
        load: InterfaceLoad,
        mounts: BoltGroupResult,
        dimensions,
        cg,
        points,
        stability: StabilityResult | None,
        drone: DroneScreenResult | None,
    ) -> None:
        payload_name = self.values["payload_name"].get().strip() or "Payload"
        load_name = self.values["load_name"].get().strip() or "Load case"
        self.result_title.configure(text=f"{payload_name}  ·  {load_name}")
        self._set_card("force", "INTERFACE FORCE", f"{np.linalg.norm(load.force_n):,.0f} N", self._vector(load.force_n, "N"))
        self._set_card("moment", "INTERFACE MOMENT", f"{np.linalg.norm(load.moment_nm):,.1f} N·m", self._vector(load.moment_nm, "N·m"))
        row = mounts.loads.loc[mounts.loads["mount"] == mounts.governing_mount].iloc[0]
        point_id = str(row["mount_id"])
        self._set_card("governing", "GOVERNING POINT", point_id, f"{row['combined_n']:,.0f} N resultant")
        self.last_mounts = mounts
        bolt_passes = True
        bolt_detail = "Bolt allowables omitted"
        if "combined_util" in mounts.loads:
            utilization = float(row["combined_util"])
            bolt_passes = utilization <= 1
            bolt_detail = f"bolt utilization {utilization:.3f}"

        if stability is not None:
            status = "PASS" if stability.passes and bolt_passes else "FAIL"
            detail = f"{stability.governing_margin_m*1000:.0f} mm at {stability.governing_edge} · {bolt_detail}"
            self._set_mode_metrics([
                ("LONGITUDINAL CRITICAL ACCEL.", f"{stability.critical_longitudinal_accel_mps2:.2f} m/s²"),
                ("LATERAL CRITICAL ACCEL.", f"{stability.critical_lateral_accel_mps2:.2f} m/s²"),
                ("LONGITUDINAL CRITICAL SLOPE", f"{stability.critical_longitudinal_slope_deg:.1f}°"),
                ("LATERAL CRITICAL SLOPE", f"{stability.critical_lateral_slope_deg:.1f}°"),
            ])
        elif drone is not None:
            status = "PASS" if drone.passes and bolt_passes else "FAIL"
            detail = f"thrust margin {drone.thrust_margin*100:.1f}% · {bolt_detail}"
            gross_text = "Not set" if drone.gross_mass_margin_kg is None else f"{drone.gross_mass_margin_kg:+.2f} kg margin"
            self._set_mode_metrics([
                ("GROSS MASS", f"{drone.total_mass_kg:.2f} kg · {gross_text}"),
                ("HOVER THRUST / ROTOR", f"{drone.hover_thrust_per_rotor_n:.1f} N"),
                ("MAX. SCREENING ACCEL.", f"Z {drone.max_vertical_accel_mps2:.2f} · XY {drone.max_lateral_accel_mps2:.2f} m/s²"),
                ("COMBINED CG / MAX. TILT", f"XY {drone.cg_offset_m*1000:.0f} mm · {drone.max_tilt_deg:.1f}°"),
            ])
        else:
            mass_state, mass_margin = optional_limit_status(self._number("mass"), self._number("mass_limit"))
            env_state, env_margins = envelope_status(dimensions, [self._number("env_l"), self._number("env_w"), self._number("env_h")])
            constraints_pass = mass_state != "FAIL" and env_state != "FAIL"
            status = "PASS" if constraints_pass and bolt_passes else "FAIL"
            detail = f"mass {mass_state.lower()} · envelope {env_state.lower()} · {bolt_detail}"
            mass_text = "Not set" if mass_margin is None else f"{mass_margin:+.1f} kg margin"
            envelope_text = "Not set" if env_margins is None else " / ".join(f"{value:+.0f} mm" for value in env_margins)
            self._set_mode_metrics([
                ("PAYLOAD MASS LIMIT", f"{mass_state} · {mass_text}"),
                ("AVAILABLE ENVELOPE", f"{env_state} · {envelope_text}"),
                ("BOLT DIAMETER", f"{self._number('bolt_diameter'):.1f} mm nominal"),
                ("SAFETY FACTOR", f"{self._number('safety_factor'):.2f}"),
            ])
        self._set_card("status", "SCREENING STATUS", status, detail, status)
        self.equilibrium_label.configure(
            text=(f"Equilibrium verified · force error {np.linalg.norm(mounts.force_error_n):.1e} N · moment error {np.linalg.norm(mounts.moment_error_nm):.1e} N·m" if mounts.equilibrium_ok else "WARNING · equilibrium tolerance exceeded"),
            foreground=PASS if mounts.equilibrium_ok else FAIL,
        )
        self._populate_table(mounts)
        self.last_summary = {
            "Interface force": f"{np.linalg.norm(load.force_n):,.0f} N",
            "Interface moment": f"{np.linalg.norm(load.moment_nm):,.1f} N·m",
            "Governing point": f"{point_id} · {row['combined_n']:,.0f} N",
            "Screening status": f"{status} · {detail}",
        }
        self.cached_draw = (dimensions, cg, points, mounts, stability, drone)
        self._redraw_cached()

    def _set_mode_metrics(self, items: list[tuple[str, str]]) -> None:
        for (label_widget, value_widget), (label, value) in zip(self.mode_metrics, items):
            label_widget.configure(text=label)
            value_widget.configure(text=value)

    def _set_card(self, key: str, label: str, value: str, detail: str, status: str = "") -> None:
        card = self.summary_values[key].master
        card.winfo_children()[0].configure(text=label)
        self.summary_values[key].configure(text=value, foreground=PASS if status == "PASS" else FAIL if status == "FAIL" else INK)
        self.summary_values[f"{key}_sub"].configure(text=detail)

    def _populate_table(self, mounts: BoltGroupResult) -> None:
        self.load_table.delete(*self.load_table.get_children())
        for _, row in mounts.loads.iterrows():
            util = row.get("combined_util", np.nan)
            values = (
                str(row["mount_id"]), f"{row['x_mm']:.1f}", f"{row['y_mm']:.1f}", f"{row['axial_n']:.1f}",
                f"{row['shear_x_n']:.1f}", f"{row['shear_y_n']:.1f}", f"{row['shear_n']:.1f}", f"{row['combined_n']:.1f}",
                "—" if np.isnan(util) else f"{util:.3f}",
            )
            self.load_table.insert("", "end", values=values)

    def _redraw_cached(self) -> None:
        if not self.cached_draw:
            return
        dimensions, cg, points, mounts, stability, drone = self.cached_draw
        if drone is not None:
            self._draw_drone_layout(drone)
            masses = np.linspace(max(.1, self._number("mass") * .25), self._number("mass") * 2.0, 35)
            utilizations = []
            for payload_mass in masses:
                study = evaluate_drone_payload(
                    self._number("drone_mass"), [self._number("drone_cg_x"), self._number("drone_cg_y"), self._number("drone_cg_z")],
                    float(payload_mass), [self._number("payload_x"), self._number("payload_y"), self._number("payload_z")],
                    int(self._number("rotor_count")), self._number("max_total_thrust"), self._number("max_gross_mass"),
                    self._number("allowable_cg_offset"), self._number("required_thrust_margin") / 100.0,
                )
                utilizations.append(study.hover_thrust_utilization * 100)
            self._draw_plot(self.sensitivity_canvas, masses, utilizations, "Payload-mass sensitivity", "Payload mass [kg]", "Hover thrust utilization [%]")
        elif stability is None:
            self._draw_mount_layout(dimensions, cg, points, mounts)
            heights = np.linspace(max(0.0, cg[2] * .25), max(10.0, cg[2] * 1.75), 30)
            values = []
            mass = self._number("mass")
            accel = [self._number("accel_x"), self._number("accel_y"), self._number("accel_z")]
            for height in heights:
                case = interface_load(mass, accel, [cg[0], cg[1], height])
                group = distribute_mount_loads(points, case.force_n, case.moment_nm)
                values.append(float(group.loads["combined_n"].max()))
            self._draw_plot(self.sensitivity_canvas, heights, values, "CG-height sensitivity", "CG height [mm]", "Governing load [N]")
        else:
            self._draw_robot_layout(stability)
            positions = np.linspace(-self._number("support_l") * .55, self._number("support_l") * .55, 35)
            margins = []
            for x in positions:
                result = evaluate_stability(
                    self._number("robot_mass"), [self._number("robot_cg_x"), self._number("robot_cg_y"), self._number("robot_cg_z")],
                    self._number("mass"), [x, self._number("payload_y"), self._number("payload_z")],
                    self._number("support_l"), self._number("support_w"), self._number("long_accel"), self._number("lat_accel"),
                    self._number("long_slope"), self._number("lat_slope"), 0,
                )
                margins.append(result.governing_margin_m * 1000)
            self._draw_plot(self.sensitivity_canvas, positions, margins, "Position sensitivity", "Payload X [m]", "Stability margin [mm]")

    def _draw_mount_layout(self, dimensions, cg, points, mounts: BoltGroupResult) -> None:
        canvas = self.geometry_canvas
        canvas.delete("all")
        width, height = max(canvas.winfo_width(), 420), max(canvas.winfo_height(), 340)
        canvas.create_text(18, 18, text="Mounting-interface plan", anchor="nw", fill=INK, font=("Segoe UI Semibold", 11))
        xs, ys = list(points[:, 0]) + [-dimensions[0] / 2, dimensions[0] / 2, cg[0]], list(points[:, 1]) + [-dimensions[1] / 2, dimensions[1] / 2, cg[1]]
        scale = min((width - 80) / max(1, max(xs) - min(xs)), (height - 90) / max(1, max(ys) - min(ys)))
        cx, cy = width / 2, height / 2 + 10
        point = lambda x, y: (cx + x * scale, cy - y * scale)
        x1, y1 = point(-dimensions[0] / 2, dimensions[1] / 2)
        x2, y2 = point(dimensions[0] / 2, -dimensions[1] / 2)
        canvas.create_rectangle(x1, y1, x2, y2, outline="#8497a5", width=2)
        canvas.create_line(cx - 26, cy, cx + 35, cy, fill="#9baab4", arrow="last")
        canvas.create_line(cx, cy + 26, cx, cy - 35, fill="#9baab4", arrow="last")
        canvas.create_text(cx + 40, cy, text="+X", fill=MUTED, anchor="w")
        canvas.create_text(cx, cy - 42, text="+Y", fill=MUTED)
        loads, peak = mounts.loads["combined_n"].to_numpy(), max(float(mounts.loads["combined_n"].max()), 1.0)
        for index, ((x, y), value) in enumerate(zip(points, loads), start=1):
            px, py = point(x, y)
            radius = 6 + 7 * float(value) / peak
            canvas.create_oval(px - radius, py - radius, px + radius, py + radius, fill=ACCENT, outline="#ffffff", width=2)
            canvas.create_text(px, py - radius - 10, text=f"MP-{index:02d}", fill=INK, font=("Segoe UI Semibold", 9))
        gx, gy = point(cg[0], cg[1])
        canvas.create_line(gx - 8, gy - 8, gx + 8, gy + 8, fill=FAIL, width=2)
        canvas.create_line(gx - 8, gy + 8, gx + 8, gy - 8, fill=FAIL, width=2)
        canvas.create_text(gx + 12, gy, text="CG", fill=FAIL, anchor="w")

    def _draw_robot_layout(self, result: StabilityResult) -> None:
        canvas = self.geometry_canvas
        canvas.delete("all")
        width, height = max(canvas.winfo_width(), 420), max(canvas.winfo_height(), 340)
        canvas.create_text(18, 18, text="Support-polygon plan", anchor="nw", fill=INK, font=("Segoe UI Semibold", 11))
        length, support_width = self._number("support_l"), self._number("support_w")
        scale, cx, cy = min((width - 100) / length, (height - 100) / support_width), width / 2, height / 2 + 10
        hx, hy = length * scale / 2, support_width * scale / 2
        canvas.create_rectangle(cx - hx, cy - hy, cx + hx, cy + hy, outline=ACCENT, fill="#eef3f6", width=2)
        markers = [
            (self._number("robot_cg_x"), self._number("robot_cg_y"), "Robot CG", "#7d8c97"),
            (self._number("payload_x"), self._number("payload_y"), "Payload CG", WARNING),
            (result.combined_cg_m[0], result.combined_cg_m[1], "Combined CG", ACCENT),
            (result.load_point_m[0], result.load_point_m[1], "Load point", FAIL),
        ]
        for x, y, label, color in markers:
            px, py = cx + x * scale, cy - y * scale
            canvas.create_oval(px - 6, py - 6, px + 6, py + 6, fill=color, outline="#ffffff", width=2)
            canvas.create_text(px + 9, py - 8, text=label, anchor="sw", fill=color, font=("Segoe UI", 8))
        canvas.create_text(18, height - 20, text=f"Governing edge: {result.governing_edge} · margin {result.governing_margin_m*1000:.0f} mm", anchor="sw", fill=INK)

    def _draw_drone_layout(self, result: DroneScreenResult) -> None:
        canvas = self.geometry_canvas
        canvas.delete("all")
        width, height = max(canvas.winfo_width(), 420), max(canvas.winfo_height(), 340)
        canvas.create_text(18, 18, text="Drone mass-property plan", anchor="nw", fill=INK, font=("Segoe UI Semibold", 11))
        cx, cy = width / 2, height / 2 + 5
        span = min(width, height) * .27
        rotor_count = int(self._number("rotor_count"))
        angles = np.linspace(0, 2 * np.pi, rotor_count, endpoint=False) + np.pi / 4
        for index, angle in enumerate(angles, start=1):
            rx, ry = cx + span * np.cos(angle), cy - span * np.sin(angle)
            canvas.create_line(cx, cy, rx, ry, fill="#9aa8b2", width=3)
            canvas.create_oval(rx - 18, ry - 18, rx + 18, ry + 18, outline=ACCENT, width=2)
            canvas.create_text(rx, ry, text=str(index), fill=ACCENT, font=("Segoe UI Semibold", 8))
        canvas.create_oval(cx - 28, cy - 20, cx + 28, cy + 20, fill="#eef3f6", outline=ACCENT, width=2)
        scale = span / max(.15, self._number("allowable_cg_offset") * 2.0)
        markers = [
            (self._number("drone_cg_x"), self._number("drone_cg_y"), "Drone CG", "#7d8c97"),
            (self._number("payload_x"), self._number("payload_y"), "Payload CG", WARNING),
            (result.combined_cg_m[0], result.combined_cg_m[1], "Combined CG", FAIL if not result.cg_passes else ACCENT),
        ]
        for x, y, _label, color in markers:
            px, py = cx + x * scale, cy - y * scale
            canvas.create_oval(px - 6, py - 6, px + 6, py + 6, fill=color, outline="#ffffff", width=2)
        legend_x, legend_y = 18, 48
        for index, (_x, _y, label, color) in enumerate(markers):
            y = legend_y + index * 18
            canvas.create_oval(legend_x, y, legend_x + 9, y + 9, fill=color, outline=color)
            canvas.create_text(legend_x + 14, y + 4, text=label, anchor="w", fill=INK, font=("Segoe UI", 8))
        canvas.create_text(
            18, height - 20,
            text=f"Hover utilization {result.hover_thrust_utilization*100:.1f}% · thrust margin {result.thrust_margin*100:.1f}% · payload fraction {result.payload_mass_fraction*100:.1f}%",
            anchor="sw", fill=INK,
        )

    def _draw_plot(self, canvas: tk.Canvas, x_values, y_values, title: str, x_label: str, y_label: str) -> None:
        canvas.delete("all")
        width, height = max(canvas.winfo_width(), 420), max(canvas.winfo_height(), 340)
        left, right, top, bottom = 62, width - 24, 48, height - 52
        canvas.create_text(18, 18, text=title, anchor="nw", fill=INK, font=("Segoe UI Semibold", 11))
        canvas.create_line(left, bottom, right, bottom, fill="#8d9ca7")
        canvas.create_line(left, bottom, left, top, fill="#8d9ca7")
        xmin, xmax, ymin, ymax = float(min(x_values)), float(max(x_values)), float(min(y_values)), float(max(y_values))
        if math.isclose(ymin, ymax):
            ymin, ymax = ymin - 1, ymax + 1
        to_point = lambda x, y: (left + (x - xmin) / (xmax - xmin) * (right - left), bottom - (y - ymin) / (ymax - ymin) * (bottom - top))
        coords = []
        for x, y in zip(x_values, y_values):
            coords.extend(to_point(float(x), float(y)))
        canvas.create_line(*coords, fill=ACCENT, width=2, smooth=True)
        for fraction in (0, .5, 1):
            x, y = left + fraction * (right - left), bottom - fraction * (bottom - top)
            xv, yv = xmin + fraction * (xmax - xmin), ymin + fraction * (ymax - ymin)
            canvas.create_line(x, bottom, x, bottom + 4, fill="#8d9ca7")
            canvas.create_text(x, bottom + 9, text=f"{xv:.2g}", anchor="n", fill=MUTED, font=("Segoe UI", 8))
            canvas.create_line(left - 4, y, left, y, fill="#8d9ca7")
            canvas.create_text(left - 8, y, text=f"{yv:.3g}", anchor="e", fill=MUTED, font=("Segoe UI", 8))
        canvas.create_text((left + right) / 2, height - 18, text=x_label, fill=MUTED, font=("Segoe UI", 8))
        canvas.create_text(15, (top + bottom) / 2, text=y_label, angle=90, fill=MUTED, font=("Segoe UI", 8))

    @staticmethod
    def _vector(values, unit: str) -> str:
        return " · ".join(f"{axis} {value:,.1f}" for axis, value in zip("XYZ", values)) + f" {unit}"

    @staticmethod
    def _method_copy() -> str:
        return (
            "DETERMINISTIC MODEL\n\n"
            "• Inertial force: F = m·g₀·n using signed numerical inputs.\n"
            "• Interface moment: M = rCG × F at the mounting-plane origin.\n"
            "• Axial reactions balance Fz, Mx and My using an equal-stiffness minimum-norm distribution.\n"
            "• In-plane reactions combine equal direct shear with tangential shear about the mount centroid.\n"
            "• Bolt screening uses tension-only axial utilization and a simple quadratic interaction.\n\n"
            "SCOPE BOUNDARY\n\n"
            "This is an early screening model, not a complete bolted-joint analysis, FEA model, qualification assessment or dynamic simulation. "
            "It does not evaluate enclosure stress, host deformation, preload, bearing, pull-through, threads, contact, fatigue, shock or vibration.\n\n"
            "Robot mode uses a quasi-static rectangular-support-polygon approximation. It does not model individual contacts, active suspension, gait, "
            "wheel slip, tyre compliance, terrain deformation, control response or impacts.\n\n"
            "Drone mode uses a generic multirotor thrust-vector and mass-property approximation. It does not model aerodynamics, propeller maps, motor transients, "
            "battery voltage sag, attitude-control authority, wind, rotor failure or flight-controller response.\n\n"
            "Engineering judgement remains required. Confirm signs, load cases, allowables, boundary conditions and applicability before using results."
        )


def main() -> None:
    PayloadLabApp().mainloop()


if __name__ == "__main__":
    main()
