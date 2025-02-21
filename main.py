import web
import machine
import time
from car import car
from mpu6050 import mpu
from averager import MeasurementAverager

def test():
    with MeasurementAverager(sample_function=lambda: mpu.get_avel()[2], interval=10) as yaw_averager:
        while True:
            # Inside this block, yaw_averager is active and sampling.
            time.sleep(0.5)  # Let it collect some samples
            avg_yaw = yaw_averager.average_since_last_measurement()
            print("Averaged yaw rate:", avg_yaw)

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

def spin_at_rate1(dps=5, timeout=10000, interval=50):
    """ Spins the car at a constant rate using a PID loop with a Timer. """
    tmr = machine.Timer(-1)  # Create a software timer
    try:
        print("Starting spin in 5 seconds...")
        time.sleep(5)
        start_time = time.ticks_ms()  # Record start time

        # PID Variables
        Kp = 0.02  # Proportional gain (adjust as needed)
        Ki = 0.001  # Integral gain
        Kd = 0.005  # Derivative gain
        integral = 0
        last_error = 0

        def pid_control(t):
            """ PID loop to maintain constant spin rate. """
            nonlocal integral, last_error

            # Read current yaw rate (Z-axis) from the gyro
            _, _, yaw_rate, _ = mpu.get_avel()  

            # Compute error
            error = dps - yaw_rate  

            # PID Terms
            integral += error  # Accumulate integral term
            derivative = error - last_error  # Compute derivative term
            last_error = error  # Store last error for next iteration

            # Compute PID output (steering adjustment)
            output = (Kp * error) + (Ki * integral) + (Kd * derivative)

            # Apply steering (scale if needed)
            car.steering = max(-1, min(1, output))

            print(f"Yaw: {yaw_rate:.2f}°/s, Target: {dps}°/s, Error: {error:.2f}, Steering: {car.steering:.2f}")

            # Stop the timer when timeout is reached
            if time.ticks_diff(time.ticks_ms(), start_time) >= timeout:
                tmr.deinit()
                car.stop()
                print("Spin complete.")

        # Start the PID loop using the timer (runs at a fixed interval)
        tmr.init(period=interval, mode=machine.Timer.PERIODIC, callback=pid_control)

        # Wait for the timeout to complete
        while time.ticks_diff(time.ticks_ms(), start_time) < timeout:
            pass
    finally:
        tmr.deinit()
        car.stop()

def spin_at_rate(dps=5, timeout=10000, interval=50, Kp = 0.02, Ki = 0.001, Kd = 0.005):
    """ Spins the car at a constant rate using a PID loop with a Timer. """
    tmr = machine.Timer(-1)  # Create a software timer
    try:
        print("Starting spin in 5 seconds...")
        time.sleep(5)
        start_time = time.ticks_ms()  # Record start time

        # PID Variables
        integral = 0
        last_error = 0

        def pid_control(t):
            nonlocal integral, last_error

            # Read current yaw rate (Z-axis) from the gyro
            # Assuming mpu.get_avel() returns (Gx_dps, Gy_dps, Gz_dps)
            _, _, yaw_rate, _ = mpu.get_avel()
            yaw_rate = -yaw_rate  # Invert yaw rate for Z-axis

            # Compute error (desired rate minus current rate)
            error = dps - yaw_rate

            # Update integral (with anti-windup)
            integral += error
            # Cap the integral term using min and max functions
            integral = max(-100, min(100, integral))

            # Derivative term
            derivative = error - last_error
            last_error = error

            # PID output
            output = (Kp * error) + (Ki * integral) + (Kd * derivative)

            # Apply steering adjustment (ensure within [-1, 1])
            car.steering = max(-0.35, min(0.35, output))

            print(f"Yaw: {yaw_rate:.2f}°/s, Target: {dps}°/s, Error: {error:.2f}, Steering: {car.steering:.2f}")

            # Stop the timer and car when timeout is reached
            if time.ticks_diff(time.ticks_ms(), start_time) >= timeout:
                tmr.deinit()
                car.stop()
                print("Spin complete.")

        # Start the PID loop using the timer (fixed interval)
        tmr.init(period=interval, mode=machine.Timer.PERIODIC, callback=pid_control)

        # Wait until the timeout is reached
        while time.ticks_diff(time.ticks_ms(), start_time) < timeout:
            pass

    finally:
        tmr.deinit()
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
    # main()
    pass
