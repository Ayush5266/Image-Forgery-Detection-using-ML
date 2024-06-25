from tkinter import *
from tkinter import filedialog, ttk, messagebox
from PIL import ImageTk, Image, ExifTags, ImageChops
from optparse import OptionParser
from datetime import datetime
import numpy as np
import random
import cv2
import re
import os
from prettytable import PrettyTable

from ForgeryDetection import Detect
import double_jpeg_compression
import noise_variance
import copy_move_cfa

# Global variables
IMG_WIDTH = 400
IMG_HEIGHT = 400
uploaded_image = None

# Copy-move parameters
cmd = OptionParser("usage: %prog image_file [options]")
cmd.add_option('', '--imauto', help='Automatically search identical regions. (default: %default)', default=1)
cmd.add_option('', '--imblev', help='Blur level for degrading image details. (default: %default)', default=8)
cmd.add_option('', '--impalred', help='Image palette reduction factor. (default: %default)', default=15)
cmd.add_option('', '--rgsim', help='Region similarity threshold. (default: %default)', default=5)
cmd.add_option('', '--rgsize', help='Region size threshold. (default: %default)', default=1.5)
cmd.add_option('', '--blsim', help='Block similarity threshold. (default: %default)', default=200)
cmd.add_option('', '--blcoldev', help='Block color deviation threshold. (default: %default)', default=0.2)
cmd.add_option('', '--blint', help='Block intersection threshold. (default: %default)', default=0.2)
opt, args = cmd.parse_args()

