# Elevator System

This project is about an elevator control system. Initially, it was designed to move both vertically and horizontally for 12 spots across six floors. Due to structural limitations, the project was simplified to support only vertical movement for one spot and one floor.

## Project Overview

The original idea was to create a system that could handle both vertical and horizontal movements across multiple floors and spots. However, due to the challenges with the physical structure, we had to scale back. We tried a version with a lock mechanism to switch between vertical and horizontal movement, but that approach wasn’t feasible. As a result, the **Final_System_Vertical_Only** was developed, which only supports vertical movement for one spot and one floor.

## Subfolders

- **Elevator_System_6_Motor/**
  - This folder contains the original six-motor setup, designed to handle both vertical and horizontal movements for multiple floors and spots, but simplified later due to the structure limitations.
  - **Elevator_System_6_Motor_Simulation**: A working version using a simulated environment for testing without physical hardware.
  - **Elevator_System_6_Motor_No_Simulation**: A working version intended for testing with physical hardware, excluding simulation components.

- **Elevator_System_Motor_Testing/**: Focuses on testing individual motor functionality before integration into the full system.

- **New_Elevator_System/**: This version explored a lock mechanism to switch between vertical and horizontal movement but was ultimately not feasible.
  - **Mock_Simulator/**: Simulated testing environment for the elevator system, not requiring physical hardware.

- **Final_System_Vertical_Only/**: The final, simplified version of the project, implementing vertical movement for one spot and one floor due to earlier limitations.

## Structure and Files

Each subfolder contains the necessary Arduino code, Python scripts, database configurations, and environment setups for the respective version. The code is modular and can be adjusted if needed.

### Final Remarks

While the project started with more complex operations in mind, the limitations of the physical structure led to a simpler design. The final version still provides a working solution with vertical movement for one spot and one floor, which can be expanded upon in the future.
