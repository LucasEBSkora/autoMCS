from Encoder import Encoder
from time import sleep
import RPi.GPIO as GPIO
from display import Display 

ENCODER_GPIO_A = 14
ENCODER_GPIO_B = 15
ENCODER_GPIO_BUTTON = 4

def _onButtonPressed(encoder):
	print("pressed")
	encoder.pressed = True

def setupEncoder():
	GPIO.setmode(GPIO.BCM)
	encoder = Encoder(ENCODER_GPIO_A, ENCODER_GPIO_B)

	GPIO.setup(ENCODER_GPIO_BUTTON, GPIO.IN)

	GPIO.add_event_detect(ENCODER_GPIO_BUTTON, GPIO.FALLING, bouncetime=30, callback=lambda _: _onButtonPressed(encoder))
	encoder.pressed = False
	return encoder

def selectOptionEncoder(menu, display, encoder):
	display.drawMenu(menu)
	previous = encoder.read()
	option = 0
	while not encoder.pressed:
		r = encoder.read()
		if r > previous:
			option -= 1
		elif r < previous:
			option += 1
		previous = r
		display.drawMenu(menu, option)
		sleep(.25)
	encoder.pressed = False
	option = option % len(menu) + 1
	display.drawTitle()
	return option

#enc = setupEncoder(lambda x: print("pressed: ", x))
#d = Display()
#opts = ["Move", "Offer draw", "Offer takeback", "Resign"]

#d.drawMenu(opts, 0)

#previous = enc.read()
#i = 0
#while True:
#    r = enc.read()
#    if r > previous:
#        print(r)
#        i-=1
#        d.drawMenu(opts, i)
#        previous = r
#    if r < previous:
#        print(r)
#        i+=1
#        d.drawMenu(opts, i)
#        previous = r
#    sleep(.25)
