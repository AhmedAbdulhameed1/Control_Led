import serial
import time
import firebase_admin
from firebase_admin import credentials, db
import serial.tools.list_ports

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
    print(f"Arduino is connected on {arduino_port}")
else:
    print("No Arduino device found.")
    exit(1)  # الخروج إذا لم يتم العثور على Arduino

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

# تشغيل حلقة الاستماع للأوامر
while True:
    # قراءة الأمر الحالي من Firebase
    command_data = commands_ref.get()
    if command_data:
        command = command_data.get('command')
        
        if command and command != last_executed_command:
            if command.lower() == 'temp':  # أمر قراءة درجة الحرارة
                send_command('T')  # إرسال طلب قراءة درجة الحرارة
                temperature = read_from_arduino()  # قراءة درجة الحرارة من Arduino
                if temperature:
                    try:
                        temperature = float(temperature)  # محاولة تحويل البيانات إلى قيمة عددية
                        response_ref.update({'temp': f"Current Temperature: {temperature}°C"})
                    except ValueError:
                        response_ref.update({'temp': "Error: Invalid temperature data"})
                else:
                    response_ref.update({'temp': "Error reading temperature"})
                last_executed_command = 'temp'

            elif command.lower() == 'on':  # أمر تشغيل الـ LED
                if last_executed_command != 'on':  # إذا لم يكن الـ LED بالفعل مُشغل
                    send_command('1')  # تشغيل LED
                    response_ref.update({'led': "LED is ON"})
                    last_executed_command = 'on'

            elif command.lower() == 'off':  # أمر إطفاء الـ LED
                if last_executed_command != 'off':  # إذا لم يكن الـ LED بالفعل مُطفأ
                    send_command('0')  # إطفاء LED
                    response_ref.update({'led': "LED is OFF"})
                    last_executed_command = 'off'

            else:  # أمر غير معروف
                response_ref.update({'error': "Error: Unknown command. Please send 'temp', 'on', or 'off'."})
                last_executed_command = command

    time.sleep(1)  # تأخير بسيط قبل التحقق من الأوامر مجددًا
