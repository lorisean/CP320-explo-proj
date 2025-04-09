import RPi.GPIO as GPIO
import time

CLK = 20
DIO = 16

GPIO.setmode(GPIO.BCM)
GPIO.setup(CLK, GPIO.OUT)
GPIO.setup(DIO, GPIO.OUT)
GPIO.output(CLK, GPIO.HIGH)
GPIO.output(DIO, GPIO.HIGH)

# 0 - 9
digit_map = [0x3F, 0x06, 0x5B, 0x4F, 0x66,
             0x6D, 0x7D, 0x07, 0x7F, 0x6F]


def start():
    GPIO.output(DIO, GPIO.LOW)
    time.sleep(0.00001)
    GPIO.output(CLK, GPIO.LOW)


def stop():
    GPIO.output(CLK, GPIO.LOW)
    time.sleep(0.00001)
    GPIO.output(DIO, GPIO.LOW)
    time.sleep(0.00001)
    GPIO.output(CLK, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(DIO, GPIO.HIGH)


def write_byte(data):
    for _ in range(8):
        GPIO.output(CLK, GPIO.LOW)
        GPIO.output(DIO, data & 0x01)
        data >>= 1
        time.sleep(0.00001)
        GPIO.output(CLK, GPIO.HIGH)
        time.sleep(0.00001)

    GPIO.output(CLK, GPIO.LOW)
    GPIO.setup(DIO, GPIO.IN)
    time.sleep(0.00001)
    ack = GPIO.input(DIO)
    GPIO.output(CLK, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.setup(DIO, GPIO.OUT)


def set_brightness(level):
    start()
    write_byte(0x88 | (level & 0x07))
    stop()


def display_number(number):
    digits = [0, 0, 0, 0]
    str_num = str(number).rjust(4)
    for i in range(4):
        if str_num[i].isdigit():
            digits[i] = digit_map[int(str_num[i])]
        else:
            digits[i] = 0x00

    start()
    write_byte(0x40)  # Auto increment mode
    stop()

    start()
    write_byte(0xC0)  # Start at address 0
    for d in digits:
        write_byte(d)
    stop()


if __name__ == "__main__":
    set_brightness(7)
    try:
        for i in range(10000):
            display_number(i)
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()
