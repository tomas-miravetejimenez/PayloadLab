# PayloadLab — Mechanical Payload Integration Workbench

PayloadLab is a native Python desktop application for preliminary mechanical-interface screening. It opens as a normal Windows application—there is no browser, local web server, URL, or hosted interface.

The application provides two modes from the header:

- **Hosted Space Payload** — interface reactions, mass/envelope constraints and CG-height sensitivity.
- **Mobile Robot Payload** — quasi-static support-polygon stability plus the shared mounting-interface calculation.
- **Drone Payload** — combined mass properties, gross-mass and CG-offset checks, hover thrust utilization, thrust margin and approximate acceleration/tilt limits for a generic multirotor.

All engineering values are explicit numerical inputs or clearly identified illustrative defaults. PayloadLab does not infer requirements, parse documents, or call an LLM.

## Run the desktop application

```powershell
python -m pip install -r requirements.txt
python app.py
```

`python run_payloadlab.py` is retained as an equivalent compatibility command. Both commands open the same native Tkinter window.

## Input workflow

Inputs are grouped in a persistent, scrollable panel on the left:

1. **Payload properties** — envelope, mass and CG coordinates.
2. **Mounting interface** — mount coordinates, safety factor and bolt allowables.
3. **Interface load case** — named signed acceleration components.
4. **Mode-specific inputs** — host constraints, robot/support geometry, or drone mass/thrust limits.

Every numerical field displays its unit in a dedicated column. Mounting points are identified as `MP-01`, `MP-02`, etc., avoiding confusion with metric thread designations such as M6. Coordinates use one `X, Y` pair per line, for example:

```text
-125, -85
 125, -85
 125,  85
-125,  85
```

Select **Calculate** to refresh the results. Invalid or incomplete values produce a focused desktop error dialog identifying the affected field.

Use the result-panel controls to open a saved project or bundled example, save the current project, export mount reactions to CSV, or generate a self-contained printable HTML report.

## Results

The right side of the window contains:

- interface force and moment summaries;
- governing mount and screening status;
- numerical equilibrium evidence;
- mounting-pattern or support-polygon graphics;
- a sensitivity plot;
- a complete per-mount load table; and
- the documented model assumptions and limits.

Robot mode additionally reports critical longitudinal/lateral accelerations and slopes. Drone mode reports total mass, hover thrust per rotor, thrust utilization/margin, combined CG offset, and approximate vertical/lateral acceleration and tilt limits.

## Calculation model

The shared engine calculates the signed inertial load `F = m g₀ n`, transfers it from the payload CG to the mounting-plane origin with `M = r × F`, and distributes balancing reactions across the entered mount coordinates.

Axial reactions use a minimum-norm linear distribution that balances `Fz`, `Mx`, and `My`. In-plane reactions combine equal direct shear with tangential shear about the mount-group centroid to balance `Fx`, `Fy`, and `Mz`. An internal numerical check verifies force and moment equilibrium.

Robot stability is a quasi-static rectangular-support-polygon approximation. It combines robot and payload CGs, forms a body-frame effective gravity vector, projects the load line to the support plane, and reports edge margins and independent-axis critical estimates.

Drone screening is a generic multirotor thrust-vector and mass-property approximation. It does not model aerodynamics, propeller maps, battery voltage sag, motor transients, wind, rotor failure, attitude-control authority or flight-controller response.

## Tests

```powershell
python -m pytest -q
```

The tests cover load transfer, six-component bolt-group equilibrium, utilization behavior, robot stability, drone screening, project serialization, report exports and native GUI mode calculations.

## Project structure

```text
app.py                         native Tkinter application and entry point
run_payloadlab.py              compatibility desktop launcher
payloadlab/rigid_body.py       force and moment transfer
payloadlab/bolt_group.py       mount-reaction distribution and equilibrium
payloadlab/robot_stability.py  combined CG and support-polygon screening
payloadlab/drone_performance.py generic multirotor mass/thrust screening
payloadlab/project_io.py       versioned project and example loading
payloadlab/reporting.py        CSV and printable HTML exports
payloadlab/validation.py       reusable constraint checks
examples/                      illustrative numerical inputs
tests/                         deterministic calculation tests
```

The calculation engine has no GUI dependency, so it can also be imported into another Python interface, notebook or batch workflow.

## Scope and limitations

PayloadLab is an early screening model, not a complete bolted-joint analysis, FEA model, qualification assessment or dynamic simulation. It does not evaluate enclosure-wall stress, host deformation, preload, bearing, pull-through, thread stripping, nonlinear contact, fatigue, detailed shock or vibration.

Robot mode does not represent individual contact forces, active suspension, gait dynamics, wheel slip, tyre compliance, terrain deformation, control response or impact dynamics. Engineering judgement remains required.

