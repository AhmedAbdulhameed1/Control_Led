import streamlit as st
import serial
import serial.tools.list_ports
import time
import firebase_admin
from firebase_admin import credentials, db
import json

# Initialize Firebase
firebase_creds = json.loads(st.secrets["firebase"]["FIREBASE_CREDS"])
FIREBASE_DB_URL = 'https://iot-arduino-control-default-rtdb.europe-west1.firebasedatabase.app/'

if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_creds)
    firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DB_URL})

# # Detect Arduino COM port dynamically
# def get_arduino_port():
#     ports = list(serial.tools.list_ports.comports())
#     st.write("Available Ports:", ports)  # Log the available ports
#     for port in ports:
#         if "Arduino" in port.description:
#             return port.device
#     return None


# arduino_port = get_arduino_port()
# arduino = None
# if arduino_port:
#     try:
#         arduino = serial.Serial(arduino_port, 9600)
#         time.sleep(2)  # Wait for the connection to stabilize
#     except serial.SerialException:
#         st.error("Could not connect to Arduino. Please check the port.")
# else:
#     st.error("No Arduino device found. Please connect an Arduino.")
# إعداد الاتصال بالـ Arduino
arduino = serial.Serial('COM5', 9600)  # تأكد من تغيير COM3 إلى المنفذ الصحيح
time.sleep(2)  # انتظار لتثبيت الاتصال

# Firebase database references
commands_ref = db.reference('commands')
response_ref = db.reference('response')

# Helper functions
def send_command_to_arduino(command):
    if arduino:
        arduino.write(command.encode())
        time.sleep(1)

def read_from_arduino():
    if arduino:
        for _ in range(5):
            if arduino.in_waiting > 0:
                return arduino.readline().decode().strip()
            time.sleep(0.1)
    return None

# Streamlit UI
st.title("Arduino LED and Sensor Control")
st.write("Control your Arduino-connected devices via Firebase.")

# Command Selection
command = st.radio("Select a command to send:", ["None", "Read Temperature", "Turn LED ON", "Turn LED OFF"])

if st.button("Send Command"):
    if command == "Read Temperature":
        commands_ref.set({"command": "temp"})
        send_command_to_arduino('T')
        temperature = read_from_arduino()
        if temperature:
            try:
                temp_value = float(temperature)
                response_ref.update({"temp": f"Current Temperature: {temp_value}°C"})
                st.success(f"Temperature: {temp_value}°C")
            except ValueError:
                response_ref.update({"temp": "Error: Invalid temperature data"})
                st.error("Invalid temperature data received.")
        else:
            response_ref.update({"temp": "Error reading temperature"})
            st.error("Failed to read temperature.")

    elif command == "Turn LED ON":
        commands_ref.set({"command": "on"})
        send_command_to_arduino('1')
        response_ref.update({"led": "LED is ON"})
        st.success("LED is now ON.")

    elif command == "Turn LED OFF":
        commands_ref.set({"command": "off"})
        send_command_to_arduino('0')
        response_ref.update({"led": "LED is OFF"})
        st.success("LED is now OFF.")

    else:
        st.warning("No command selected.")

# Display Firebase Responses
st.subheader("Firebase Responses")
response_data = response_ref.get()
if response_data:
    st.json(response_data)
else:
    st.write("No responses from Firebase yet.")
