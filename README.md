# PayloadLab: Mechanical Payload Integration Workbench

PayloadLab is a Python desktop application for early payload integration checks. It runs in a native Tkinter window and does not use a browser or local web server.

It has three calculation modes:

- **Hosted Space Payload:** interface reactions, mass and envelope checks, and CG height sensitivity.
- **Mobile Robot Payload:** mounting loads and quasi-static stability within a rectangular support polygon.
- **Drone Payload:** combined mass properties, gross mass, CG offset, hover thrust, thrust margin, and simplified acceleration limits.

The user supplies the requirements and engineering inputs. The included values are examples and should be replaced for a real study.

## Run the desktop application

```powershell
python -m pip install -r requirements.txt
python app.py
```

`python run_payloadlab.py` opens the same application and is kept as a compatibility launcher.

## Input workflow

Inputs are grouped in a scrollable panel on the left:

1. **Payload properties:** envelope, mass, and CG coordinates.
2. **Mounting interface:** mount coordinates, safety factor, and bolt allowables.
3. **Interface load case:** signed acceleration components.
4. **Mode-specific inputs:** host constraints, robot geometry, or drone thrust limits.

Each numerical field shows its unit. Mounting points use the names `MP-01`, `MP-02`, and so on, which avoids confusion with metric thread sizes. Enter one `X, Y` coordinate pair per line:

```text
-125, -85
 125, -85
 125,  85
-125,  85
```

Select **Calculate** to update the results. If an input is missing or invalid, the application identifies the affected field.

The buttons above the results can open or save a project, export mount reactions to CSV, and create a printable HTML report.

## Results

The results area shows:

- interface force and moment;
- the governing mounting point;
- pass or fail status;
- force and moment equilibrium errors;
- a layout view and sensitivity graph;
- loads at each mounting point; and
- assumptions and limits.

Robot mode also reports critical longitudinal and lateral acceleration and slope estimates. Drone mode reports total mass, hover thrust per rotor, thrust margin, combined CG offset, and simplified acceleration and tilt limits.

## Calculation model

The application calculates the signed inertial load with `F = m g₀ n`. It transfers the load from the payload CG to the mounting-plane origin with `M = r × F`, then distributes the reactions across the mounting points.

Axial reactions use a minimum-norm linear solution for `Fz`, `Mx`, and `My`. In-plane reactions combine direct shear with tangential shear about the mounting-point centroid. The application checks force and moment equilibrium after each calculation.

Robot stability uses a quasi-static rectangular support polygon. The model combines the robot and payload CGs, includes the entered slope and acceleration, and finds the shortest distance from the projected load point to a support edge.

Drone mode uses total available thrust and combined mass properties. It does not model propeller performance, battery voltage, wind, motor response, rotor failure, or flight-control behaviour.

## Tests

```powershell
python -m pytest -q
```

The tests cover load transfer, bolt-group equilibrium, utilization, robot stability, drone calculations, project files, report exports, and the desktop interface.

## Project structure

```text
app.py                          Tkinter application and entry point
run_payloadlab.py               compatibility launcher
payloadlab/rigid_body.py        force and moment transfer
payloadlab/bolt_group.py        mounting-point reaction distribution
payloadlab/robot_stability.py   combined CG and support-polygon calculation
payloadlab/drone_performance.py multirotor mass and thrust calculation
payloadlab/project_io.py        project and example loading
payloadlab/reporting.py         CSV and HTML exports
payloadlab/validation.py        input checks
examples/                       example inputs
tests/                          calculation and interface tests
```

The calculation modules do not depend on Tkinter and can be imported into another Python program or notebook.

## Scope and limitations

PayloadLab is an early screening tool. It is not a bolted-joint design calculation, FEA model, qualification assessment, or dynamic simulation. It does not calculate enclosure stress, host deformation, preload, bearing, pull-through, thread stripping, contact, fatigue, shock, or vibration.

Robot mode does not model individual foot or wheel loads, active suspension, gait, slip, tyre compliance, terrain deformation, control response, or impacts. Check the assumptions and input data before using the results in a design decision.
