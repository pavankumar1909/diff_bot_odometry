# ROS 2 Autonomous Differential Robot – Package Architecture Overview

## Objective
Build a **demo autonomous mobile robot** capable of navigating from **point A to point B with obstacle avoidance**, using:
- Differential drive
- Wheel encoders + motors (Arduino)
- LiDAR
- Raspberry Pi (ROS 2)
- IMU optional (Phase-2)

This document defines **what ROS 2 packages are needed** and **what each package must contain**, following industry-style separation of concerns.

---

## High-Level Workspace Structure

```
ros2_ws/
├── src/
│   ├── diff_bot_description/
│   ├── diff_bot_firmware/
│   ├── diff_bot_control/
│   ├── diff_bot_sensors/
│   ├── diff_bot_localization/
│   ├── diff_bot_navigation/
│   └── diff_bot_bringup/
```

---

## 1. diff_bot_description (Robot Model)

### Purpose
Defines **what the robot is**:
- Physical structure
- Coordinate frames
- Sensor placement

### Contains
```
diff_bot_description/
├── urdf/
│   └── diff_bot.urdf.xacro
├── meshes/              (optional)
├── rviz/
│   └── robot.rviz
└── launch/
    └── display.launch.py
```

### Must Define Frames
- `base_footprint`
- `base_link`
- `left_wheel_link`, `right_wheel_link`
- `lidar_link`
- `imu_link` (even if IMU not used initially)

### Why This Package Matters
- Required for TF tree
- Used by Nav2 and RViz
- Defines collision geometry

---

## 2. diff_bot_firmware (Hardware Interface)

### Purpose
Acts as a **bridge between Arduino hardware and ROS 2** using `ros2_control`.

### Contains
```
diff_bot_firmware/
├── src/
│   └── diff_bot_interface.cpp
├── include/
│   └── diff_bot_interface.hpp
├── plugin.xml
└── CMakeLists.txt
```

### Responsibilities
- Read encoder data from Arduino
- Send motor velocity commands to Arduino
- Export interfaces:
  - State: position, velocity
  - Command: velocity

### Key Rule
> No control logic, no planning, no navigation here – **pure hardware I/O only**.

---

## 3. diff_bot_control (Controllers)

### Purpose
Configures and runs **ros2_control controllers**.

### Contains
```
diff_bot_control/
├── config/
│   └── controllers.yaml
└── launch/
    └── control.launch.py
```

### Typical Controllers
- `diff_drive_controller`
- `joint_state_broadcaster`

### Produces / Consumes
- Subscribes: `/cmd_vel`
- Publishes: `/odom`, `/joint_states`

---

## 4. diff_bot_sensors (Sensor Drivers)

### Purpose
Runs **all sensor drivers**, isolated from logic and control.

### Contains
```
diff_bot_sensors/
├── launch/
│   ├── lidar.launch.py
│   └── imu.launch.py   (optional)
└── config/
    ├── lidar.yaml
    └── imu.yaml
```

### Sensors
- LiDAR → `/scan`
- IMU (optional) → `/imu/data`

### Design Rule
> Sensors publish data only. No fusion or decisions here.

---

## 5. diff_bot_localization (State Estimation)

### Purpose
Computes **robot pose estimation**.

### Phase-1 (Minimum)
- Use wheel odometry only
- No IMU

### Phase-2 (Improved)
- Use `robot_localization` EKF
- Fuse encoders + IMU

### Contains
```
diff_bot_localization/
├── config/
│   └── ekf.yaml
└── launch/
    └── localization.launch.py
```

### Output Topic
```
/odometry/filtered
```

---

## 6. diff_bot_navigation (Navigation & Obstacle Avoidance)

### Purpose
Implements **autonomous navigation logic** using Nav2.

### Contains
```
diff_bot_navigation/
├── config/
│   └── nav2_params.yaml
├── maps/               (optional, later)
└── launch/
    └── nav2.launch.py
```

### Uses
- LiDAR (`/scan`)
- Odometry (`/odom` or `/odometry/filtered`)
- TF tree

### Responsibilities
- Path planning
- Obstacle avoidance
- Goal execution (A → B)

---

## 7. diff_bot_bringup (System Startup)

