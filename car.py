import machine

class Car:
    def __init__(self):
        self.min_freq = 5   # Minimum PWM frequency at low speeds
        self.max_freq = 100  # Maximum PWM frequency at full throttle

        # Motor A (Left)
        self.ENA = machine.PWM(machine.Pin(5), freq=20, duty=0)
        self.IN1 = machine.Pin(4, machine.Pin.OUT)
        self.IN2 = machine.Pin(0, machine.Pin.OUT)
        self.MtrA = (self.ENA, self.IN1, self.IN2)

        # Motor B (Right)
        self.ENB = machine.PWM(machine.Pin(14), freq=20, duty=0)
        self.IN3 = machine.Pin(12, machine.Pin.OUT)
        self.IN4 = machine.Pin(13, machine.Pin.OUT)
        self.MtrB = (self.ENB, self.IN3, self.IN4)

        # Initialize both motors to stop
        set_mode(0, self.MtrA)
        set_mode(0, self.MtrB)

    @property
    def l_thr(self):
        return abs(get_speed(self.MtrA)) * (-1 if get_mode(self.MtrA) == 2 else 1)

    @l_thr.setter
    def l_thr(self, value):
        """ Set left motor throttle (-1 to 1) """
        value = max(-1, min(1, value))  # Constrain to -1 to 1
        self.update_motor(self.MtrA, value)

    @property
    def r_thr(self):
        return abs(get_speed(self.MtrB)) * (-1 if get_mode(self.MtrB) == 2 else 1)

    @r_thr.setter
    def r_thr(self, value):
        """ Set right motor throttle (-1 to 1) """
        value = max(-1, min(1, value))  # Constrain to -1 to 1
        self.update_motor(self.MtrB, value)

    def go(self, throttle):
        """ Set throttle for both motors """
        self.l_thr = throttle
        self.r_thr = throttle

    def stop(self):
        """ Stop both motors """
        self.l_thr = 0
        self.r_thr = 0

    def update_motor(self, motor, throttle):
        """ Update motor speed and mode based on throttle """
        speed = abs(throttle)
        mode = 1 if throttle >= 0 else 2  # 1 = Forward, 2 = Reverse

        # Direct multiplication scaling, clamped to min_freq
        new_freq = max(self.min_freq, int(self.max_freq * speed))
        motor[0].freq(new_freq)  # Dynamically update PWM frequency

        set_speed(speed, motor)
        set_mode(mode, motor)

def set_mode(mode, motor):
    """ Set motor direction """
    _, IN1, IN2 = motor
    IN1.value(mode & 1)
    IN2.value(mode >> 1)

def set_speed(speed, motor):
    """ Set motor speed (0 to 1 scaled to 1023 PWM) """
    motor[0].duty(int(min(speed * 1023, 1023)))

def get_speed(motor):
    return round(motor[0].duty() / 1024, 2)

def get_mode(motor):
    _, IN1, IN2 = motor
    return (IN2.value() << 1) | IN1.value()