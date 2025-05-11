# huza (khuza08) 2k25

import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext, messagebox
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageTk
import math
import os
import threading

class ASCIIArtConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ASCII Art Converter")
        self.root.geometry("900x650")
        self.root.configure(bg="#2d2d2d")
        
        # variable
        self.filename = None
        self.output_name = tk.StringVar(value="ascii_output")
        self.orientation = tk.StringVar(value="P")
        self.preview_img = None
        self.result_img = None
        self.is_converting = False
        
        # ASCII chars
        self.chars = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. "[::-1]
        self.charArray = list(self.chars)
        self.charLength = len(self.charArray)
        self.interval = self.charLength / 256
        
        # default config
        self.scaleFactor = tk.DoubleVar(value=0.1)
        self.brightness = tk.DoubleVar(value=1.2)
        self.contrast = tk.DoubleVar(value=1.3)
        self.saturation = tk.DoubleVar(value=1.3)
        self.oneCharWidth = 10
        self.oneCharHeight = 18
        
        self.create_widgets()
    
    def create_widgets(self):
        # main frame
        main_frame = tk.Frame(self.root, bg="#2d2d2d")
        main_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
        
        # left frame - Input controls
        left_frame = tk.LabelFrame(main_frame, text="Input Settings",fg="white", bg="#2d2d2d", font=("Arial", 12))
        left_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH)
        
        # image selection
        tk.Button(left_frame, text="Select Image", command=self.select_image, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), pady=5).pack(fill=tk.X, padx=10, pady=10)
        
        self.image_label = tk.Label(left_frame, text="No image selected",fg="white", bg="#2d2d2d", wraplength=200)
        self.image_label.pack(fill=tk.X, padx=10, pady=5)
        
        # output name
        tk.Label(left_frame, text="Output Filename:", bg="#2d2d2d").pack(anchor=tk.W, padx=10, pady=(10, 0))
        tk.Entry(left_frame, textvariable=self.output_name).pack(fill=tk.X, padx=10, pady=5)
        
        # orientation
        tk.Label(left_frame, text="Orientation:",fg="white", bg="#2d2d2d").pack(anchor=tk.W, padx=10, pady=(10, 0))
        orientation_frame = tk.Frame(left_frame, bg="#2d2d2d")
        orientation_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Radiobutton(orientation_frame, text="Portrait (P)", variable=self.orientation, value="P",fg="white", bg="#2d2d2d").pack(side=tk.LEFT, padx=(0, 10))
        tk.Radiobutton(orientation_frame, text="Landscape (L)", variable=self.orientation, value="L",fg="white", bg="#2d2d2d").pack(side=tk.LEFT)
        
        # advanced settings
        advanced_frame = tk.LabelFrame(left_frame, text="Advanced Settings", bg="#2d2d2d")
        advanced_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # scalefactor
        tk.Label(advanced_frame, text="Scale Factor:",fg="white", bg="#2d2d2d").pack(anchor=tk.W, padx=5, pady=(5, 0))
        scale_slider = ttk.Scale(advanced_frame, from_=0.1, to=1.0, variable=self.scaleFactor, orient=tk.HORIZONTAL)
        scale_slider.pack(fill=tk.X, padx=5, pady=5)
        
        # brightness
        tk.Label(advanced_frame, text="Brightness:",fg="white", bg="#2d2d2d").pack(anchor=tk.W, padx=5, pady=(5, 0))
        brightness_slider = ttk.Scale(advanced_frame, from_=0.5, to=2.0, variable=self.brightness, orient=tk.HORIZONTAL)
        brightness_slider.pack(fill=tk.X, padx=5, pady=5)
        
        # contrast
        tk.Label(advanced_frame, text="Contrast:",fg="white", bg="#2d2d2d").pack(anchor=tk.W, padx=5, pady=(5, 0))
        contrast_slider = ttk.Scale(advanced_frame, from_=0.5, to=2.0, variable=self.contrast, orient=tk.HORIZONTAL)
        contrast_slider.pack(fill=tk.X, padx=5, pady=5)
        
        # saturation
        tk.Label(advanced_frame, text="Saturation:",fg="white", bg="#2d2d2d").pack(anchor=tk.W, padx=5, pady=(5, 0))
        saturation_slider = ttk.Scale(advanced_frame, from_=0.5, to=2.0, variable=self.saturation, orient=tk.HORIZONTAL)
        saturation_slider.pack(fill=tk.X, padx=5, pady=5)
        
        # convert button
        self.convert_btn = tk.Button(
            left_frame, 
            text="Convert to ASCII", 
            command=self.start_conversion, 
            bg="#2196F3", 
            fg="white", 
            font=("Arial", 10, "bold"), 
            pady=8
        )
        self.convert_btn.pack(fill=tk.X, padx=10, pady=10)
        
        # progress bar
        self.progress = ttk.Progressbar(left_frame, orient=tk.HORIZONTAL, length=100, mode='indeterminate')
        self.progress.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.progress.pack_forget()  # Hide initially
        
        # right frame for peview and output
        right_frame = tk.LabelFrame(main_frame, text="Preview & Result",fg="white", bg="#2d2d2d", font=("Arial", 12))
        right_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # preview image
        self.preview_frame = tk.Frame(right_frame, bg="#2d2d2d", width=400, height=300)
        self.preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.preview_frame.pack_propagate(False)
        
        self.preview_label = tk.Label(self.preview_frame,fg="white", bg="#2d2d2d", text="Image preview will appear here")
        self.preview_label.pack(fill=tk.BOTH, expand=True)
        
        # tabs for results
        self.result_tabs = ttk.Notebook(right_frame)
        self.result_tabs.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ASCII text tab
        self.text_frame = tk.Frame(self.result_tabs, bg="#ffffff")
        self.result_tabs.add(self.text_frame, text="ASCII Text")
        
        self.text_output = scrolledtext.ScrolledText(self.text_frame, wrap=tk.WORD, font=("Courier", 8))
        self.text_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # ASCII image tab
        self.image_frame = tk.Frame(self.result_tabs, bg="#ffffff")
        self.result_tabs.add(self.image_frame,fg="white", text="ASCII Image")
        
        self.image_output = tk.Label(self.image_frame, bg="#ffffff")
        self.image_output.pack(fill=tk.BOTH, expand=True)
        
    def select_image(self):
        self.filename = filedialog.askopenfilename(
            title="Choose an image", 
            filetypes=[("Image format", "*.jpg *.jpeg *.png")]
        )
        
        if self.filename:
            self.image_label.config(text=os.path.basename(self.filename))
            self.update_preview()
        
    def update_preview(self):
        if not self.filename:
            return
            
        try:
            # load and resize image for preview
            img = Image.open(self.filename)
            img.thumbnail((400, 300))
            
            # convert to PhotoImage
            photo = ImageTk.PhotoImage(img)
            
            # update preview
            self.preview_label.config(image=photo, text="")
            self.preview_img = photo 
        except Exception as e:
            messagebox.showerror("Preview Error", f"Error loading preview: {str(e)}")
    
    def getChar(self, inputInt):
        return self.charArray[math.floor(inputInt * self.interval)]
    
    def start_conversion(self):
        if not self.filename:
            messagebox.showerror("Error", "Hey!, select your image first please ^^ ")
            return
            
        if not self.output_name.get().strip():
            messagebox.showerror("Error", "Hey!, please enter an output filename!")
            return
            
        #  convertinggggggg progressss
        self.convert_btn.config(state=tk.DISABLED)
        self.progress.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.progress.start()
        self.is_converting = True
        
        # start conversion in a separate thread
        threading.Thread(target=self.convert_to_ascii).start()
    
    def convert_to_ascii(self):
        try:
            # get params
            output_name = self.output_name.get().strip()
            orientation = self.orientation.get()
            
            # load and enhance image
            im = Image.open(self.filename)
            im = ImageEnhance.Brightness(im).enhance(self.brightness.get())
            im = ImageEnhance.Contrast(im).enhance(self.contrast.get())
            im = ImageEnhance.Color(im).enhance(self.saturation.get())
            
            # resize according to orientation
            width, height = im.size
            if orientation == "L":  # landscape
                im = im.resize((
                    int(self.scaleFactor.get() * width), 
                    int(self.scaleFactor.get() * height * (self.oneCharWidth / self.oneCharHeight))
                ), Image.NEAREST)
            else:  # portrait
                im = im.resize((
                    int(self.scaleFactor.get() * width * (self.oneCharHeight / self.oneCharWidth)), 
                    int(self.scaleFactor.get() * height)
                ), Image.NEAREST)
            
            # font
            try:
                fnt = ImageFont.truetype('courier.ttf', 16)
            except IOError:
                # use default font if courier not available
                fnt = ImageFont.load_default()
            
            # get resized dimensions
            width, height = im.size
            pix = im.load()
            
            # output image
            outputImage = Image.new('RGB', (self.oneCharWidth * width, self.oneCharHeight * height), color=(0, 0, 0))
            d = ImageDraw.Draw(outputImage)
            
            # output ascii text
            text_output = ""
            
            # is this math?
            for i in range(height):
                line = ""
                for j in range(width):
                    r, g, b = pix[j, i]
                    h = int(r / 3 + g / 3 + b / 3)
                    pix[j, i] = (h, h, h)
                    char = self.getChar(h)
                    line += char
                    d.text((j * self.oneCharWidth, i * self.oneCharHeight), char, font=fnt, fill=(r, g, b))
                text_output += line + "\n"
            
            # save output
            outputImage.save(f"{output_name}.png")
            with open(f"{output_name}.txt", "w") as text_file:
                text_file.write(text_output)
            
            # update UI with results
            self.root.after(0, lambda: self.update_results(text_output, outputImage))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Conversion Error", f"Error during conversion: {str(e)}"))
        finally:
            # hide progress bar if finished
            self.root.after(0, self.finish_conversion)
    
    def update_results(self, text_output, image):
        # update text output
        self.text_output.delete(1.0, tk.END)
        self.text_output.insert(tk.END, text_output)
        
        # resize image for display
        image.thumbnail((600, 400))
        photo = ImageTk.PhotoImage(image)
        
        # update image output
        self.image_output.config(image=photo)
        self.result_img = photo  # Keep reference
        
        # select result tab
        self.result_tabs.select(0) 
        
        # showw success message
        messagebox.showinfo("Success", f"Yay, Conversion complete!\nSaved as {self.output_name.get()}.txt and {self.output_name.get()}.png")
    
    def finish_conversion(self):
        self.progress.stop()
        self.progress.pack_forget()
        self.convert_btn.config(state=tk.NORMAL)
        self.is_converting = False

if __name__ == "__main__":
    root = tk.Tk()
    app = ASCIIArtConverterApp(root)
    root.mainloop()