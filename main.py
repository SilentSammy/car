import web
import machine
import time
from car import car
from mpu6050 import mpu

# MPU Test functions
def print_avel(samples=5):
    while True:
        Gx, Gy, Gz, total = mpu.get_avel(samples)
        print(f"Gx: {Gx}, Gy: {Gy}, Gz: {Gz}, Total: {total}")
        time.sleep(0.2)

def print_pitch_rate(samples=5):
    while True:
        pr = mpu.get_pitch_rate(samples)
        print(f"{pr}")
        time.sleep(0.2)

def print_tilt(samples = 5):
    while True:
        roll, pitch, total = mpu.get_tilt(samples)
        print(f"Roll: {roll}, Pitch: {pitch}, Total: {total}")
        time.sleep(0.2)

def print_pitch(samples = 5):
    while True:
        p = mpu.get_pitch(samples)
        print(f"{p}")
        time.sleep(0.2)

# Car test functions
def test_sequence():
    time.sleep(5)

    # Test forward movement
    car.throttle = 0.25
    car.steering = 0
    time.sleep(2)

    # Test reverse movement
    car.throttle = -0.25
    car.steering = 0
    time.sleep(2)

    # Test left turn
    car.throttle = 0
    car.steering = -1
    time.sleep(2)

    # Test right turn
    car.throttle = 0
    car.steering = 1
    time.sleep(2)

    # Stop
    car.stop()

def aim_up(threshold=1, timeout=10000, spin_time=200, pause_time=150):
    """ Aligns the car to face uphill using spin-pause cycles to reduce accelerometer noise. """
    print("Test starting in 5 seconds...")
    time.sleep(5)

    try:
        start_time = time.ticks_ms()  # Record start time
        while time.ticks_diff(time.ticks_ms(), start_time) < timeout:
            # Read current tilt values
            roll, pitch, total = mpu.get_tilt()

            # Compute pitch error
            error = total - pitch  # We want pitch to match total incline

            # Determine steering direction based on roll (FIXED direction)
            steering_direction = -1 if roll < 0 else 1  

            # Compute proportional steering value and scale by 0.3
            raw_steering = steering_direction * error * 0.05  
            car.steering = raw_steering * 0.3  

            print(f"Aligning... Roll: {roll:.2f}, Pitch: {pitch:.2f}, Target: {total:.2f}, Error: {error:.2f}, Raw Steering: {raw_steering:.2f}, Scaled Steering: {car.steering:.2f}")

            # Spin for a short duration
            time.sleep(spin_time / 1000)

            # Stop briefly to let accelerometer settle
            car.steering = 0  
            time.sleep(pause_time / 1000)

    finally:
        car.stop()

def main():
    def receive_state(r):
        print("Received:", r)

        # Receive control variables
        car.throttle = float(r['params'].get('t', car.throttle))
        car.steering = float(r['params'].get('s', car.steering))
        
        # Print received values
        return {"t": car.throttle, "s": car.steering}

    print("Starting program...")

    # Set up web server
    endpoints = {
        "ctrl": receive_state
    }
    web.connect_wifi()
    web.start_webserver(endpoints)

if __name__ == "__main__":
    main()
    pass