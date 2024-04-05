import datetime, time, json





def is_true(data: json):
    if data.keys() == {"lat", "lon", "alt"}:
        return True


dosya_yolu = "data.txt"

data = ""

print("Veri bekleniyor...")
lt = datetime.datetime.now()


while data == "":
    if datetime.datetime.now() - lt > datetime.timedelta(seconds=5):
        print("Veri bekleniyor...")

    dosya_time = datetime.datetime.now()
    dosya_time2 = dosya_time + datetime.timedelta(minutes=1)
    dosya_time = dosya_time.strftime("%H:%M")
    dosya_time2 = dosya_time2.strftime("%H:%M")

    with open(dosya_yolu, "r") as dosya:
        veri = dosya.read().strip()
        if dosya_time in veri or dosya_time2 in veri:
            data = json.loads(veri.split(">>")[1])
            if is_true(data):
                print("Veri alındı:", data)
                with open(dosya_yolu, "w+") as dosya:
                    dosya.write("")
                    print("Dosya temizlendi")
            else:
                print("Veri eksik veya hatalı: ", data, "Tekrar bekleniyor...")
                data = ""
    
   

    time.sleep(1)
		