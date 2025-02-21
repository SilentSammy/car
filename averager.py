import machine

class MeasurementAverager:
    def __init__(self, sample_function, interval=10):
        """
        Initializes the averager.
        
        sample_function: A callable that returns a measurement (number or tuple).
        interval: Timer period in milliseconds for sampling.
        """
        self.sample_function = sample_function
        self.interval = interval
        self._sum = None   # Running total of samples
        self._count = 0    # Number of samples taken
        
        # Set up the timer for periodic sampling
        self.timer = machine.Timer(-1)
        self.timer.init(period=self.interval, mode=machine.Timer.PERIODIC, callback=self._sample_callback)
    
    def _sample_callback(self, t):
        sample = self.sample_function()
        # On first sample, initialize _sum
        if self._sum is None:
            self._sum = sample
        else:
            if isinstance(sample, tuple):
                # Element-wise addition for tuples
                self._sum = tuple(s + v for s, v in zip(self._sum, sample))
            else:
                self._sum += sample
        self._count += 1

    def average_since_last_measurement(self):
        """
        Returns the average measurement since the last call and resets the accumulators.
        If no samples have been collected, returns None.
        """
        if self._count == 0:
            return None
        if isinstance(self._sum, tuple):
            avg = tuple(s / self._count for s in self._sum)
        else:
            avg = self._sum / self._count
        # Reset the accumulator and sample count
        self._sum = None
        self._count = 0
        return avg

    def stop(self):
        """ Stops the timer. """
        if self.timer:
            self.timer.deinit()
            self.timer = None

    # Context-manager support:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()

    def __del__(self):
        self.stop()

# Test the averager
if __name__ == "__main__":
    import time
    import mpu6050

    def test():
        with MeasurementAverager(sample_function=lambda: mpu.get_avel()[2], interval=10) as yaw_averager:
            while True:
                # Inside this block, yaw_averager is active and sampling.
                time.sleep(0.5)  # Let it collect some samples
                avg_yaw = yaw_averager.average_since_last_measurement()
                print("Averaged yaw rate:", avg_yaw)

    test()
