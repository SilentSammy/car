from machine import Pin, I2C
import time
import ustruct

class MPU6050:
    def __init__(self, i2c, addr=0x68):
        self.i2c = i2c
        self.addr = addr
        self.i2c.writeto_mem(self.addr, 0x6B, b'\x00')  # Wake up MPU6050
        self.gyro_offset = self.get_gyro_offset()  # Gyro calibration

    def get_gyro_offset(self):
        """ Compute gyroscope offsets by averaging multiple readings. """
        print("Calibrating gyroscope... Keep the car still!")
        offsets = [0, 0, 0]
        samples = 100

        for _ in range(samples):
            raw = self.i2c.readfrom_mem(self.addr, 0x43, 6)
            vals = ustruct.unpack(">hhh", raw)
            offsets[0] += vals[0]
            offsets[1] += vals[1]
            offsets[2] += vals[2]

        return [o / samples for o in offsets]

    def get_pitch_rate(self):
        """ Get Y-axis (pitch) rotation rate in degrees/sec (for wheelie stabilization). """
        raw = self.i2c.readfrom_mem(self.addr, 0x43, 6)
        vals = ustruct.unpack(">hhh", raw)
        return (vals[1] - self.gyro_offset[1]) / 131.0  # Y-axis gyro in deg/sec
