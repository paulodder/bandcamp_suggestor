import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)


class RPButtons:
    def __init__(self, ports):
        """
        Initialize with list of ports

        """
        self.buttons__ports = list(enumerate(ports))

        for port in ports:
            GPIO.setup(port, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def button_pressed(self):
        """Returns the port index if a button is pressed, False otherwise"""
        for button, port in self.buttons__ports:
            if GPIO.input(port) == False:
                return button
        return False

    def button_pressed_blocking(self, timeout=1, update_rate=0.1):
        """Returns the port index if a button is pressed, False otherwise"""
        elapsed = 0
        while True:
            for button, port in self.buttons__ports:
                if GPIO.input(port) == False:
                    return button
            time.sleep(update_rate)

            elapsed += update_rate
            if elapsed >= timeout:
                return False
