import web
import machine
import time
from car import car
from mpu6050 import mpu

def print_avel():
    while True:
        avel = mpu.get_avel()
        print(f"Gx: {avel[0]}, Gy: {avel[1]}, Gz: {avel[2]}")
        time.sleep(0.25)

def print_avel_avg(samples=5):
    while True:
        total = [0, 0, 0]
        for _ in range(samples):
            avel = mpu.get_avel()
            total[0] += avel[0]
            total[1] += avel[1]
            total[2] += avel[2]
            #time.sleep(0.01)
        avg = [v / samples for v in total]
        print(f"Gx: {avg[0]}, Gy: {avg[1]}, Gz: {avg[2]}")
        time.sleep(0.2)

def print_pitch_rate_avg(samples=5):
    while True:
        pr = mpu.get_pitch_rate_avg(samples)
        print(f"{pr}")
        time.sleep(0.2)

def print_pitch_avg(samples = 5):
    while True:
        p = mpu.get_pitch_avg(samples)
        print(f"{p}")
        time.sleep(0.2)

def print_tilt():
    while True:
        roll, pitch = mpu.get_tilt()
        print(f"Pitch: {pitch}, Roll: {roll}")
        time.sleep(0.25)

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

def hold_pitch_test():
    print("Starting test in 5 seconds...")
    time.sleep(5)

    start_pitch = mpu.get_pitch_avg(10)  # Average pitch over 10 readings
    print(f"Starting pitch: {start_pitch}")

    start_time = time.ticks_ms()
    duration = 1000  # Run test for 10 seconds

    while time.ticks_diff(time.ticks_ms(), start_time) < duration:
        current_pitch = mpu.get_pitch_avg(5)  # Get pitch angle
        error = start_pitch - current_pitch  # Difference from target pitch

        # Simple proportional control
        Kp = 0.05  # Proportional gain (tweak this value)
        correction = Kp * error  # Compute throttle correction

        # Clamp throttle to -1 to 1
        car.throttle = max(-0.5, min(0.5, correction))

        print(f"Pitch: {current_pitch}, Throttle: {car.throttle}")

    car.stop()
    print("Test complete.")

def main():
    def receive_state(r):
        print("Received:", r)

        # Receive control variables
        car.throttle = float(r['params'].get('t', car.throttle))
        car.steering = float(r['params'].get('s', car.steering))
        
        # Print received values
        print("Received:", car.throttle, car.steering)
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