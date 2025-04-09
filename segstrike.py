import RPi.GPIO as GPIO
import time
import random
import sys # file descriptor for stdin
import select # check if a key has been pressed without blocking the program forever
import tty # makes the terminal stop waiting for Enter after each keypress
import termios # save and restore terminal settings
# GPIO Pins
CLK = 20
DIO = 16

# Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(CLK, GPIO.OUT)
GPIO.setup(DIO, GPIO.OUT)
GPIO.output(CLK, GPIO.HIGH)
GPIO.output(DIO, GPIO.HIGH)

# Segment map
TOP_SEG = 0x01
BOT_SEG = 0x08
RIGHT_SEG = 0b00000110
LEFT_SEG = 0b000110000
COLON = 0x80

UP_arr = [TOP_SEG, TOP_SEG, TOP_SEG, TOP_SEG]
DOWN_arr = [BOT_SEG, BOT_SEG, BOT_SEG, BOT_SEG]
RIGHT_arr = [0, 0, 0, RIGHT_SEG]
LEFT_arr = [LEFT_SEG, 0, 0, 0]

# I/O helpers
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
    GPIO.output(CLK, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.setup(DIO, GPIO.OUT)

def set_brightness(level):
    start()
    write_byte(0x88 | (level & 0x07))
    stop()

def write_segments(segment_data, toggle_colon=False):
    if toggle_colon:
        start()
        write_byte(0x40)
        stop()
        start()
        write_byte(0xC0)
        for val in segment_data:
            write_byte(val ^ COLON)
        stop()

        time.sleep(0.001)

        start()
        write_byte(0x40)
        stop()
        start()
        write_byte(0xC0)
        for val in segment_data:
            write_byte(val)
        stop()
    else:
        start()
        write_byte(0x40)
        stop()
        start()
        write_byte(0xC0)
        for val in segment_data:
            write_byte(val)
        stop()

def clear_display():
    write_segments([0, 0, 0, 0])

# key reader
def get_key(timeout=100):
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    start_time = time.time()
    key = None
    try:
        while time.time() - start_time < timeout:
            if select.select([sys.stdin], [], [], 0)[0]:
                key = sys.stdin.read(1)
                break
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return key

# Game logic
def segment_strike(diff="easy"):
    print(f"{diff} mode.... \nGet ready! You have 15 seconds!!")
    time.sleep(1)
    score = 0
    round_time = 15
    end_time = time.time() + round_time

    while time.time() < end_time:
        mode = random.choice(['up', 'down', 'left', 'right'])
        if mode == 'up':
            write_segments(UP_arr, True)
        elif mode == 'down':
            write_segments(DOWN_arr, True)
        elif mode == 'right':
            write_segments(RIGHT_arr, True)
        elif mode == 'left':
            write_segments(LEFT_arr, True)

        #print("debug: mode ", mode)
        if diff == "hard":
            key = get_key(1)
        else:
            key = get_key()

        if (mode == 'up' and key == 'w') or (mode == 'down' and key == 's') or (mode == 'left' and key == 'a') or (mode == 'right' and key == 'd'):
            print("Nice! +1")
            score += 1
        else:
            print("Wrong key!!  ", key)
            if diff == "medium":
                print("oops... -1")
                score -= 1
            elif diff == "hard":
                print("oh NAH! -1")
                score -= 1

    print(f"\nTime's up! Your score: {score}")
    digits = [int(x) for x in str(score).rjust(4, '0')]
    seg_map = [0x3F, 0x06, 0x5B, 0x4F, 0x66,
               0x6D, 0x7D, 0x07, 0x7F, 0x6F]
    seg_digits = [seg_map[d] for d in digits]
    write_segments(seg_digits)

    time.sleep(3)
    clear_display()

if __name__ == "__main__":
    try:
        set_brightness(7)
        print("Choose difficulty:")
        print("1. easy")
        print("2. medium")
        print("3. hard")
        while True:
            userinput = input("?: ")
            diffs = {'1': "easy", '2': "medium" ,'3': "hard"}
            if userinput in diffs:
                segment_strike(diffs[userinput])
            else:
                print("Invalid input. Please choose 1, 2, or 3.")

    except KeyboardInterrupt:
        pass
    finally:
        clear_display()
        GPIO.cleanup()
