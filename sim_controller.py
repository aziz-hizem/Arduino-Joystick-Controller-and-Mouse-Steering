"""Mouse steering + Arduino joystick throttle/brake, fed to a vJoy virtual controller."""
import argparse
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk

import pyautogui
import pyvjoy
import serial

# vJoy axes accept values from 0x0000 to 0x8000
AXIS_MIN = 0
AXIS_MAX = 0x8000
CENTER = AXIS_MAX // 2

# Arduino analog reading (0-1023) of the joystick's vertical axis
JOYSTICK_REST = 517
DEADZONE = 20
THROTTLE_ZONE_START = 532
BRAKE_ZONE_END = 492

# Settings (updated live by the GUI sliders)
settings = {
    'sensitivity': 1.0,
    'pushback': 0.01,
    'smoothing': 0.2
}


def map_value(val, in_min, in_max, out_min, out_max):
    return int((val - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)


def clamp(val):
    return max(AXIS_MIN, min(AXIS_MAX, val))


class Controller:
    def __init__(self, vjoy, arduino):
        self.vjoy = vjoy
        self.arduino = arduino
        self.screen_width = pyautogui.size().width
        self.stop_event = threading.Event()

        # Kept as floats so small pushback steps still move the wheel back to center
        self.virtual_wheel_pos = float(CENTER)
        self.physical_wheel_pos = float(CENTER)
        self.last_mouse_x = self.screen_width / 2
        self.last_mouse_move_time = time.time()

    def update_steering(self):
        current_mouse_x = pyautogui.position().x
        if current_mouse_x != self.last_mouse_x:
            self.last_mouse_move_time = time.time()
            self.last_mouse_x = current_mouse_x

            # Convert mouse position to wheel position
            normalized = (current_mouse_x / self.screen_width - 0.5) * 2  # -1 to 1
            target = CENTER + normalized * CENTER * settings['sensitivity']
            self.physical_wheel_pos = clamp(target)

    def apply_pushback(self):
        if time.time() - self.last_mouse_move_time < 0.1:  # Active steering
            # Smooth transition between current position and target
            self.virtual_wheel_pos += (self.physical_wheel_pos - self.virtual_wheel_pos) * settings['smoothing']
        else:  # No recent mouse movement: pull the wheel back to center
            self.virtual_wheel_pos += (CENTER - self.virtual_wheel_pos) * settings['pushback']

        self.virtual_wheel_pos = clamp(self.virtual_wheel_pos)
        self.vjoy.set_axis(pyvjoy.HID_USAGE_X, round(self.virtual_wheel_pos))

    def update_throttle_brake(self, val):
        throttle = 0
        brake = 0
        if abs(val - JOYSTICK_REST) >= DEADZONE:
            if val > THROTTLE_ZONE_START:
                throttle = map_value(val, THROTTLE_ZONE_START, 1023, 0, AXIS_MAX)
            elif val < BRAKE_ZONE_END:
                brake = map_value(val, 0, BRAKE_ZONE_END, AXIS_MAX, 0)

        self.vjoy.set_axis(pyvjoy.HID_USAGE_Z, throttle)
        self.vjoy.set_axis(pyvjoy.HID_USAGE_RZ, brake)

    def read_latest_joystick_value(self):
        """Drain every pending serial line and return only the newest reading.

        The Arduino sends ~100 readings per second; reading one line per loop
        would let the buffer grow and make throttle/brake lag further and further behind.
        """
        latest = None
        while self.arduino.in_waiting:
            line = self.arduino.readline().decode(errors='ignore').strip()
            if line.isdigit():
                latest = int(line)
        return latest

    def reset_axes(self):
        self.vjoy.set_axis(pyvjoy.HID_USAGE_X, CENTER)
        self.vjoy.set_axis(pyvjoy.HID_USAGE_Z, 0)
        self.vjoy.set_axis(pyvjoy.HID_USAGE_RZ, 0)

    def run(self):
        try:
            while not self.stop_event.is_set():
                self.update_steering()

                value = self.read_latest_joystick_value()
                if value is not None:
                    self.update_throttle_brake(value)

                self.apply_pushback()
                time.sleep(0.005)
        except serial.SerialException as e:
            print(f"Lost connection to Arduino: {e}")
        finally:
            self.stop_event.set()


def start_gui(controller, input_thread):
    root = tk.Tk()
    root.title("Steering Settings")
    root.geometry("300x200")
    root.configure(bg="#1c1c1c")

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TLabel", background="#1c1c1c", foreground="white", font=('Helvetica', 10))
    style.configure("TScale", background="#1c1c1c")

    def add_slider(label, key, from_, to):
        ttk.Label(root, text=label).pack(pady=5)
        slider = ttk.Scale(root, from_=from_, to=to, value=settings[key], orient="horizontal",
                           command=lambda value: settings.__setitem__(key, float(value)))
        slider.pack(fill="x", padx=20)

    add_slider("Steering Sensitivity", 'sensitivity', 0.1, 2.0)
    add_slider("Pushback Strength", 'pushback', 0.001, 0.1)
    add_slider("Smoothing", 'smoothing', 0.05, 0.5)

    def on_close():
        controller.stop_event.set()
        input_thread.join(timeout=1)
        root.destroy()

    def watch_input_thread():
        # Close the window if the input loop stopped on its own (e.g. Arduino unplugged)
        if controller.stop_event.is_set():
            on_close()
        else:
            root.after(200, watch_input_thread)

    root.protocol("WM_DELETE_WINDOW", on_close)
    watch_input_thread()
    try:
        root.mainloop()
    except KeyboardInterrupt:
        on_close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', default='COM6', help="Arduino serial port (default: COM6)")
    parser.add_argument('--baud', type=int, default=9600, help="serial baud rate (default: 9600)")
    parser.add_argument('--device', type=int, default=1, help="vJoy device id (default: 1)")
    args = parser.parse_args()

    try:
        vjoy = pyvjoy.VJoyDevice(args.device)
    except Exception as e:
        print(f"Failed to initialize vJoy device {args.device}: {e}")
        print("Is the vJoy driver installed and the device enabled in 'Configure vJoy'?")
        sys.exit(1)

    try:
        arduino = serial.Serial(args.port, args.baud, timeout=0.1)
    except Exception as e:
        print(f"Failed to connect to Arduino on {args.port}: {e}")
        sys.exit(1)

    controller = Controller(vjoy, arduino)
    input_thread = threading.Thread(target=controller.run, daemon=True)
    input_thread.start()

    try:
        # Tkinter must run on the main thread
        start_gui(controller, input_thread)
    finally:
        controller.stop_event.set()
        input_thread.join(timeout=1)
        controller.reset_axes()
        arduino.close()
        print("Exiting...")


if __name__ == "__main__":
    main()
