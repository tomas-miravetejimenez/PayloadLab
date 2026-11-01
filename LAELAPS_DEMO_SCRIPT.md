# PayloadLab: Laelaps AI Demo Voice-over

**Target length:** About four minutes

**Format:** 1920 x 1080 screen recording with voice-over

## Before recording

1. Run `python app.py` and wait for the default result to appear.
2. Maximize the PayloadLab window or keep it at its native 1450×900 size.
3. Close notifications and unrelated windows.
4. Move the cursor slowly and leave enough time to read each result.
5. Present the tool as an early calculation aid, not a validated design tool.

## Script

### 0:00 to 0:25: Introduction

**On screen:** PayloadLab title and the three mode selectors. Start with the complete window visible.

**Voice-over:**

> Hi, I am Tomás Miravete. This is PayloadLab, a Python desktop application I built to check payload integration on mobile robots and drones. It also includes a hosted space payload mode, since the mounting-load calculation is shared across the three cases.

### 0:25 to 0:50: What the tool checks

**On screen:** Move the cursor across **Mobile Robot Payload** and **Drone Payload** without rapidly clicking.

**Voice-over:**

> The aim is to answer a few early questions before detailed analysis. How does the payload move the centre of gravity? What loads reach each mounting point? How much stability or thrust margin remains? The inputs are visible, and the results update without relying on hidden requirements or generated data.

### 0:50 to 2:00: Mobile robot mode

**On screen:** Select **Mobile Robot Payload**. Pause while the default calculation appears. Point to:

- payload mass and payload position inputs;
- support-polygon dimensions;
- the screening-status card;
- longitudinal and lateral critical acceleration;
- the support-polygon graphic.

Change **Payload position X** from `0.22` m to `0.32` m and select **Calculate**. Pause on the updated stability margin and sensitivity chart.

**Voice-over:**

> I will start with the mobile robot mode. The left panel contains the payload mass and position, the robot mass and centre of gravity, the support dimensions, the slope, and the acceleration case.
>
> The model combines the robot and payload centres of gravity. It then projects the effective load line onto a rectangular support polygon. The stability margin is the shortest distance from that point to a support edge. A positive value remains inside the polygon, zero is the theoretical tipping boundary, and a negative value is outside it.
>
> The graph varies the payload position along the X axis while keeping the other inputs fixed. I will move the payload from 0.22 metres to 0.32 metres. After recalculating, the graph and the governing margin change. This gives a quick view of how the installation position affects the robot.

### 2:00 to 3:05: Drone mode

**On screen:** Select **Drone Payload**. Point to:

- drone and payload mass properties;
- rotor count and maximum total thrust;
- gross-mass, CG-offset, and required-thrust-margin limits;
- hover thrust per rotor;
- thrust margin and combined-CG display;
- payload-mass sensitivity chart.

Change **Payload mass** from `2.0` kg to `2.5` kg and select **Calculate**. Pause on the changed thrust margin.

**Voice-over:**

> In drone mode, the inputs include the airframe mass, payload mass, rotor count, total available thrust, gross-mass limit, and allowable CG offset.
>
> PayloadLab calculates the combined centre of gravity and the thrust needed to hover. It reports the thrust per rotor, remaining thrust margin, and simplified acceleration and tilt limits.
>
> I will increase the payload mass from 2 to 2.5 kilograms. The new result shows the reduction in thrust margin and the higher hover-thrust demand. The sensitivity graph shows the same trend over a wider payload-mass range.

### 3:05 to 3:35: Mounting loads

**On screen:** Open the **Mounting-point loads** tab. Slowly highlight the `MP-01`, `MP-02`, and subsequent rows, then return to **Overview**.

**Voice-over:**

> The mounting-point table is available in every mode. The calculation transfers the load from the payload centre of gravity to the mounting plane and distributes the reactions across the entered points. It also checks force and moment equilibrium. If the mounting pattern cannot react the applied load, the overall result fails.

### 3:35 to 4:00: Limits and closing

**On screen:** Open **Method and limits**, pause on the scope boundary, then finish on the main overview.

**Voice-over:**

> This is an early screening tool. It is not an FEA model, a detailed joint calculation, or a flight or gait simulation. The method and limits tab lists the assumptions so that the result can be reviewed in context.
>
> The project source and calculation notes are available in the GitHub repository linked in my application. Thank you for watching.

## Optional closing title card

**PayloadLab: Mechanical Payload Integration Workbench**

Python, Tkinter, NumPy, and pandas

GitHub: `github.com/tomas-miravetejimenez/PayloadLab`

## Recording notes

- Focus on the robot and drone modes.
- Mention the limits shown in the application.
- Treat the default values as examples, not as Laelaps design data.
- Leave short pauses after each input change so the viewer can read the new result.
