import cv2
import time
import numpy as np
import math
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import handtrackingmodule as htm  # Pastikan file ini ada dan tidak error

################################
wCam, hCam = 640, 480
################################

# Inisialisasi kamera
cap = cv2.VideoCapture(0)  # Gunakan 0 jika hanya ada satu kamera
cap.set(3, wCam)  # Lebar frame
cap.set(4, hCam)  # Tinggi frame

# Cek apakah kamera bisa dibuka
if not cap.isOpened():
    print("Error: Kamera tidak dapat diakses!")
    exit()

pTime = 0

# Inisialisasi detector tangan
detector = htm.handDetector(detectionCon=0.7)

# Inisialisasi kontrol volume
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))

volRange = volume.GetVolumeRange()  # Ambil range volume
minVol = volRange[0]
maxVol = volRange[1]

vol = 0
volBar = 400
volPer = 0

while True:
    success, img = cap.read()
    
    if not success:
        print("Gagal menangkap gambar dari kamera!")
        continue  # Lewati iterasi jika tidak berhasil membaca frame
    
    img = detector.findHands(img)
    lmList = detector.findPosition(img, draw=False)

    if len(lmList) != 0:
        x1, y1 = lmList[4][1], lmList[4][2]   # Posisi ibu jari
        x2, y2 = lmList[8][1], lmList[8][2]   # Posisi jari telunjuk
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2  # Titik tengah antara dua jari

        cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
        cv2.circle(img, (x2, y2), 15, (255, 0, 255), cv2.FILLED)
        cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
        cv2.circle(img, (cx, cy), 15, (255, 0, 255), cv2.FILLED)

        length = math.hypot(x2 - x1, y2 - y1)  # Hitung jarak antara ibu jari dan telunjuk
        
        # Konversi panjang ke skala volume
        vol = np.interp(length, [50, 300], [minVol, maxVol])
        volBar = np.interp(length, [50, 300], [400, 150])
        volPer = np.interp(length, [50, 300], [0, 100])

        # Set volume
        volume.SetMasterVolumeLevel(vol, None)

        if length < 50:
            cv2.circle(img, (cx, cy), 15, (0, 255, 0), cv2.FILLED)  # Jika jari sangat dekat, ubah warna

    # Tampilan bar volume
    cv2.rectangle(img, (50, 150), (85, 400), (255, 0, 0), 3)
    cv2.rectangle(img, (50, int(volBar)), (85, 400), (255, 0, 0), cv2.FILLED)
    cv2.putText(img, f'{int(volPer)} %', (40, 450), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 3)

    # Hitung FPS
    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime
    cv2.putText(img, f'FPS: {int(fps)}', (40, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 3)

    cv2.imshow("Hand Tracking Volume Control", img)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):  # Tekan 'q' untuk keluar
        break

cap.release()
cv2.destroyAllWindows()