### Purpose
Starts **entire robot system in correct order**.

### Contains
```
diff_bot_bringup/
└── launch/
    └── bringup.launch.py
```

### Launch Order
1. Robot description
2. ros2_control + hardware
3. Sensors
4. Localization
5. Navigation

### Design Rule
> One launch file = full robot alive

---

## Minimal Package Set (First Demo)

For the **simplest working demo**:
```
diff_bot_description
diff_bot_firmware
diff_bot_control
diff_bot_navigation
diff_bot_bringup
```

IMU and localization fusion can be added later.

---

## System Data Flow Summary

```
Nav2 → /cmd_vel
        ↓
ros2_control → Arduino → Motors
        ↑
Encoders → ros2_control → /odom
        ↑
LiDAR → Nav2
```

(Phase-2: IMU → EKF → /odometry/filtered)

---

## Core Engineering Principle

> **Drivers → Control → Localization → Planning → Bringup**

Following this structure ensures scalability, maintainability, and industry-grade design.

---

## Next Possible Extensions
- Add IMU + EKF
- Add SLAM (`slam_toolbox`)
- Add safety watchdogs
- Add fault handling

---

## Navigation Logic (LiDAR + Encoder Only)

### Scope
This section describes the **navigation logic used in Phase-1**, where the robot:
- Has **no map**
- Uses **only LiDAR and wheel encoders**
- Performs **reactive obstacle avoidance while reaching a goal (A → B)**

---

## Inputs and Outputs

### Subscribed Topics
- `/scan` → `sensor_msgs/LaserScan` (LiDAR)
- `/odom` → `nav_msgs/Odometry` (from wheel encoders)
- `/tf` → `odom → base_link`

### Published Topic
- `/cmd_vel` → `geometry_msgs/Twist`

---

## High-Level Navigation Pipeline

```
Goal (A → B)
     ↓
Relative goal computation (odom)
     ↓
Obstacle detection (LiDAR sectors)
     ↓
Velocity decision logic
     ↓
/cmd_vel
```

---

## Step-by-Step Logic

### 1. Goal Representation
The goal is represented **relative to the `odom` frame**, not a map frame.

Example:
```
goal_x = 2.0  (meters)
goal_y = 0.0
```

---

### 2. Pose Estimation
From `/odom`, extract:
- Current position: `(x, y)`
- Orientation: `yaw` (computed from differential wheel odometry)

This is sufficient for **short-distance indoor navigation**.

---

### 3. Goal Direction Computation

Relative vector to goal:
```
dx = goal_x - x
dy = goal_y - y
```

Distance to goal:
```
distance = sqrt(dx² + dy²)
```

Desired heading:
```
target_yaw = atan2(dy, dx)
yaw_error = target_yaw - yaw
```

---

### 4. Obstacle Detection (LiDAR)

LiDAR scan is divided into three regions:
```
Left | Front | Right
```

Minimum distance is computed in each region.

Typical thresholds:
- Front obstacle: `< 0.6 m`
- Side obstacle: `< 0.4 m`

---

### 5. Decision Logic

#### Case A: Goal Reached
```
if distance < 0.15 m:
    stop robot
```

---

#### Case B: Obstacle in Front
```
if front < threshold:
    if left > right:
        rotate left
    else:
        rotate right
```

Linear velocity is set to zero; only angular velocity is applied.

---

#### Case C: Path Clear (Normal Motion)

Linear velocity:
```
v = min(max_speed, k_v × distance)
```

Angular velocity:
```
w = k_w × yaw_error
```

Publish to `/cmd_vel`.

---

### 6. Control Loop

- Runs at **10–20 Hz**
- Each cycle:
  1. Read odometry
  2. Read LiDAR
  3. Compute decision
  4. Publish velocity command

---

## Characteristics of This Navigation Method

### Advantages
- No IMU required
- No map required
- Robust for demos
- Handles dynamic obstacles
- Easy to debug and tune

### Limitations
- Accumulates odometry drift over long distances
- Not suitable for large-scale environments
- No global optimal path planning

---

## Engineering Summary

> Navigation is implemented as a reactive controller that steers toward an odometry-based goal while locally avoiding obstacles using LiDAR sector analysis.

---

End of document.

