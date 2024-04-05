import requests
import time

ip = "127.0.0.1"
req = requests.get(ip)
dosya_time = time.strftime("%H:%M", time.localtime())

file = open("data.txt", "w+")

js = req.json()
file.write(f"{dosya_time}>>{js}")
file.close()