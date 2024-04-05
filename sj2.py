from pymavlink import mavutil
import datetime
from Objects import Drone, log_save
import time
import os
import json

#----------
KONUM_LAN = 39.925533
KONUM_LAT = 32.866287


# Ekler
ERROR_MODE = "LAND"
INTERRUPT_MODE = "RTL"
SERVO_PIN = 17
ucus_date_time = time.strftime("%d-%m-%Y|%H:%M", time.localtime())

# Drone baglantisi
address = "/dev/ttyACM0"
baud = 57600
inuse_drone_id = 1
drone_ids = [1]

# Loglari ayarlama
ucus_date_time = time.strftime("%d-%m-%Y(%H:%M)", time.localtime())

karakutu = os.path.join(os.getcwd(), "blackbox")
None if os.path.exists(karakutu) else os.mkdir(karakutu)
logs = os.path.join(karakutu, ucus_date_time.split("(")[0])
None if os.path.exists(logs) else os.mkdir(logs)

errors_path = os.path.join(logs, "hatalar")
None if os.path.exists(errors_path) else os.mkdir(errors_path)
logs_path = os.path.join(logs, "loglar")
None if os.path.exists(logs_path) else os.mkdir(logs_path)

error_log_path = os.path.join(errors_path, f"error-{ucus_date_time}.log")
log_path = os.path.join(logs_path, f"ucus-{ucus_date_time}.log")

a = 1
while os.path.exists(error_log_path):
	error_log_path = error_log_path.split(".log")[0] + f"({a}).log"
	a += 1
a = 1
while os.path.exists(log_path):
	log_path = log_path.split(".log")[0] + f"({a}).log"
	a += 1
log_file = open(log_path, "w+")
error_file = open(error_log_path, "w+")


# ---------------KODLAR----------------


try:
	log_file.write(f"Uçuş başladı {time.strftime("%H:%M:%S", time.localtime())}\n")
	vehicle = mavutil.mavlink_connection(address , baud=baud, autoreconnect=True)
	print("Drone bağlantısı kuruldu.")
	vehicle.wait_heartbeat()
	print("Bağlantı sağlandı.")
	drone = Drone(vehicle)
	log_save(f">>Drone bağlantısı kuruldu", log_file)

	drone_ids = drone.get_all_drone_ids()
	log_save(f">>Ucustaki drone_idler\n{drone_ids}", log_file)

	log_save(f">>Drone {inuse_drone_id} Kalkis konumu {drone.get_location(inuse_drone_id)}", log_file)

	while abs(drone.get_location(inuse_drone_id)["lan"] - KONUM_LAN) > 0.0001 and abs(drone.get_location(inuse_drone_id)["lat"] - KONUM_LAT) > 0.0001:
		print("Drone otonom ucusa devam ediyor...")
		log_save(f">>Drone otonom ucusa devam ediyor", log_file)
		time.sleep(1)
	print("Drone konuma ulaştı", drone.get_location(inuse_drone_id))
	log_save(f">>Drone konuma ulaştı {drone.get_location(inuse_drone_id)}", log_file)


except Exception as e:
	print(f"HATA OLUŞTU DRONELAR {ERROR_MODE} ALIYOR")
	log_save(f">>Hata oluştu uçuş sonlandırıldı {INTERRUPT_MODE} moduna alındı", log_file)
	log_save(f">>Hata dosyası: {error_log_path}", log_file)
	drone.safety_mode(ERROR_MODE, drone_ids)
	error_file.write(e)
	print(f"Oluşan hata log'lara yazıldı:\n{error_log_path}")

except KeyboardInterrupt:
	print(f"Klavyeden çıkış yapıldı dronelar {INTERRUPT_MODE} moduna alınıyor")
	log_save(f">>Klavyeden ucus sonlandırıldı {INTERRUPT_MODE} moduna alındı", log_file)
	drone.safety_mode(INTERRUPT_MODE, drone_ids)

log_file.write(f"Uçuş tamamlandı {time.strftime("%H:%M:%S", time.localtime())}\n")
print(f"Uçuş logları kaydedildi:\n{log_path}")
log_file.close()
error_file.close()


# Loglara eklenilcekler:
#	- Uçuş başlangıç ve bitiş zamanı
#	- Ateşin algılandığı konumlar