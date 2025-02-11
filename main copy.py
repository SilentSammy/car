from machine import Pin, I2C
import time
from mpu6050 import MPU6050

# Initialize I2C with D4 (SDA) and D0 (SCL)
i2c = I2C(scl=Pin(16), sda=Pin(2))

# Initialize MPU6050 (calibration happens on startup)
mpu = MPU6050(i2c)

while True:
    accel, gyro = mpu.read_accel_gyro()
    print("Accelerometer (g):", accel)
    print("Gyroscope (°/s):", gyro)
    print("-" * 30)
    time.sleep(1)
