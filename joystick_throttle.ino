const int joystickPin = A1;  // Connect VRy here (vertical axis of HW-504)
int joyValue = 0;

void setup() {
  Serial.begin(9600);
}

void loop() {
  joyValue = analogRead(joystickPin);  // Value from 0 to 1023
  Serial.println(joyValue);
  delay(10);  // Reduce lag, but don't overload serial
}
