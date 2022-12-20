import RPi.GPIO as GPIO
import time

Pin = 17

dutyCycle = 0

GPIO.setmode(GPIO.BCM)
GPIO.setup(Pin, GPIO.OUT)

PWMController = GPIO.PWM(Pin, 100)

PWMController.start(50)
while True:
    PWMController.ChangeDutyCycle(50)
