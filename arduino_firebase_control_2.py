import serial
import time
import firebase_admin
from firebase_admin import credentials, db
import serial.tools.list_ports
import streamlit as st

# دالة لاكتشاف المنفذ الذي يتصل به الـ Arduino تلقائيًا
def get_arduino_port():
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        if "Arduino" in port.description or "USB" in port.description:
            return port.device
    return None  # إذا لم يتم العثور على Arduino

# إعداد الاتصال بالـ Arduino باستخدام المنفذ المكتشف
arduino_port = get_arduino_port()
if arduino_port:
    arduino = serial.Serial(arduino_port, 9600)  # الاتصال بالـ Arduino باستخدام المنفذ المكتشف
    time.sleep(2)  # انتظار لتثبيت الاتصال
    arduino_status = f"Arduino is connected on {arduino_port}"
else:
    arduino_status = "No Arduino device found. Please connect an Arduino."
    arduino = None

# إعداد Firebase
cred = credentials.Certificate(r"E:\2024_AUC_ECE_material\mea\projects\control\iot-arduino-control-firebase-adminsdk-by0lr-8c52e1a1f3.json") # ضع المسار الصحيح لملف JSON
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://iot-arduino-control-default-rtdb.europe-west1.firebasedatabase.app/commands'  # ضع رابط قاعدة بيانات Firebase
})

# مسارات قاعدة البيانات
commands_ref = db.reference('commands')
response_ref = db.reference('response')

# دالة لإرسال أوامر إلى Arduino
def send_command(command):
    arduino.write(command.encode())  # إرسال الأمر كـ byte
    time.sleep(1)  # انتظار لإتاحة الوقت للرد

# دالة لاستلام البيانات من Arduino
def read_from_arduino():
    for _ in range(5):  # محاولة قراءة البيانات 5 مرات
        if arduino.in_waiting > 0:  # التحقق من وجود بيانات
            data = arduino.readline().decode().strip()
            return data
        time.sleep(0.1)  # تأخير قصير قبل المحاولة مرة أخرى
    return None  # إذا لم توجد بيانات بعد 5 محاولات

# حفظ آخر أمر تم تنفيذه
last_executed_command = None

# Streamlit UI
st.title("Arduino LED and Temperature Control via Firebase")

# مشروع التحكم عن بعد باستخدام Arduino و Firebase
st.markdown("""
This project demonstrates controlling an Arduino device remotely using Firebase.
You can send commands like turning on/off an LED or reading the temperature from a sensor connected to the Arduino.

The system continuously listens for commands from Firebase and executes them on the connected Arduino device.
""")

# عرض حالة الاتصال بالـ Arduino
st.subheader("Arduino Connection Status")
st.write(arduino_status)

# عرض الأوامر المتاحة للمستخدم
st.subheader("Available Commands:")
st.write("""
- **Turn LED ON**: Turns on the LED connected to the Arduino.
- **Turn LED OFF**: Turns off the LED connected to the Arduino.
- **Read Temperature**: Reads the temperature from a sensor connected to the Arduino.
""")

# Command Selection
command = st.radio("Select a command to send:", ["None", "Read Temperature", "Turn LED ON", "Turn LED OFF"])

# إرسال الأمر عند الضغط على زر
if st.button("Send Command"):
    if arduino:
        if command == "Read Temperature":
            commands_ref.set({"command": "temp"})
            send_command('T')  # إرسال طلب قراءة درجة الحرارة
            temperature = read_from_arduino()  # قراءة درجة الحرارة من Arduino
            if temperature:
                try:
                    temperature = float(temperature)  # محاولة تحويل البيانات إلى قيمة عددية
                    response_ref.update({'temp': f"Current Temperature: {temperature}°C"})
                    st.success(f"Temperature: {temperature}°C")
                except ValueError:
                    response_ref.update({'temp': "Error: Invalid temperature data"})
                    st.error("Invalid temperature data received.")
            else:
                response_ref.update({'temp': "Error reading temperature"})
                st.error("Failed to read temperature.")

        elif command == "Turn LED ON":
            if last_executed_command != 'on':  # إذا لم يكن الـ LED بالفعل مُشغل
                send_command('1')  # تشغيل LED
                response_ref.update({'led': "LED is ON"})
                st.success("LED is now ON.")
                last_executed_command = 'on'

        elif command == "Turn LED OFF":
            if last_executed_command != 'off':  # إذا لم يكن الـ LED بالفعل مُطفأ
                send_command('0')  # إطفاء LED
                response_ref.update({'led': "LED is OFF"})
                st.success("LED is now OFF.")
                last_executed_command = 'off'

        else:
            st.warning("No command selected.")

    else:
        st.error("Arduino is not connected. Please connect the Arduino device.")

# Display Firebase Responses
st.subheader("Firebase Responses")
response_data = response_ref.get()
if response_data:
    st.json(response_data)
else:
    st.write("No responses from Firebase yet.")

# Add some details about the project (instructions and explanation)
st.markdown("""
### How It Works
1. **Connect your Arduino** to the computer via USB.
2. **Run the script**, and it will automatically detect the Arduino COM port.
3. **Send commands** via the radio buttons and click "Send Command" to control the Arduino.
4. **Firebase** stores the command states and responses, so you can control the Arduino remotely.
""")
