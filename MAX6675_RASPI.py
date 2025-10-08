import spidev
import RPi.GPIO as GPIO
import time
import requests
import json  # ✅ for proper JSON encoding

# ==== CONFIGURATION ====
CS_PINS = {
    'pompaA': 15,  # Chip Select for sensor A
    'pompaB': 19,  # Chip Select for sensor B
    'pompaC': 11,  # Chip Select for sensor C
    'pompaD': 37   # Chip Select for sensor D
}

GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/*********/exec"

# ==== SETUP ====
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

for cs in CS_PINS.values():
    GPIO.setup(cs, GPIO.OUT)
    GPIO.output(cs, GPIO.HIGH)

spi = spidev.SpiDev()
spi.open(0, 0)             # Use SPI bus 0, device 0
spi.max_speed_hz = 500000  # MAX6675 safe limit

# ==== FUNCTIONS ====
def read_temp(cs_pin):
    GPIO.output(cs_pin, GPIO.LOW)
    time.sleep(0.001)
    raw = spi.readbytes(2)
    value = (raw[0] << 8) | raw[1]
    GPIO.output(cs_pin, GPIO.HIGH)

    if value & 0x4:  # No thermocouple connected
        return None

    temp_c = (value >> 3) * 0.25
    return temp_c

def send_to_google(data_dict):
    try:
        json_data = json.dumps(data_dict)
        params = {"data": json_data}
        response = requests.get(GOOGLE_SCRIPT_URL, params=params)
        print(f"Sent all data --> {response.text}")
    except Exception as e:
        print(f"Error sending data: {e}")

# ==== MAIN LOOP ====
try:
    while True:
        readings = {}  
        for sensor_id, cs_pin in CS_PINS.items():
            raw_temp = read_temp(cs_pin)
            if raw_temp is not None and raw_temp != 0:
                
                readings[sensor_id] = round(F_temp, 2)
                print(f"{sensor_id}: {F_temp:.2f} °C")
            else:
                print(f"{sensor_id}: Thermocouple not connected")
                readings[sensor_id] = None
        print("-" * 40)
        send_to_google(readings)
        time.sleep(300)

except KeyboardInterrupt:
    print("Exiting...")

finally:
    spi.close()
    GPIO.cleanup()
