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

    # Calibration
    def save_offsets(self, filename, offsets):
        """ Save offsets to a file """
        with open(filename, "w") as f:
            f.write("\n".join(map(str, offsets)) + "\n")

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
            roll, pitch, _ = self.get_tilt_raw()
            roll_offset += roll
            pitch_offset += pitch
            time.sleep(0.01)

        # Compute floating-point averages
        roll_offset /= samples
        pitch_offset /= samples

        self.tilt_offsets = [roll_offset, pitch_offset]
        self.save_offsets("tilt.txt", self.tilt_offsets)
        print("Tilt calibration complete:", self.tilt_offsets)

    # Sensor readings
    def read_accel_raw(self):
        """ Read raw accelerometer values (no calibration) """
        raw = self.i2c.readfrom_mem(self.addr, 0x3B, 6)
        return ustruct.unpack(">hhh", raw)  # (Ax, Ay, Az)

    def read_gyro_raw(self):
        """ Read raw gyroscope values (without offsets) """
        raw = self.i2c.readfrom_mem(self.addr, 0x43, 6)
        return ustruct.unpack(">hhh", raw)  # (Gx, Gy, Gz)

    def read_gyro_x_raw(self):
        """ Read raw gyroscope value for Gx (pitch rate) """
        raw = self.i2c.readfrom_mem(self.addr, 0x43, 2)  # Read 2 bytes for Gx
        Gx, = ustruct.unpack(">h", raw)  # Unpack as a single short integer
        return Gx

    # Processed gyro data
    def get_gyro_calibrated(self):
        """ Read gyroscope values (pitch, roll and yaw) with applied offsets """
        Gx, Gy, Gz = self.read_gyro_raw()
        Gx -= self.gyro_offsets[0] # Pitch
        Gy -= self.gyro_offsets[1] # Roll
        Gz -= self.gyro_offsets[2] # Yaw
        Gt = (Gx ** 2 + Gy ** 2 + Gz ** 2) ** 0.5  # Total angular velocity
        return Gx, Gy, Gz, Gt  # Returns calibrated values
    
    def get_avel(self, samples=1):
        """ Get calibrated angular velocity (degrees per second), optionally averaging over multiple samples """
        total_Gx, total_Gy, total_Gz, total_Gt = 0, 0, 0, 0
        for _ in range(samples):
            Gx, Gy, Gz, Gt = self.get_gyro_calibrated()  # Get corrected gyro values
            total_Gx += Gx
            total_Gy += Gy
            total_Gz += Gz
            total_Gt += Gt

        avg_Gx = total_Gx / samples
        avg_Gy = total_Gy / samples
        avg_Gz = total_Gz / samples
        avg_Gt = total_Gt / samples

        scale_factor = 131.0  # MPU6050 scale factor for ±250°/s mode

        # Convert raw values to degrees per second (°/s)
        Gx_dps = round(avg_Gx / scale_factor, 2)
        Gy_dps = round(avg_Gy / scale_factor, 2)
        Gz_dps = round(avg_Gz / scale_factor, 2)
        Gt_dps = round(avg_Gt / scale_factor, 2)

        return Gx_dps, Gy_dps, Gz_dps, Gt_dps  # Returns angular velocity in °/s

    def get_pitch_rate(self, samples=1):
        """ Get pitch angular velocity (degrees per second), optionally averaging over multiple samples """
        total_Gx = 0
        for _ in range(samples):
            Gx = self.read_gyro_x_raw()  # Get raw Gx value
            Gx -= self.gyro_offsets[0]  # Apply offset
            total_Gx += Gx
        avg_Gx = total_Gx / samples
        scale_factor = 131.0  # MPU6050 scale factor for ±250°/s mode
        pitch_rate = round(avg_Gx / scale_factor, 2)  # Convert to degrees per second
        return pitch_rate

    # Processed accelerometer data
    def get_tilt_raw(self):
        """ Compute raw roll and pitch angles in degrees """
        Ax, Ay, Az = self.read_accel_raw()
        roll = math.atan2(Ax, math.sqrt(Ay**2 + Az**2)) * (180 / math.pi)
        pitch = math.atan2(Ay, math.sqrt(Ax**2 + Az**2)) * (180 / math.pi)
        tilt = (roll ** 2 + pitch ** 2) ** 0.5  # Pythagorean theorem
        return roll, pitch, tilt

    def get_pitch_raw(self):
        """ Compute raw pitch angle in degrees """
        Ax, Ay, Az = self.read_accel_raw()
        pitch = math.atan2(Ay, math.sqrt(Ax**2 + Az**2)) * (180 / math.pi)
        return pitch

    def get_tilt(self, samples=1):
        """ Get roll and pitch with applied offsets, optionally averaging over multiple samples """
        total_roll, total_pitch, total_tilt = 0, 0, 0
        for _ in range(samples):
            roll, pitch, tilt = self.get_tilt_raw()
            roll -= self.tilt_offsets[0]
            pitch -= self.tilt_offsets[1]
            total_roll += roll
            total_pitch += pitch
            total_tilt += tilt

        avg_roll = total_roll / samples
        avg_pitch = total_pitch / samples
        total = (avg_roll ** 2 + avg_pitch ** 2) ** 0.5  # Pythagorean theorem
        return round(avg_roll, 2), round(avg_pitch, 2), round(total, 2)

    def get_pitch(self, samples=1):
        """ Get pitch angle with applied offsets, optionally averaging over multiple samples """
        total_pitch = 0
        for _ in range(samples):
            pitch = self.get_pitch_raw()
            pitch -= self.tilt_offsets[1]
            total_pitch += pitch

        avg_pitch = total_pitch / samples
        return round(avg_pitch, 2)

# Instantiate MPU6050
mpu = MPU6050(I2C(scl=Pin(16), sda=Pin(2)))
