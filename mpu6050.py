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

        # Load tilt and gyro offsets
        self.gyro_offsets = self.load_offsets("gyro.txt", 3)
        self.tilt_offsets = self.load_offsets("tilt.txt", 2)

    def load_offsets(self, filename, expected_length):
        """ Load offsets from file if available, else default to zeros """
        try:
            with open(filename, "r") as f:
                offsets = [float(line.strip()) for line in f.readlines()]
                if len(offsets) != expected_length:
                    raise ValueError  # Ensure correct number of values
                print(f"{filename} offsets loaded:", offsets)
                return offsets
        except (OSError, ValueError):
            print(f"No valid {filename} file found. Using default offsets.")
            return [0.0] * expected_length  # Ensure correct length (0,0,0) or (0,0)

    def calibrate_gyro(self, samples=100):
        """ Manually run to calibrate gyroscope and save offsets """
        print("Calibrating gyroscope... Keep sensor still.")
        Gx_offset, Gy_offset, Gz_offset = 0, 0, 0

        for _ in range(samples):
            Gx, Gy, Gz = self.read_gyro_raw()
            Gx_offset += Gx
            Gy_offset += Gy
            Gz_offset += Gz
            time.sleep(0.01)

        # Compute floating-point averages
        Gx_offset /= samples
        Gy_offset /= samples
        Gz_offset /= samples

        self.gyro_offsets = [Gx_offset, Gy_offset, Gz_offset]
        self.save_offsets("gyro.txt", self.gyro_offsets)
        print("Gyro calibration complete:", self.gyro_offsets)

    def calibrate_tilt(self, samples=100):
        """ Manually run to calibrate tilt sensor (zero pitch & roll) and save offsets """
        print("Calibrating tilt... Keep sensor at desired reference orientation.")
        roll_offset, pitch_offset = 0, 0

        for _ in range(samples):
            roll, pitch = self.get_tilt_raw()
            roll_offset += roll
            pitch_offset += pitch
            time.sleep(0.01)

        # Compute floating-point averages
        roll_offset /= samples
        pitch_offset /= samples

        self.tilt_offsets = [roll_offset, pitch_offset]
        self.save_offsets("tilt.txt", self.tilt_offsets)
        print("Tilt calibration complete:", self.tilt_offsets)

    def save_offsets(self, filename, offsets):
        """ Save offsets to a file """
        with open(filename, "w") as f:
            f.write("\n".join(map(str, offsets)) + "\n")

    def read_accel_raw(self):
        """ Read raw accelerometer values (no calibration) """
        raw = self.i2c.readfrom_mem(self.addr, 0x3B, 6)
        return ustruct.unpack(">hhh", raw)  # (Ax, Ay, Az)

    def read_gyro_raw(self):
        """ Read raw gyroscope values (without offsets) """
        raw = self.i2c.readfrom_mem(self.addr, 0x43, 6)
        return ustruct.unpack(">hhh", raw)  # (Gx, Gy, Gz)

    def read_gyro(self):
        """ Read gyroscope values with applied offsets """
        Gx, Gy, Gz = self.read_gyro_raw()
        Gx -= self.gyro_offsets[0]
        Gy -= self.gyro_offsets[1]
        Gz -= self.gyro_offsets[2]
        return Gx, Gy, Gz  # Returns calibrated values

    def get_avel(self):
        """ Get calibrated angular velocity (degrees per second) """
        Gx, Gy, Gz = self.read_gyro()  # Get corrected gyro values
        scale_factor = 131.0  # MPU6050 scale factor for ±250°/s mode

        # Convert raw values to degrees per second (°/s)
        Gx_dps = round(Gx / scale_factor, 2)
        Gy_dps = round(Gy / scale_factor, 2)
        Gz_dps = round(Gz / scale_factor, 2)

        return Gx_dps, Gy_dps, Gz_dps  # Returns angular velocity in °/s

    def get_tilt_raw(self):
        """ Compute raw roll and pitch angles in degrees """
        Ax, Ay, Az = self.read_accel_raw()
        roll = math.atan2(Ax, math.sqrt(Ay**2 + Az**2)) * (180 / math.pi)
        pitch = math.atan2(Ay, math.sqrt(Ax**2 + Az**2)) * (180 / math.pi)
        return round(roll, 2), round(pitch, 2)

    def get_tilt(self):
        """ Get roll and pitch with applied offsets """
        roll, pitch = self.get_tilt_raw()
        roll -= self.tilt_offsets[0]
        pitch -= self.tilt_offsets[1]
        return round(roll, 2), round(pitch, 2)

# Instantiate MPU6050
mpu = MPU6050(I2C(scl=Pin(16), sda=Pin(2)))
