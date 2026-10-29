# PayloadLab — Laelaps AI Demo Video Script

**Recommended duration:** 90–120 seconds  
**Format:** 1920×1080 screen recording with voice-over  
**Positioning:** A self-initiated engineering tool demonstrating structured payload-integration thinking for mobile robots and multirotor drones.

## Before recording

1. Run `python app.py` and wait for the default result to appear.
2. Maximize the PayloadLab window or keep it at its native 1450×900 size.
3. Close notifications and unrelated windows.
4. Keep the cursor movement slow and deliberate.
5. Do not describe the results as certification, validation, or a replacement for detailed engineering analysis.

## Scene-by-scene script

### 0:00–0:10 — Introduction

**On screen:** PayloadLab title and the three mode selectors. Start with the complete window visible.

**Voice-over:**

> Hi, I’m Tomás Miravete. I built PayloadLab as a compact Python engineering workbench for preliminary payload-integration screening across hosted platforms, mobile robots, and drones.

### 0:10–0:22 — Why it is relevant

**On screen:** Move the cursor across **Mobile Robot Payload** and **Drone Payload** without rapidly clicking.

**Voice-over:**

> For a company like Laelaps AI, where payloads may be integrated on walking robots or aerial platforms, the same early design questions appear repeatedly: mass properties, centre of gravity, interface loads, mounting reactions, stability, and available performance margin.

### 0:22–0:52 — Mobile robot demonstration

**On screen:** Select **Mobile Robot Payload**. Pause while the default calculation appears. Point to:

- payload mass and payload position inputs;
- support-polygon dimensions;
- the screening-status card;
- longitudinal and lateral critical acceleration;
- the support-polygon graphic.

Change **Payload position X** from `0.22` m to `0.32` m and select **Calculate**. Pause on the updated stability margin and sensitivity chart.

**Voice-over:**

> In robot mode, the tool combines the robot and payload mass properties and projects the effective load line onto a simplified support polygon. It reports the governing stability margin and independent critical acceleration and slope estimates. Here, moving the payload forward immediately updates the combined response and shows how installation position affects stability.

### 0:52–1:20 — Drone demonstration

**On screen:** Select **Drone Payload**. Point to:

- drone and payload mass properties;
- rotor count and maximum total thrust;
- gross-mass, CG-offset, and required-thrust-margin limits;
- hover thrust per rotor;
- thrust margin and combined-CG display;
- payload-mass sensitivity chart.

Change **Payload mass** from `2.0` kg to `2.5` kg and select **Calculate**. Pause on the changed thrust margin.

**Voice-over:**

> In drone mode, PayloadLab combines the airframe and payload centres of gravity, checks gross mass and lateral CG offset, and estimates hover thrust per rotor, thrust utilization, available thrust margin, and simplified acceleration and tilt limits. Increasing payload mass makes the performance trade-off visible immediately.

### 1:20–1:40 — Mounting interface and engineering discipline

**On screen:** Open the **Mounting-point loads** tab. Slowly highlight the `MP-01`, `MP-02`, and subsequent rows, then return to **Overview**.

**Voice-over:**

> Across every mode, the same deterministic rigid-body engine transfers the applied load to the mounting plane and distributes reactions across clearly identified mounting points. It also verifies force and moment equilibrium, so an under-constrained mounting pattern cannot be presented as a passing result.

### 1:40–1:55 — Scope and closing

**On screen:** Open **Method and limits**, pause on the scope boundary, then finish on the main overview.

**Voice-over:**

> This is intentionally an early-stage screening tool, not an FEA model or a flight- or gait-dynamics simulation. I built it to demonstrate how I structure ambiguous multidisciplinary problems into transparent assumptions, calculations, checks, and engineering decisions. Thank you for watching.

## Optional closing title card

**PayloadLab — Mechanical Payload Integration Workbench**  
Python · Tkinter · NumPy · pandas · deterministic engineering calculations  
GitHub: `github.com/tomas-miravetejimenez/PayloadLab`

## Recording notes

- Use the robot and drone modes as the main story; the hosted-space mode can remain visible in the header to show extensibility.
- Keep the application’s caveats visible or mention them verbally. Avoid implying knowledge of Laelaps AI’s confidential requirements or specific platform specifications.
- Use the built-in default values as illustrative examples, not as Laelaps design data.
- A calm 90-second explanation is stronger than demonstrating every input or export feature.
