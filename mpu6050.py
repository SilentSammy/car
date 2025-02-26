from machine import Pin, I2C
import ustruct
import time
import math
import os

class MPU6050:
    def __init__(self, i2c, addr=0x68):
        self.i2c = i2c
        self.addr = addr
        # Wake up the MPU6050
        self.i2c.writeto_mem(self.addr, 0x6B, b'\x00')
        # Load stored offsets (or default to zeros)
        self.gyro_offsets = self.load_offsets("gyro.txt", 3)
        self.tilt_offsets = self.load_offsets("tilt.txt", 2)

    # Calibration and offset persistence
    def save_offsets(self, filename, offsets):
        """Save offsets to a file."""
        with open(filename, "w") as f:
            for value in offsets:
                f.write(str(value) + "\n")

    def load_offsets(self, filename, expected_length):
        """Load offsets from file if available; otherwise, return zeros."""
        try:
            with open(filename, "r") as f:
                offsets = [float(line.strip()) for line in f.readlines()]
                if len(offsets) != expected_length:
                    raise ValueError
                print(f"{filename} offsets loaded:", offsets)
                return offsets
        except (OSError, ValueError):
            print(f"No valid {filename} file found. Using default offsets.")
            return [0.0] * expected_length

    def calibrate_gyro(self, samples=100):
        """Calibrate gyroscope by averaging multiple readings, then save offsets."""
        print("Calibrating gyroscope... Keep sensor still.")
        Gx_offset, Gy_offset, Gz_offset = 0, 0, 0
        for _ in range(samples):
            Gx, Gy, Gz = self.read_gyro_raw()
            Gx_offset += Gx
            Gy_offset += Gy
            Gz_offset += Gz
            time.sleep(0.01)
        Gx_offset /= samples
        Gy_offset /= samples
        Gz_offset /= samples
        self.gyro_offsets = [Gx_offset, Gy_offset, Gz_offset]
        self.save_offsets("gyro.txt", self.gyro_offsets)
        print("Gyro calibration complete:", self.gyro_offsets)

    def calibrate_tilt(self, samples=100):
        """Calibrate tilt sensor (for pitch & roll) and save offsets."""
        print("Calibrating tilt... Keep sensor at desired reference orientation.")
        roll_offset, pitch_offset = 0, 0
        for _ in range(samples):
            roll, pitch, _ = self.get_tilt_raw()
            roll_offset += roll
            pitch_offset += pitch
            time.sleep(0.01)
        roll_offset /= samples
        pitch_offset /= samples
        self.tilt_offsets = [roll_offset, pitch_offset]
        self.save_offsets("tilt.txt", self.tilt_offsets)
        print("Tilt calibration complete:", self.tilt_offsets)

    # Raw sensor readings
    def read_accel_raw(self):
        """Read raw accelerometer values (Ax, Ay, Az)."""
        raw = self.i2c.readfrom_mem(self.addr, 0x3B, 6)
        return ustruct.unpack(">hhh", raw)

    def read_gyro_raw(self):
        """Read raw gyroscope values (Gx, Gy, Gz)."""
        raw = self.i2c.readfrom_mem(self.addr, 0x43, 6)
        return ustruct.unpack(">hhh", raw)

    def read_gyro_x_raw(self):
        """Read raw gyroscope value for Gx (used for pitch rate)."""
        raw = self.i2c.readfrom_mem(self.addr, 0x43, 2)
        Gx, = ustruct.unpack(">h", raw)
        return Gx

    # Processed gyro data
    def get_gyro_calibrated(self):
        """Return calibrated gyro values (pitch, roll, yaw) and total angular velocity (spin)."""
        pitch_rate, roll_rate, yaw_rate = self.read_gyro_raw()
        pitch_rate -= self.gyro_offsets[0]
        roll_rate  -= self.gyro_offsets[1]
        yaw_rate   -= self.gyro_offsets[2]
        
        # Debugging calculations
        pitch_rate_squared = math.pow(pitch_rate, 2)
        roll_rate_squared = math.pow(roll_rate, 2)
        yaw_rate_squared = math.pow(yaw_rate, 2)
        spin = math.sqrt(pitch_rate_squared + roll_rate_squared + yaw_rate_squared)
        
        # Print statements for debugging
        # print(f"Pitch rate: {pitch_rate}, Roll rate: {roll_rate}, Yaw rate: {yaw_rate}")
        # print(f"Pitch rate squared: {pitch_rate_squared}, Roll rate squared: {roll_rate_squared}, Yaw rate squared: {yaw_rate_squared}")
        # print(f"Spin: {spin}")
        
        return pitch_rate, roll_rate, yaw_rate, spin

    def get_avel(self):
        """Return calibrated angular velocity (degrees per second) as a single measurement."""
        pitch_rate, roll_rate, yaw_rate, spin = self.get_gyro_calibrated()
        scale_factor = 131.0  # For ±250°/s mode
        pitch_rate_dps = pitch_rate / scale_factor
        roll_rate_dps  = roll_rate  / scale_factor
        yaw_rate_dps   = yaw_rate   / scale_factor
        spin_dps       = math.sqrt(pitch_rate_dps**2 + roll_rate_dps**2 + yaw_rate_dps**2)
        return pitch_rate_dps, roll_rate_dps, yaw_rate_dps, spin_dps

    def get_pitch_rate(self):
        """Return pitch angular velocity (degrees per second) as a single measurement."""
        pitch_rate = self.read_gyro_x_raw()
        pitch_rate -= self.gyro_offsets[0]
        scale_factor = 131.0
        return round(pitch_rate / scale_factor, 2)

    # Processed accelerometer data
    def get_tilt_raw(self):
        """Compute raw roll and pitch angles (degrees) and total tilt using accelerometer."""
        Ax, Ay, Az = self.read_accel_raw()
        roll = math.atan2(Ax, math.sqrt(Ay**2 + Az**2)) * (180 / math.pi)
        pitch = math.atan2(Ay, math.sqrt(Ax**2 + Az**2)) * (180 / math.pi)
        tilt = math.sqrt(roll**2 + pitch**2)
        return roll, pitch, tilt

    def get_tilt(self):
        """Return roll and pitch angles with applied offsets, and total tilt, as a single measurement."""
        roll, pitch, tilt = self.get_tilt_raw()
        roll -= self.tilt_offsets[0]
        pitch -= self.tilt_offsets[1]
        total = math.sqrt(roll**2 + pitch**2)
        return round(roll, 2), round(pitch, 2), round(total, 2)

    def get_pitch_raw(self):
        """Return raw pitch angle (degrees) from accelerometer."""
        Ax, Ay, Az = self.read_accel_raw()
        pitch = math.atan2(Ay, math.sqrt(Ax**2 + Az**2)) * (180 / math.pi)
        return pitch

    def get_pitch(self):
        """Return pitch angle with applied offset, as a single measurement."""
        pitch = self.get_pitch_raw() - self.tilt_offsets[1]
        return round(pitch, 2)

# Instantiate MPU6050
mpu = MPU6050(I2C(scl=Pin(16), sda=Pin(2)))
