import machine
import time
from car import car
from mpu6050 import mpu

def print_avel():
    while True:
        avel = mpu.get_avel()
        print(f"Gx: {avel[0]}, Gy: {avel[1]}, Gz: {avel[2]}")
        time.sleep(0.25)

def print_tilt():
    while True:
        roll, pitch = mpu.get_tilt()
        print(f"Pitch: {pitch}, Roll: {roll}")
        time.sleep(0.25)

