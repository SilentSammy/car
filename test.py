from mpu6050 import mpu
import time

def main():
    while True:
        pitch = 15 * round(mpu.get_pitch() / 15)
        roll = 15 * round(mpu.get_roll() / 15)
        avel = mpu.read_gyro()
        #print(f"Pitch: {pitch}, Roll: {roll}")
        print(f"Gx: {avel[0]}, Gy: {avel[1]}, Gz: {avel[2]}")
        time.sleep(0.25)