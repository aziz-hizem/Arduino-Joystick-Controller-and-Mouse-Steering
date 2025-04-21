# Racing Simulator Controller

A custom racing simulator controller that combines mouse steering with an Arduino-based throttle/brake pedal system using the joystick module.

## Features

- Mouse-based steering with customizable settings
- Arduino-powered throttle and brake control using joystick module
- Graphical interface for adjusting steering parameters
- Smooth steering with pushback and center-return mechanics
- Real-time control adjustments
- Compatible with vJoy virtual controller

## Components Required

- Arduino board (with analog input capability)
- Joystick module for throttle/brake
- vJoy installed and configured (one controller with X, Z, RZ axis enabled)

## Software Requirements

- Python 3.x
- vJoy
- Required Python packages:
  - pyserial
  - pyvjoy
  - pyautogui
  - tkinter (usually comes with Python)

## Installation

1. Install vJoy driver on your Windows system
2. Connect the Arduino and upload the `joystick_throttle.ino` sketch (default port is COM6)
3. Install required Python packages:
```bash
pip install pyserial pyvjoy pyautogui
```	
4. Configure the Arduino COM port in Sim_controller.py (default is COM6)


## Usage
1. Run the Python controller script:
```bash
python Sim_controller.py
 ```

2. The GUI will appear with three adjustable settings:
   
   - Steering Sensitivity: Adjusts how much the mouse movement affects steering
   - Pushback Strength: Controls how strongly the wheel returns to center
   - Smoothing: Adjusts the smoothness of steering movements


3. Use your mouse for steering and the Arduino-connected potentiometer for throttle/brake control after configuring in game controls (tested with F1 24)


## Controls
- Steering : Move your mouse left/right
- Throttle : Move potentiometer forward from center
- Brake : Move potentiometer backward from center
- Settings : Adjust in real-time using the GUI sliders
## Project Structure
- Sim_controller.py : Main Python script for the controller
- joystick_throttle.ino : Arduino code for throttle/brake input
- vJoyInterface.dll : Required vJoy interface library


## Acknowledgments
- vJoy project for the virtual joystick driver
- Arduino community for hardware interfacing resources
