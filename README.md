# Arduino Joystick Controller & Mouse Steering

A DIY experiment in turning cheap hardware into a game controller: **steer with the mouse** and use an **Arduino joystick module as throttle and brake**. Both inputs are merged into a single virtual gamepad through the **vJoy** driver, so any game that supports controllers can use it (tested with *F1 24*).

It is not meant to replace a real wheel or gamepad. It was built to explore serial communication with an Arduino, virtual HID devices on Windows, and how to make raw mouse input feel like a steering wheel (smoothing and self-centering).

## How it works

```
HW-504 joystick ──analog──▶ Arduino ──serial (0-1023)──┐
                                                      ├──▶ sim_controller.py ──▶ vJoy device ──▶ game
Mouse position ───────────────────────────────────────┘        (Tkinter GUI for live tuning)
```

| vJoy axis | Input | Mapping |
|---|---|---|
| **X** | Mouse horizontal position | Screen center = wheel center, scaled by sensitivity |
| **Z** | Joystick pushed forward | Throttle, 0 to 100% |
| **RZ** | Joystick pulled back | Brake, 0 to 100% |

- **Smoothing**: while the mouse moves, the wheel eases toward the mouse position instead of jumping to it.
- **Pushback**: when the mouse stops, the wheel gradually returns to center, like a real wheel's self-centering force.
- **Deadzone**: small joystick movements around its rest position are ignored so neither pedal is pressed by accident.
- The script always uses the **newest** Arduino reading and discards older queued ones, so the pedals never lag behind.

## Hardware

- Any Arduino with an analog input (Uno, Nano, ...)
- HW-504 (or similar) analog joystick module

| Joystick pin | Arduino pin |
|---|---|
| VRy | A1 |
| +5V | 5V |
| GND | GND |

## Setup (Windows)

1. **Install [vJoy](https://github.com/jshafer817/vJoy/releases)**, open *Configure vJoy* and enable device 1 with the **X**, **Z** and **Rz** axes.
2. **Flash the Arduino** with [`arduino/joystick_throttle/joystick_throttle.ino`](arduino/joystick_throttle/joystick_throttle.ino) using the Arduino IDE, and note its COM port.
3. **Install the Python dependencies** (Python 3.8+):
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the controller** with your Arduino's port:
   ```bash
   python sim_controller.py --port COM6
   ```
5. **Bind the axes in your game**: steering to X, throttle to Z and brake to Rz.

Options: `--port` (default `COM6`), `--baud` (default `9600`), `--device` vJoy device id (default `1`).

## Tuning

A small settings window opens with three live sliders:

| Slider | Effect |
|---|---|
| Steering Sensitivity | How much of the screen width maps to a full wheel turn |
| Pushback Strength | How fast the wheel re-centers when the mouse stops |
| Smoothing | How quickly the wheel follows the mouse |

Closing the window stops the controller and resets all axes to neutral.

## Alternative: AutoHotkey steering script

[`ahk/mouse_steering.ahk`](ahk/mouse_steering.ahk) is a lightweight, steering-only version written in **AutoHotkey v2**. It maps the mouse position straight to the vJoy X axis, without smoothing, pushback or the Arduino.

It calls the vJoy driver directly, so copy `vJoyInterface.dll` from the vJoy install folder (e.g. `C:\Program Files\vJoy\x64\`) next to the script before running it.

## Project structure

```
├── sim_controller.py                           # Main app: mouse + Arduino -> vJoy, with tuning GUI
├── arduino/joystick_throttle/joystick_throttle.ino   # Arduino sketch streaming the joystick axis
├── ahk/mouse_steering.ahk                      # Minimal AutoHotkey v2 steering alternative
└── requirements.txt
```

## Troubleshooting

- **"Failed to initialize vJoy device"**: vJoy is not installed, or device 1 is not enabled in *Configure vJoy*.
- **"Failed to connect to Arduino"**: wrong `--port`, or the port is busy (close the Arduino IDE Serial Monitor).
- **Throttle or brake engaged at rest**: your joystick's rest value may differ from 517. Check it in the Serial Monitor and adjust `JOYSTICK_REST`, `THROTTLE_ZONE_START` and `BRAKE_ZONE_END` in `sim_controller.py`.

## Acknowledgments

- [vJoy](https://github.com/jshafer817/vJoy) virtual joystick driver and [pyvjoy](https://github.com/tidzo/pyvjoy)

## License

[MIT](LICENSE)
