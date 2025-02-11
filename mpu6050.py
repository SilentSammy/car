from machine import Pin, I2C
import ustruct
import time
import math
import os

class MPU6050:
    def __init__(self, i2c, addr=0x68):
        self.i2c = i2c
        self.addr = addr
        self.i2c.writeto_mem(self.addr, 0x6B, b'\x00')  # Wake up MPU6050

        # Load gyro offsets from file if available
        self.gyro_offsets = self.load_gyro_offsets()

    def load_gyro_offsets(self):
        """ Load gyroscope offsets from 'gyro.txt', or default to (0,0,0) if file is missing """
        try:
            with open("gyro.txt", "r") as f:
                offsets = [int(line.strip()) for line in f.readlines()]
                print("Gyro offsets loaded:", offsets)
                return offsets
        except (OSError, ValueError):
            print("No gyro calibration file found. Using default offsets.")
            return [0, 0, 0]  # Default to no offset

    def calibrate_gyro(self, samples=100):
        """ Manually run this function to calibrate the gyroscope and save offsets """
        print("Calibrating gyroscope... Keep sensor still.")
        Gx_offset, Gy_offset, Gz_offset = 0, 0, 0

        for _ in range(samples):
            Gx, Gy, Gz = self.read_gyro_raw()  # Read raw values
            Gx_offset += Gx
            Gy_offset += Gy
            Gz_offset += Gz
            time.sleep(0.01)  # Small delay to ensure stable readings

        # Compute the average offsets
        Gx_offset //= samples
        Gy_offset //= samples
        Gz_offset //= samples

        # Update the instance variable to take effect immediately
        self.gyro_offsets = [Gx_offset, Gy_offset, Gz_offset]

        # Save offsets to a file
        with open("gyro.txt", "w") as f:
            f.write(f"{Gx_offset}\n{Gy_offset}\n{Gz_offset}\n")

        print("Gyro calibration complete. Offsets saved and applied:", self.gyro_offsets)

    def read_accel_raw(self):
        """ Read raw accelerometer values (no calibration) """
        raw = self.i2c.readfrom_mem(self.addr, 0x3B, 6)
        return ustruct.unpack(">hhh", raw)  # Returns (Ax, Ay, Az) raw values

    def read_gyro_raw(self):
        """ Read raw gyroscope values (without offsets) """
        raw = self.i2c.readfrom_mem(self.addr, 0x43, 6)
        return ustruct.unpack(">hhh", raw)  # Returns (Gx, Gy, Gz) raw values

    def read_gyro(self):
        """ Read gyroscope values with applied offsets """
        Gx, Gy, Gz = self.read_gyro_raw()
        Gx -= self.gyro_offsets[0]
        Gy -= self.gyro_offsets[1]
        Gz -= self.gyro_offsets[2]
        return Gx, Gy, Gz  # Returns calibrated values

    def get_tilt_raw(self):
        """ Compute roll and pitch angles in degrees from raw accelerometer values """
        Ax, Ay, Az = self.read_accel_raw()
        roll = math.atan2(Ax, math.sqrt(Ay**2 + Az**2)) * (180 / math.pi)
        pitch = math.atan2(Ay, math.sqrt(Ax**2 + Az**2)) * (180 / math.pi)
        return round(roll, 2), round(pitch, 2)

mpu = MPU6050(I2C(scl=Pin(16), sda=Pin(2)))