def getImage(path, width, height):
    img = Image.open(path)
    img = img.resize((width, height), Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(img)

def browseFile():
    filename = filedialog.askopenfilename(title="Select an image", filetypes=[("JPEG files", "*.jpeg"), ("PNG files", "*.png"), ("JPG files", "*.jpg")])
    if not filename:
        return

    global uploaded_image
    uploaded_image = filename

    progressBar['value'] = 0
    fileLabel.configure(text=filename)
    img = getImage(filename, IMG_WIDTH, IMG_HEIGHT)
    imagePanel.configure(image=img)
    imagePanel.image = img

    blank_img = getImage("images/output.png", IMG_WIDTH, IMG_HEIGHT)
    resultPanel.configure(image=blank_img)
    resultPanel.image = blank_img
    resultLabel.configure(text="READY TO SCAN", foreground="green")

def copy_move_forgery():
    if not uploaded_image:
        messagebox.showerror('Error', "Please select an image")
        return

    detect = Detect(uploaded_image)
    key_points, descriptors = detect.siftDetector()
    forgery = detect.locateForgery(60, 2)
    progressBar['value'] = 100

    if forgery is None:
        img = getImage("images/no_copy_move.png", IMG_WIDTH, IMG_HEIGHT)
        resultPanel.configure(image=img)
        resultPanel.image = img
        resultLabel.configure(text="ORIGINAL IMAGE", foreground="green")
    else:
        img = getImage("images/copy_move.png", IMG_WIDTH, IMG_HEIGHT)
        resultPanel.configure(image=img)
        resultPanel.image = img
        resultLabel.configure(text="Image Forged", foreground="red")
        cv2.imshow('Forgery', forgery)
        if cv2.waitKey(1000) in [ord('q'), ord('Q')]:
            cv2.destroyAllWindows()

def metadata_analysis():
    if not uploaded_image:
        messagebox.showerror('Error', "Please select an image")
        return

    img = Image.open(uploaded_image)
    img_exif = img.getexif()
    progressBar['value'] = 100

    if img_exif is None:
        img = getImage("images/no_metadata.png", IMG_WIDTH, IMG_HEIGHT)
        resultPanel.configure(image=img)
        resultPanel.image = img
        resultLabel.configure(text="NO Data Found", foreground="red")
    else:
        img = getImage("images/metadata.png", IMG_WIDTH, IMG_HEIGHT)
        resultPanel.configure(image=img)
        resultPanel.image = img
        resultLabel.configure(text="Metadata Details", foreground="green")
        with open('Metadata_analysis.txt', 'w') as f:
            for key, val in img_exif.items():
                if key in ExifTags.TAGS:
                    f.write(f'{ExifTags.TAGS[key]} : {val}\n')
        os.startfile('Metadata_analysis.txt')

def noise_variance_inconsistency():
    if not uploaded_image:
        messagebox.showerror('Error', "Please select an image")
        return

    noise_forgery = noise_variance.detect(uploaded_image)
    progressBar['value'] = 100

    if noise_forgery:
        img = getImage("images/varience.png", IMG_WIDTH, IMG_HEIGHT)
        resultPanel.configure(image=img)
        resultPanel.image = img
        resultLabel.configure(text="Noise variance", foreground="red")
    else:
        img = getImage("images/no_varience.png", IMG_WIDTH, IMG_HEIGHT)
        resultPanel.configure(image=img)
        resultPanel.image = img
        resultLabel.configure(text="No Noise variance", foreground="green")

def cfa_artifact():
    if not uploaded_image:
        messagebox.showerror('Error', "Please select an image")
        return

    identical_regions_cfa = copy_move_cfa.detect(uploaded_image, opt, args)
    progressBar['value'] = 100

    if identical_regions_cfa:
        img = getImage("images/cfa.png", IMG_WIDTH, IMG_HEIGHT)
        resultPanel.configure(image=img)
        resultPanel.image = img
        resultLabel.configure(text=f"{str(identical_regions_cfa)}, CFA artifacts detected", foreground="red")
    else:
        img = getImage("images/no_cfa.png", IMG_WIDTH, IMG_HEIGHT)
        resultPanel.configure(image=img)
        resultPanel.image = img
        resultLabel.configure(text="NO-CFA artifacts detected", foreground="green")

def ela_analysis():
    if not uploaded_image:
        messagebox.showerror('Error', "Please select an image")
        return

    TEMP = 'temp.jpg'
    SCALE = 10
    original = Image.open(uploaded_image)
    original.save(TEMP, quality=90)
    temporary = Image.open(TEMP)
    diff = ImageChops.difference(original, temporary)
    d = diff.load()
    WIDTH, HEIGHT = diff.size

    for x in range(WIDTH):
        for y in range(HEIGHT):
            d[x, y] = tuple(k * SCALE for k in d[x, y])

    progressBar['value'] = 100
    diff.show()

def jpeg_Compression():
    if not uploaded_image:
        messagebox.showerror('Error', "Please select an image")
        return

    double_compressed = double_jpeg_compression.detect(uploaded_image)
    progressBar['value'] = 100

    if double_compressed:
        img = getImage("images/double_compression.png", IMG_WIDTH, IMG_HEIGHT)
        resultPanel.configure(image=img)
        resultPanel.image = img
        resultLabel.configure(text="Double compression", foreground="red")
    else:
        img = getImage("images/single_compression.png", IMG_WIDTH, IMG_HEIGHT)
        resultPanel.configure(image=img)
        resultPanel.image = img
        resultLabel.configure(text="Single compression", foreground="green")

def image_decode():
    if not uploaded_image:
        messagebox.showerror('Error', "Please select an image")
        return

    img = cv2.imread(uploaded_image)
    width = img.shape[0]
    height = img.shape[1]
    img1 = np.zeros((width, height, 3), np.uint8)
    img2 = np.zeros((width, height, 3), np.uint8)

    for i in range(width):
        for j in range(height):
            for l in range(3):
                v1 = format(img[i][j][l], '08b')
                v2 = v1[:4] + chr(random.randint(0, 1)+48) * 4
                v3 = v1[4:] + chr(random.randint(0, 1)+48) * 4
                img1[i][j][l] = int(v2, 2)
                img2[i][j][l] = int(v3, 2)

    progressBar['value'] = 100
    cv2.imwrite('output.png', img2)
    im = Image.open('output.png')
    im.show()

def string_analysis():
    if not uploaded_image:
        messagebox.showerror('Error', "Please select an image")
        return

    x = PrettyTable()
    x.field_names = ["Bytes", "8-bit", "string"]

    with open(uploaded_image, "rb") as f:
        n = 0
        b = f.read(16)

        while b:
            s1 = " ".join([f"{i:02x}" for i in b])
            s1 = s1[0:23] + " " + s1[23:]
            s2 = "".join([chr(i) if 32 <= i <= 127 else "." for i in b])
            x.add_row([f"{n * 16:08x}", s1, s2])
            b = f.read(16)
            n += 1

    with open('strings.txt', 'w') as file:
        file.write(str(x))

    progressBar['value'] = 100
    os.startfile('strings.txt')

def create_gui():
    root = Tk()
    root.title("Image Forensic")
    root.geometry('850x600')
    root.resizable(0, 0)

    # Title label
    titleLabel = Label(root, text="Image Forensics Tool", font=("Arial", 18))
    titleLabel.grid(row=0, column=0, columnspan=4, pady=10)

    # Image Panels
    global imagePanel
    global resultPanel
    imagePanel = Label(root, width=IMG_WIDTH, height=IMG_HEIGHT)
    imagePanel.grid(row=1, column=0, columnspan=2, padx=10, pady=10)
    resultPanel = Label(root, width=IMG_WIDTH, height=IMG_HEIGHT)
    resultPanel.grid(row=1, column=2, columnspan=2, padx=10, pady=10)

    # Labels
    global fileLabel
    fileLabel = Label(root, text="No file selected", font=("Arial", 12))
    fileLabel.grid(row=2, column=0, columnspan=4, pady=5)
    global resultLabel
    resultLabel = Label(root, text="READY TO SCAN", font=("Arial", 12), foreground="green")
    resultLabel.grid(row=3, column=0, columnspan=4, pady=5)

    # Progress Bar
    global progressBar
    progressBar = ttk.Progressbar(root, length=100, mode='determinate')
    progressBar.grid(row=4, column=0, columnspan=4, pady=5)

    # Buttons
    browseButton = Button(root, text="Browse File", command=browseFile, width=15)
    browseButton.grid(row=5, column=0, pady=5)
    elaButton = Button(root, text="ELA Analysis", command=ela_analysis, width=15)
    elaButton.grid(row=5, column=1, pady=5)
    metadataButton = Button(root, text="Metadata Analysis", command=metadata_analysis, width=15)
    metadataButton.grid(row=5, column=2, pady=5)
    decodeButton = Button(root, text="Decode", command=image_decode, width=15)
    decodeButton.grid(row=5, column=3, pady=5)

    compressionButton = Button(root, text="JPEG Compression", command=jpeg_Compression, width=15)
    compressionButton.grid(row=6, column=0, pady=5)
    copyMoveButton = Button(root, text="Copy-Move Forgery", command=copy_move_forgery, width=15)
    copyMoveButton.grid(row=6, column=1, pady=5)
    cfaButton = Button(root, text="CFA Artifact", command=cfa_artifact, width=15)
    cfaButton.grid(row=6, column=2, pady=5)
    noiseButton = Button(root, text="Noise Variance", command=noise_variance_inconsistency, width=15)
    noiseButton.grid(row=6, column=3, pady=5)

    stringButton = Button(root, text="String Analysis", command=string_analysis, width=15)
    stringButton.grid(row=7, column=1, pady=5)

    root.mainloop()

if __name__ == "__main__":
    create_gui()
