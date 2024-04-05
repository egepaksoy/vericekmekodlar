from pymavlink import mavutil
import RPi.GPIO as GPIO
from gpiozero import AngularServo
import time

RANGE = 0.00001

class Drone():
	def __init__(self, vehicle: mavutil.mavlink_connection):
		self.vehicle = vehicle
		self.fire_detected = False
		self.fire_detected_drone_id = None

	def is_armed(self, drone_id):
		while True:
			msg = self.vehicle.recv_match(type='HEARTBEAT', blocking=True)
			if msg and msg.get_srcSystem() == drone_id:
				return (msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED) != 0

	def arm(self, drone_id: int = 1, arm: bool = True):
		ret = {}

		if self.is_armed(drone_id) == False:
			self.vehicle.mav.command_long_send(drone_id, self.vehicle.target_component, mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0, int(arm), 0, 0, 0, 0, 0, 0)
			edildi = "edildi" if arm == True else "kapatıldı"
			print(f"{drone_id} numaralı drone arm {edildi}")
			time.sleep(1)
		ret.append({drone_id: self.is_armed(drone_id)})

		return ret

	def get_all_drone_ids(self):
		drone_ids = set()

		start_time = time.time()
		while time.time() - start_time < 10:
			msg = self.vehicle.recv_match(type='HEARTBEAT', blocking=True)
			if msg:
				drone_ids.add(msg.get_srcSystem())

		return list(drone_ids)
	
	def get_mode(self, drone_id: int = 1):
		mode = self.vehicle.get_mode(drone_id)
		return self.vehicle.mode_mapping().get(mode).upper()
	
	def change_mode(self, mode: str, drone_id: int = 1):
		mode = self.vehicle.mode_mapping().get(mode.upper())

		if mode is None:
			raise ValueError(f"Geçersiz mod ismi: {mode}")
		
		if self.fire_detected and drone_id == self.fire_detected_drone_id and mode == "LAND":
			print(f"Ates algilayan drone ates üstünde olduğu için {mode} moduna geçirilemez RTL moduna geçiriliyor")
			self.change_mode("RTL", drone_id)
		
		else:
			self.vehicle.mav.command_long_send(drone_id, self.vehicle.target_component, mavutil.mavlink.MAV_CMD_DO_SET_MODE, 0, drone_id, mode, 0, 0, 0, 0, 0)
			print(f"{drone_id} numaralı drone {mode} moduna geçirildi")
		
		return {drone_id: mode}
	
	def takeoff(self, alt: int, drone_ids: list = [1]):
		self.arm(drone_ids)
		self.change_mode("GUIDED", drone_ids)
		for drone_id in drone_ids:
			self.vehicle.mav.command_long_send(drone_id, self.vehicle.target_component, mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 0, 0, 0, 0, 0, 0, 0, alt)
			drone_location = self.get_location()
			while drone_location['alt'] < alt*0.95:
				drone_location = self.get_location()
				print(f"{drone_id} numaralı drone {drone_location['alt']} metre yükseklikte")
				time.sleep(1)
			print(f"{drone_id} numaralı drone {alt} metre yüksekliğe ulaştı")
		print("Tüm dronelar belirtilen yüksekliğe ulaştı")

		return {drone_id: self.get_location(drone_id)}

	def get_location(self, drone_id: int = 1):
		while True:
			msg = self.vehicle.recv_match(type='GLOBAL_POSITION_INT', blocking=True)
			if msg and msg.get_srcSystem() == drone_id:
				return {
					'lat': msg.lat / 1E7,  # Convert to degrees
					'lon': msg.lon / 1E7,  # Convert to degrees
					'alt': msg.alt / 1E3   # Convert to meters
				}
	
	
	def go_to(self, lat: float, lon: float, alt: float, drone_id: int = 1):
		if self.get_mode(drone_id) != "GUIDED":
			self.change_mode("GUIDED", drone_id)
			print(f"{drone_id} numaralı drone GUIDED modunda değil komut iptal edildi")
		else:
			self.vehicle.mav.command_long_send(drone_id, self.vehicle.target_component, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, 0, lat, lon, alt)
			print(f"{drone_id} numaralı drone ({lat}, {lon}, {alt}) konumuna gidiyor")
			drone_location = self.get_location()
			while abs(drone_location['lat'] - lat) <= RANGE and abs(drone_location['lon'] - lon) <= RANGE and abs(drone_location['alt'] - alt) <= 0.95:
				drone_location = self.get_location()
				print(f"{drone_id} numaralı drone ({drone_location['lat']}, {drone_location['lon']}, {drone_location['alt']}) konumunda")
				time.sleep(1)
			print(f"{drone_id} numaralı drone ({lat}, {lon}, {alt}) konumuna ulaştı")
			time.sleep(1)

		return {drone_id: self.get_location(drone_id)}
	

	def fire_detected(self, servo_pin):
		self.fire_detected = True
		self.fire_detected_drone_id = self.vehicle.get_srcSystem()
		drone_location = self.get_location()
		print(f"Ateş {self.fire_detected_drone_id} id'li drone tarafından {drone_location} konumunda tespit edildi")
		
		self.go_to(drone_location['lat'], drone_location['lon'], drone_location['alt'] - 2)
		
		print("Servo açılıyor...")
		servo = AngularServo(servo_pin, min_pulse_width=0.0006, max_pulse_width=0.0023)
		servo.value = -1
		time.sleep(4)

		print("Yangın söndürme başarılı drone eski yüksekliğine çıkıyor...")

		self.go_to(drone_location['lat'], drone_location['lon'], drone_location['alt'])
		print("Drone eski konumuna ulaştı RTL alınıyor")
		self.change_mode("RTL")

		return [self.fire_detected_drone_id, drone_location, drone_location['alt'] - 2]

	def open_servo(self, servo_pin):
		servo = AngularServo(servo_pin, min_pulse_width=0.0006, max_pulse_width=0.0023)
		servo.value = -1
		time.sleep(4)
		print("Servo açıldı")



	def safety_mode(self, mode: str, drone_ids: list = [1]):
		for drone_id in drone_ids:
			self.change_mode(mode, drone_id)
			time.sleep(1)
		print(f"Tüm dronelar {mode} moduna alındı")








	#? Bu değerler donusturulmeden ne anlama geliyor?
	def msg_locations(self):
		while True:
			msg = self.vehicle.recv_match(type='GLOBAL_POSITION_INT', blocking=True)
			if msg:
				return {
					'lat': msg.lat,
					'lon': msg.lon,
					'alt': msg.alt
				}


def log_save(text, file):
	timestamp = time.strftime("%H:%M:%S", time.localtime())
	if ">>" in text:
		text = str(timestamp) + text
	
	file.write(text + "\n")







# TODO: Drone tarama yapıcak ates konumuna servo acılcak
#? SIDE-QUEST: Sürü halindeki droneların birbirleriyle haberleşmesi
#! 1 metre = 0.00001144032 derece