from pymavlink import mavutil
import datetime
from Objects import Drone, log_save
import time
import os
import json

# Ekler
ERROR_MODE = "LAND"
INTERRUPT_MODE = "RTL"
SERVO_PIN = 17
ucus_date_time = time.strftime("%d-%m-%Y|%H:%M", time.localtime())
dosya_yolu = "data.txt"

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


def is_true(data: json):
    if data.keys() == {"lat", "lon", "alt"}:
        return True


data = ""

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

	lt = datetime.datetime.now()
	print("Veri bekleniyor...")
	while data == "":
		dosya_time = datetime.datetime.now()
		dosya_time2 = dosya_time + datetime.timedelta(minutes=1)
		dosya_time = dosya_time.strftime("%H:%M")
		dosya_time2 = dosya_time2.strftime("%H:%M")

		if datetime.datetime.now() - lt > datetime.timedelta(seconds=5):
			print("Veri bekleniyor...")
			lt = datetime.datetime.now()
		time.sleep(1)
		

		with open(dosya_yolu, "r") as dosya:
			veri = dosya.read().strip()
			if dosya_time in veri or dosya_time2 in veri:
				data = json.loads(veri.split(">>")[1])
				if is_true(data):
					print("Veri alındı:", data)
					log_save(f">>Veri alındı: {data}", log_file)
					with open(dosya_yolu, "w+") as dosya:
						dosya.write("")
						print("Dosya temizlendi")
						log_save(f">>Dosya temizlendi", log_file)
				else:
					print("Veri eksik veya hatalı: ", data, "Tekrar bekleniyor...")
					log_save(f">>Veri eksik veya hatalı: {data}", log_file)
					data = ""
		

	if is_true(data):
		drone.change_mode("GUIDED", inuse_drone_id)
		log_save(f">>Drone GUIDED moda alındı", log_file)
		print("Drone GUIDED moda alındı")
		time.sleep(2)
		log_save(f">>Drone alınan konuma gidiyor", log_file)
		log_save(f"Drone alınan konum: {data}\nDrone mevcut konumu: {drone.get_location(inuse_drone_id)}", log_file)
		print(f"Drone alınan {data} konumuna gidiyor...")
		drone.go_to(data['lat'], data['lon'], data['alt'], inuse_drone_id)
		print(f"Drone alınan {drone.get_location(inuse_drone_id)} konumuna ulaştı.")
		log_save(f">>Drone alınan konuma ulaştı: {drone.get_location(inuse_drone_id)}", log_file)

		time.sleep(2)
		log_save(f">>Drone görevi tamamlamak için servoyu açıyor", log_file)
		print("Alçalıyor...")
		drone.go_to(drone.get_location(inuse_drone_id)["lat"], drone.get_location(inuse_drone_id)['lon'], drone.get_location(inuse_drone_id)['alt'] - 2, inuse_drone_id)
		time.sleep(1)
		print("Servo açılıyor...")
		drone.open_servo(SERVO_PIN)
		log_save(f">>Servo açıldı {drone.get_location(inuse_drone_id)} konumuna bırakıldı", log_file)
		
		time.sleep(2)
		print("Drone görevi tamamladı RTL alınıyor...")
		log_save(f">>Drone görevi tamamlandı RTL alınıyor", log_file)

		drone.change_mode("RTL", inuse_drone_id)


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