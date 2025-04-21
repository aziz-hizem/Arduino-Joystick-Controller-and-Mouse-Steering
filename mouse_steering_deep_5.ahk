#Requires AutoHotkey v2.0
#SingleInstance Force
Persistent

global vJoyDevice := 1
global axisMax := 32767
global axisMin := -32768

; --- vJoy Initialization ---
if !DllCall("LoadLibrary", "Str", "vJoyInterface.dll", "Ptr") {
    MsgBox("vJoyInterface.dll not found!")
    ExitApp
}

if !DllCall("vJoyInterface\AcquireVJD", "UInt", vJoyDevice, "CDecl Int") {
    MsgBox("Failed to acquire vJoy Device " vJoyDevice)
    ExitApp
}

; --- Steering Logic ---
UpdateSteering() {
    global vJoyDevice, axisMin, axisMax
    
    MouseGetPos(&mouseX, &mouseY)
    mouseX := Min(Max(mouseX, 0), A_ScreenWidth)
    
    ; Map mouse to steering axis (-32768 to 32767)
    steerValue := Round((mouseX / A_ScreenWidth) * (axisMax - axisMin) + axisMin)
    vJoySetAxis(steerValue, vJoyDevice, 0x30)  ; 0x30 = X-axis
    
    Tooltip("Steering: " steerValue)
}

vJoySetAxis(axisVal, rID, axisID) {
    global axisMin, axisMax
    normalizedVal := Round((axisVal - axisMin) / (axisMax - axisMin) * 32767)
    DllCall("vJoyInterface\SetAxis", "Int", normalizedVal, "UInt", rID, "UInt", axisID, "CDecl Int")
}

SetTimer(UpdateSteering, 10)