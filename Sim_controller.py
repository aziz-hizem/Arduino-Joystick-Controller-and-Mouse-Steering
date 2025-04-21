import serial
import pyvjoy
import pyautogui
import time
import sys
import threading
import tkinter as tk
from tkinter import ttk

# Initialize vJoy
try:
    vjoy = pyvjoy.VJoyDevice(1)
except Exception as e:
    print(f"Failed to initialize vJoy device: {e}")
    sys.exit(1)

# Initialize Arduino
try:
    arduino = serial.Serial('COM6', 9600, timeout=1)
except Exception as e:
    print(f"Failed to connect to Arduino: {e}")
    sys.exit(1)

# Screen dimensions
SCREEN_WIDTH = pyautogui.size().width

# Constants
CENTER = int(32768/2)
MAX_STEER = 65535
MIN_STEER = 0
DEADZONE = 20
THROTTLE_ZONE_START = 532
BRAKE_ZONE_END = 492

# Settings
settings = {
    'sensitivity': 1.0,
    'pushback': 0.01,
    'smoothing': 0.2  # Added smoothing factor
}

# State
virtual_wheel_pos = CENTER  
physical_wheel_pos = CENTER  
last_mouse_x = SCREEN_WIDTH / 2
last_mouse_move_time = time.time()

def map_value(val, in_min, in_max, out_min, out_max):
    return int((val - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

def update_steering():
    global physical_wheel_pos, last_mouse_x, last_mouse_move_time
    
    current_mouse_x = pyautogui.position().x
    if current_mouse_x != last_mouse_x:
        last_mouse_move_time = time.time()
        last_mouse_x = current_mouse_x
        
        # Convert mouse position to virtual wheel position
        normalized = (current_mouse_x / SCREEN_WIDTH - 0.5) * 2  # -1 to 1
        target = CENTER + int(normalized * 32768 * settings['sensitivity'])
        physical_wheel_pos = max(MIN_STEER, min(MAX_STEER, target))

def apply_pushback():
    global virtual_wheel_pos, physical_wheel_pos
    
    # Calculate pushback force (stronger when farther from center)
    pushback_force = (CENTER - virtual_wheel_pos) * settings['pushback']
    
    # If mouse is moving, blend physical and pushback positions
    if time.time() - last_mouse_move_time < 0.1:  # Active steering
        # Smooth transition between current position and target
        virtual_wheel_pos += int((physical_wheel_pos - virtual_wheel_pos) * settings['smoothing'])
    else:  # No recent mouse movement - apply pushback
        virtual_wheel_pos += int(pushback_force)
    
    # Clamp to valid range
    virtual_wheel_pos = max(MIN_STEER, min(MAX_STEER, virtual_wheel_pos))
    
    # Update vJoy
    vjoy.set_axis(pyvjoy.HID_USAGE_X, virtual_wheel_pos)

def update_throttle_brake(val):
    if abs(val - 517) < DEADZONE:
        vjoy.set_axis(pyvjoy.HID_USAGE_Z, 0)
        vjoy.set_axis(pyvjoy.HID_USAGE_RZ, 0)
        return

    if val > THROTTLE_ZONE_START:
        throttle = map_value(val, THROTTLE_ZONE_START, 1023, 0, 32767)
        vjoy.set_axis(pyvjoy.HID_USAGE_Z, throttle)
        vjoy.set_axis(pyvjoy.HID_USAGE_RZ, 0)
    elif val < BRAKE_ZONE_END:
        brake = map_value(val, 0, BRAKE_ZONE_END, 32767, 0)
        vjoy.set_axis(pyvjoy.HID_USAGE_Z, 0)
        vjoy.set_axis(pyvjoy.HID_USAGE_RZ, brake)
    else:
        vjoy.set_axis(pyvjoy.HID_USAGE_Z, 0)
        vjoy.set_axis(pyvjoy.HID_USAGE_RZ, 0)

def main_loop():
    try:
        while True:
            update_steering()
            
            # Read Arduino
            line = arduino.readline().decode().strip()
            if line.isdigit():
                update_throttle_brake(int(line))
            
            apply_pushback()
            time.sleep(0.005)

    except KeyboardInterrupt:
        print("\nExiting...")
        vjoy.set_axis(pyvjoy.HID_USAGE_X, CENTER)
        vjoy.set_axis(pyvjoy.HID_USAGE_Z, 0)
        vjoy.set_axis(pyvjoy.HID_USAGE_RZ, 0)
        sys.exit(0)

def start_gui():
    root = tk.Tk()
    root.title("F1 Steering Settings")
    root.geometry("300x200")
    root.configure(bg="#1c1c1c")

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TLabel", background="#1c1c1c", foreground="white", font=('Helvetica', 10))
    style.configure("TScale", background="#1c1c1c")

    ttk.Label(root, text="Steering Sensitivity").pack(pady=5)
    sens_slider = ttk.Scale(root, from_=0.1, to=2.0, value=settings['sensitivity'], orient="horizontal")
    sens_slider.pack(fill="x", padx=20)

    ttk.Label(root, text="Pushback Strength").pack(pady=5)
    push_slider = ttk.Scale(root, from_=0.001, to=0.1, value=settings['pushback'], orient="horizontal")
    push_slider.pack(fill="x", padx=20)

    ttk.Label(root, text="Smoothing").pack(pady=5)
    smooth_slider = ttk.Scale(root, from_=0.05, to=0.5, value=settings['smoothing'], orient="horizontal")
    smooth_slider.pack(fill="x", padx=20)

    def update_settings():
        while True:
            settings['sensitivity'] = sens_slider.get()
            settings['pushback'] = push_slider.get()
            settings['smoothing'] = smooth_slider.get()
            time.sleep(0.1)

    threading.Thread(target=update_settings, daemon=True).start()
    root.mainloop()

# Launch GUI thread
gui_thread = threading.Thread(target=start_gui)
gui_thread.daemon = True
gui_thread.start()

# Launch main input loop
main_loop()