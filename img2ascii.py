#khuza08

from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import math
import os

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

clear()

Tk().withdraw()

# choose image file
filename = askopenfilename(title="choose an image", filetypes=[("image format", "*.jpg *.jpeg *.png")])
if not filename:
    print("nothing choosen")
    exit()

# input
output_name = input("input filename (without extension): ").strip() or "ascii_output"
orientation = input("choose image orientation (p for portrait, L for landscape): ").strip().upper()

# input orientation
if orientation not in ["P", "L"]:
    print("wrong input or else!, portrait as default (P).")
    orientation = "P"

# ascii chars
chars = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. "[::-1]
charArray = list(chars)
charLength = len(charArray)
interval = charLength / 256

scaleFactor = 0.1 # the larger value, more heavier and more detailed
oneCharWidth = 10
oneCharHeight = 18

def getChar(inputInt):
    return charArray[math.floor(inputInt * interval)]

# tuning 
im = Image.open(filename)
im = ImageEnhance.Brightness(im).enhance(1.2) # brightness
im = ImageEnhance.Color(im).enhance(1.3) # saturation
im = ImageEnhance.Contrast(im).enhance(1.3) # contrast

# orientation
width, height = im.size
if orientation == "L":  # landscape
    im = im.resize((int(scaleFactor * width), int(scaleFactor * height * (oneCharWidth / oneCharHeight))), Image.NEAREST)
else:  # portrait
    im = im.resize((int(scaleFactor * width * (oneCharHeight / oneCharWidth)), int(scaleFactor * height)), Image.NEAREST)

# font & size
fnt = ImageFont.truetype('C:\\Windows\\Fonts\\lucon.ttf', 16)

# resize ^
width, height = im.size
pix = im.load()

# text output for canvas
outputImage = Image.new('RGB', (oneCharWidth * width, oneCharHeight * height), color=(0, 0, 0))
d = ImageDraw.Draw(outputImage)
text_file = open(f"{output_name}.txt", "w")

# math
for i in range(height):
    for j in range(width):
        r, g, b = pix[j, i]
        h = int(r / 3 + g / 3 + b / 3)
        pix[j, i] = (h, h, h)
        text_file.write(getChar(h))
        d.text((j * oneCharWidth, i * oneCharHeight), getChar(h), font=fnt, fill=(r, g, b))
    text_file.write('\n')

# save
outputImage.save(f"{output_name}.png")
text_file.close()

print(f"saved as {output_name}.txt and {output_name}.png")
