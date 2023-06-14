import board
import busio
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

OLED_WIDTH = 128
OLED_HEIGHT = 64

LINE_HEIGHT = 16

class Display:
    def __init__(self, addr = 0x3C):
        self.__i2c = board.I2C()
        self.__oled_reset = digitalio.DigitalInOut(board.D4)
        adafruit_ssd1306.SET_CONTRAST = 255
        self.__oled = adafruit_ssd1306.SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, self.__i2c, addr=addr, reset=self.__oled_reset)
        self.__oled.fill(0)
        self.__oled.show()
        self.__img = Image.new("1", (self.__oled.width, self.__oled.height))
        self.__draw = ImageDraw.Draw(self.__img)
        self.__top_text = None

    def clearDisplay(self):
        self.__top_text = None
        self.__draw.rectangle((0,0,self.__oled.width,self.__oled.height), fill=0)
        self.__oled.image(self.__img)
        self.__oled.show()

    def drawTitle(self):
        self.__draw.rectangle((0,0, self.__oled.width, self.__oled.height), fill=0)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        self.__draw.text((0, 20), "AutoMCS", font=font, fill=255)

        if self.__top_text != None:
            font_top = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15)
            self.__draw.text((10, 0), self.__top_text, font=font_top, fill=255)

        self.__oled.image(self.__img)
        self.__oled.show()

    def setTopText(self, text):
        self.__top_text = text

    def drawMenu(self, opts, selected = 0):
        self.__draw.rectangle((0,0, self.__oled.width, self.__oled.height), fill=0)
        selected = selected % len(opts)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        self.__draw.text((0, 20), "AutoMCS", font=font, fill=255)

        if self.__top_text != None:
            font_top = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15)
            self.__draw.text((10, 0), self.__top_text, font=font_top, fill=255)

        self.__draw.rectangle((0,48,self.__oled.width,48+16), fill=255)
        self.__draw.text((2, 50), "<", fill=0)
        self.__draw.text((abs(int(len(opts[selected])*3 - self.__oled.width/2)), 50), opts[selected], fill=0)
        self.__draw.text((self.__oled.width-6, 50), ">", fill=0)

        self.__oled.image(self.__img)
        self.__oled.show()

