import web
import machine
import time
from car import car, set_mode, set_speed
from mpu6050 import mpu
from averager import MeasurementAverager
import math

def test():
    with MeasurementAverager(sample_function=lambda: mpu.get_avel()[2], interval=10) as yaw_averager:
        while True:
            # Inside this block, yaw_averager is active and sampling.
            time.sleep(0.5)  # Let it collect some samples
            avg_yaw = yaw_averager.average_since_last_measurement()
            print("Averaged yaw rate:", avg_yaw)

# MPU Test functions
def print_avel(interval=10, sleep_time=0.2):
    with MeasurementAverager(sample_function=lambda: mpu.get_avel(), interval=interval) as avel_averager:
        while True:
            Gx, Gy, Gz, total = avel_averager.average_since_last_measurement()
            print(f"Gx: {Gx}, Gy: {Gy}, Gz: {Gz}, Total: {total}")
            time.sleep(sleep_time)

def print_pitch_rate(interval=10, sleep_time=0.2):
    with MeasurementAverager(sample_function=lambda: mpu.get_pitch_rate(), interval=interval) as pitch_rate_averager:
        while True:
            pr = pitch_rate_averager.average_since_last_measurement()
            print(f"{pr}")
            time.sleep(sleep_time)

def print_tilt(interval=10, sleep_time=0.2):
    with MeasurementAverager(sample_function=lambda: mpu.get_tilt(), interval=interval) as tilt_averager:
        while True:
            roll, pitch, total = tilt_averager.average_since_last_measurement()
            print(f"Roll: {roll}, Pitch: {pitch}, Total: {total}")
            time.sleep(sleep_time)

def print_pitch(interval=10, sleep_time=0.2):
    with MeasurementAverager(sample_function=lambda: mpu.get_pitch(), interval=interval) as pitch_averager:
        while True:
            p = pitch_averager.average_since_last_measurement()
            print(f"{p}")
            time.sleep(sleep_time)

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

def spin_at_rate(dps=9, timeout=10, dt=0.05, Kp=0, Ki=0.1, Kd=0, limit=0.5, sample_rate=10):
    """ Spins the car at a constant rate using a PID loop with a Timer. """
    tmr = machine.Timer(-1)  # Create a software timer
    averager = None
    try:
        print("Starting spin in 5 seconds...")
        time.sleep(5)
        start_time = time.time()  # Record start time

        # PID Variables
        integral = 0
        last_error = 0

        def pid_control(t):
            nonlocal integral, last_error

            # Read current yaw rate (Z-axis) from the gyro
            # Assuming mpu.get_avel() returns (Gx_dps, Gy_dps, Gz_dps)
            yaw_rate = -averager.average_since_last_measurement()  # Invert yaw rate for Z-axis

            # Compute error (desired rate minus current rate)
            error = dps - yaw_rate

            # Update integral (with anti-windup)
            integral += error * dt
            # Cap the integral term using min and max functions
            integral = max(-100, min(100, integral))

            # Derivative term
            derivative = (error - last_error) / dt
            last_error = error

            # PID output
            output = (Kp * error) + (Ki * integral) + (Kd * derivative)

            # Apply steering adjustment (ensure within [-1, 1])
            car.steering = max(-limit, min(limit, output))

            print(f"Y: {yaw_rate:.2f}, T: {dps}, E: {error:.2f}, S: {car.steering:.2f}")

            # Stop the timer and car when timeout is reached
            if time.time() - start_time >= timeout:
                tmr.deinit()
                car.stop()
                print("Spin complete.")

        # Start taking measurements
        averager = MeasurementAverager(sample_function=lambda: mpu.get_avel()[2], interval=int(dt*1000/sample_rate))

        # Start the PID loop using the timer (fixed interval)
        tmr.init(period=int(dt * 1000), mode=machine.Timer.PERIODIC, callback=pid_control)

        # Wait until the timeout is reached
        while time.time() - start_time < timeout:
            pass

    finally:
        if averager:
            averager.stop()
        tmr.deinit()
        car.stop()

def spin_for_time(spin=0.3, timeout=5):
    """ Spins the car at a fixed steering value for a fixed duration, and measures its angular velocity. """
    with MeasurementAverager(sample_function=lambda: mpu.get_avel()[2], interval=10) as averager:
        try:
            start_time = time.time()  # Record start time

            while time.time() - start_time < timeout:
                car.steering = spin
        finally:
            yaw_rate = averager.average_since_last_measurement()
            car.stop()
            print(f"Yaw rate: {yaw_rate:.2f}")

def motor_test(m, freq):
    # WARNING: Use 5V
    m[0].freq(freq)

    tmr = machine.Timer(-1)
    start_time = time.ticks_ms()  # use ticks_ms for millisecond resolution
    duration = 10  # seconds

    def timer_callback(timer):
        elapsed = time.ticks_diff(time.ticks_ms(), start_time) / 1000  # convert ms to s
        if elapsed < duration:
            sin_val = math.sin(math.pi * elapsed)
            print(sin_val)
            set_mode(1 if sin_val >= 0 else 2, m)
            set_speed(abs(sin_val), m)
        else:
            timer.deinit()
            car.stop()

    tmr.init(period=50, mode=machine.Timer.PERIODIC, callback=timer_callback)

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
    # web.start_access_point()
    web.start_webserver(endpoints)

if __name__ == "__main__":
    # main()
    pass
