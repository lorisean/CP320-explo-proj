import RPi.GPIO as GPIO
import time
import random

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
LEFT_SEG = 0b00110000
COLON = 0x80

UP_arr = [TOP_SEG, TOP_SEG, TOP_SEG, TOP_SEG]
DOWN_arr = [BOT_SEG, BOT_SEG, BOT_SEG, BOT_SEG]
RIGHT_arr = [0, 0, 0, RIGHT_SEG]
LEFT_arr = [LEFT_SEG, 0, 0, 0]

notUP_arr = [TOP_SEG, TOP_SEG ^ 0b01000000, TOP_SEG ^ 0b01000000, TOP_SEG]
notDOWN_arr = [BOT_SEG, BOT_SEG ^ 0b01000000, BOT_SEG ^ 0b01000000, BOT_SEG]
notRIGHT_arr = [0, 0 ^ 0b01000000, 0 ^ 0b01000000, RIGHT_SEG]
notLEFT_arr = [LEFT_SEG, 0 ^ 0b01000000, 0 ^ 0b01000000, 0]

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

def randomizerr(shape, count):
    choices = []
    i = count
    while i > 0:
        option = random.choice(["new", "reuse"])
        #print(f"option: {option}")

        if option == "new":
            random_shape = random.getrandbits(32)
            random_shape_array = [
                (random_shape >> 24) & 0xFF,  # first 8 bits
                (random_shape >> 16) & 0xFF,
                (random_shape >> 8) & 0xFF,
                random_shape & 0xFF  # last 8 bits
            ]
            #print(f"option: {option}, choices: {choices}, random_shape_array: {random_shape_array}, count: {count}")
            choices.append(random_shape_array)

        else: # reuse shape
            degree = random.randint(1, 3)
            shapeclone = shape.copy()
            positions = random.sample(range(4), degree)
            new_bytes = [random.getrandbits(8) for _ in range(degree)]
            for pos, val in zip(positions, new_bytes):
                shapeclone[pos] = val
            choices.append(shapeclone)

        i -= 1
        time.sleep(0.25)
        #print("i", i)

    #print(f"randomizerr generated {len(choices)} shapes!")
    return choices

# matching game
# easy for 2 digits, med for 3, hard for everything
# randomize 32 bits and split into array[4] (hard)
def matcha(diff="easy"):
    print(f"{diff} difficulty.... \nGet ready!")
    time.sleep(1)
    score = 0
    game_time = 60*3
    round_speed = 3
    shapegen = 4
    end_time = time.time() + game_time
    winner = False
    round = 1
    while time.time() < end_time and not winner:
        random_shape = random.getrandbits(32)
        random_shape_array = [
            (random_shape >> 24) & 0xFF,  # first 8 bits
            (random_shape >> 16) & 0xFF,
            (random_shape >> 8) & 0xFF,
            random_shape & 0xFF  # last 8 bits
        ]

        # randomly make 4+ other shapes or edit the existing shape for max randomness
        clear_display()
        time.sleep(1)
        # create options
        random_shape_choices = randomizerr(random_shape_array, shapegen) # array of arrays
        index = random.randint(1, shapegen - 1)
        random_shape_choices.insert(index, random_shape_array)
        print()
        print(f"Round {round}")

        tries = 3
        while tries > 0:
            tries -= 1
            print(f"Memorize this shape!") #, random_shape_array)
            #print()
            write_segments(random_shape_array)
            time.sleep(round_speed)
            clear_display()
            time.sleep(1)

            print("The shapes...")
            for shapes in random_shape_choices: # shapes is an array like random_shape_array

                #print("debug:shapes", shapes)

                write_segments(shapes)
                time.sleep(round_speed) # see shapes for round_speed seconds
            clear_display()
            userinput = input("Which shape was the correct match: ")
            if userinput == str(index+1):
                print("Well done!")
                #winner = True
                score+=1
                break
            else :
                print("NOPE.", tries, "left...")
        round += 1

    print(f"\nTime's up! Your score: {score}")

    """if winner:
        print("You win!")
    else:
        print("You lose AWWWW!")"""

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
        while True:
            matcha()

    except KeyboardInterrupt:
        pass
    finally:
        clear_display()
        GPIO.cleanup()
else:
    write_segments(UP_arr, True)
    time.sleep(1)
    write_segments(DOWN_arr, True)
    time.sleep(1)
    write_segments(RIGHT_arr, True)
    time.sleep(1)
    write_segments(LEFT_arr, True)
    time.sleep(1)
    write_segments(notUP_arr, True)
    time.sleep(1)
    write_segments(notDOWN_arr, True)
    time.sleep(1)
    write_segments(notRIGHT_arr, True)
    time.sleep(1)
    write_segments(notLEFT_arr, True)

    time.sleep(1)
    clear_display()
    GPIO.cleanup()


