import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext, messagebox
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageTk
import math
import os
import threading
import gc
import psutil
from tkinterdnd2 import DND_FILES, TkinterDnD

class ASCIIArtConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("image2ascii by khuza08")
        self.root.geometry("900x650")
        self.root.configure(bg="#2d2d2d")
        
        # mem tracking
        self.process = psutil.Process(os.getpid())
        
        # variables
        self.filename = None
        self.output_name = tk.StringVar(value="ascii_output")
        self.orientation = tk.StringVar(value="P")
        self.preview_img = None
        self.result_img = None
        self.original_image = None 
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
        
        #  memory label for monitoring (debug only)
        self.memory_label = None
        
        self.create_widgets()
        
        # Set up periodic memory check (debug only)
        # self.check_memory_usage()
        
        # bind cleanup to window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        # main frame
        main_frame = tk.Frame(self.root, bg="#2d2d2d")
        main_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
        
        # add memory label for debugging (optional)
        # self.memory_label = tk.Label(self.root, text="Memory: 0 MB", fg="white", bg="#2d2d2d")
        # self.memory_label.pack(side=tk.BOTTOM, pady=5)
        
        # left frame - Input controls
        left_frame = tk.LabelFrame(main_frame, text="Input Settings",fg="white", bg="#2d2d2d", font=("Arial", 12))
        left_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH)
        
        # drag and Drop area
        self.drop_frame = tk.Frame(left_frame, bg="#3d3d3d", height=100, bd=2, relief=tk.GROOVE)
        self.drop_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.drop_label = tk.Label(
            self.drop_frame, 
            text="Drop Image Here",
            fg="white", 
            bg="#3d3d3d", 
            font=("Arial", 12, "bold"),
            padx=20,
            pady=20
        )
        self.drop_label.pack(expand=True, fill=tk.BOTH)
        
        # drop zone
        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.drop_file)
        
        # image selection button
        tk.Button(left_frame, text="Select Image", command=self.select_image, bg="#2d2d2d", fg="white", font=("Arial", 10, "bold"), pady=5).pack(fill=tk.X, padx=10, pady=10)
        
        # img info
        self.image_label = tk.Label(left_frame, text="No image selected",fg="white", bg="#2d2d2d", wraplength=200)
        self.image_label.pack(fill=tk.X, padx=10, pady=5)
        
        # output name
        tk.Label(left_frame, text="Output Filename:", fg="white",bg="#2d2d2d").pack(anchor=tk.W, padx=10, pady=(10, 0))
        tk.Entry(left_frame, textvariable=self.output_name).pack(fill=tk.X, padx=10, pady=5)
        
        # orientation
        tk.Label(left_frame, text="Orientation:",fg="white", bg="#2d2d2d").pack(anchor=tk.W, padx=10, pady=(10, 0))
        orientation_frame = tk.Frame(left_frame, bg="#2d2d2d")
        orientation_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Radiobutton(orientation_frame, text="Portrait (P)", variable=self.orientation, value="P", 
                       bg="#2d2d2d", fg="#ffffff", activebackground="#3d3d3d", 
                       activeforeground="#ffffff", selectcolor="#555555", 
                       highlightbackground="#ffffff").pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Radiobutton(orientation_frame, text="Landscape (L)", variable=self.orientation, value="L", 
                       bg="#2d2d2d", fg="#ffffff", activebackground="#3d3d3d", 
                       activeforeground="#ffffff", selectcolor="#555555", 
                       highlightbackground="#ffffff").pack(side=tk.LEFT)
        
        # advanced settings
        advanced_frame = tk.LabelFrame(left_frame, text="Advanced Settings", fg="white", bg="#2d2d2d")
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
        
        # clean memory  (Optional - for debugging)
        # tk.Button(left_frame, text="Clean Memory", command=self.force_cleanup, bg="#2d2d2d", fg="white").pack(fill=tk.X, padx=10, pady=5)
        
        # convert button
        self.convert_btn = tk.Button(
            left_frame, 
            text="Convert to ASCII", 
            command=self.start_conversion, 
            bg="#2d2d2d", 
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
        self.text_frame = tk.Frame(self.result_tabs, bg="#2d2d2d")
        self.result_tabs.add(self.text_frame, text="ASCII Text")
        
        self.text_output = scrolledtext.ScrolledText(self.text_frame, fg="white" , bg="#2d2d2d" ,wrap=tk.WORD, font=("Courier", 8))
        self.text_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # ASCII image tab
        self.image_frame = tk.Frame(self.result_tabs, bg="#2d2d2d")
        self.result_tabs.add(self.image_frame, text="ASCII Image")
        
        self.image_output = tk.Label(self.image_frame, bg="#2d2d2d")
        self.image_output.pack(fill=tk.BOTH, expand=True)

    ## fixed memleak (using around 6GB of ram!)
    def check_memory_usage(self):
        """update memory usage label (for debugging)"""
        if self.memory_label:
            memory_mb = self.process.memory_info().rss / (1024 * 1024)
            self.memory_label.config(text=f"Memory: {memory_mb:.2f} MB")
        self.root.after(1000, self.check_memory_usage)
    
    def force_cleanup(self):
        """force garbage collection and cleanup (for debugging)"""
        self.clean_image_references()
        gc.collect()
        if self.memory_label:
            memory_mb = self.process.memory_info().rss / (1024 * 1024)
            self.memory_label.config(text=f"Memory: {memory_mb:.2f} MB")
        messagebox.showinfo("Memory Cleanup", "Memory cleanup performed")
    
    def clean_image_references(self):
        """clean up image references to prevent memory leaks"""
        # clear preview if it's large
        if hasattr(self, 'preview_label') and self.preview_label.winfo_exists():
            self.preview_label.config(image='')
        
        # close PIL image
        for attr_name in ['original_image']:
            if hasattr(self, attr_name) and getattr(self, attr_name) is not None:
                img = getattr(self, attr_name)
                try:
                    img.close()
                except:
                    pass
                setattr(self, attr_name, None)
        
        # set references to None to help garbage collection
        self.preview_img = None
        self.result_img = None
        
        # force garbage collection
        gc.collect()
        
    def drop_file(self, event):
        """handle the file drop event"""
        # clean up previous image data
        self.clean_image_references()
        file_path = event.data
        
        # clean file path if availablee
        if file_path.startswith("{") and file_path.endswith("}"):
            file_path = file_path[1:-1]
        
        # check if multiple files were dropped
        if " " in file_path and not os.path.exists(file_path):
            file_paths = file_path.split(" ")
            for path in file_paths:
                cleaned_path = path.strip()
                if cleaned_path.startswith('"') and cleaned_path.endswith('"'):
                    cleaned_path = cleaned_path[1:-1]
                if os.path.exists(cleaned_path):
                    file_path = cleaned_path
                    break
        
        # check if the file actually existsz
        if not os.path.exists(file_path):
            messagebox.showerror("Error", f"File not found: {file_path}")
            return

        #try to open file wit PiL to verify valid images
        try:
            test_img = Image.open(file_path)
            test_img.verify()
            test_img.close()

            self.filename = file_path
            self.image_label.config(text=os.path.basename(self.filename))
            self.hide_drop_area()
            self.update_preview()
        except Exception as e:
            err_msg = str(e)
            self.root.after(0, lambda: messagebox.showerror("Conversion Error", f"Error during conversion: {err_msg}"))



        # check if the file is an valid image file
        valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
        if file_path.lower().endswith(valid_extensions):
            self.filename = file_path
            self.image_label.config(text=os.path.basename(self.filename))
            self.hide_drop_area()
            self.update_preview()
        else:
            messagebox.showerror("Error", "Only image files are supported!")
    
    def select_image(self):
        """open file dialog to select an image"""
        # cleanup previous image data
        self.clean_image_references()
        
        self.filename = filedialog.askopenfilename(
            title="Choose an image", 
            filetypes=[("Image format", "*.jpg *.jpeg *.png *.bmp *.gif")]
        )
        
        if self.filename:
            self.image_label.config(text=os.path.basename(self.filename))
            self.hide_drop_area()
            self.update_preview()
    
    def hide_drop_area(self):
        """hide the drop area once an image is selected"""
        self.drop_frame.pack_forget()
    
    def show_drop_area(self):
        """show the drop area again if needed"""
        self.drop_frame.pack(fill=tk.X, padx=10, pady=10, before=self.image_label)
        
    def update_preview(self):
        if not self.filename:
            return
            
        try:
            # clean any existing preview
            if self.preview_img:
                self.preview_label.config(image='')
                self.preview_img = None
            
            # load and resize image for preview
            self.original_image = Image.open(self.filename)
            img_copy = self.original_image.copy()  # Work with a copy
            img_copy.thumbnail((400, 300))
            
            # convert to PhotoImage
            photo = ImageTk.PhotoImage(img_copy)
            
            # update preview
            self.preview_label.config(image=photo, text="")
            self.preview_img = photo
            
            # close the copy to free memory
            img_copy.close()
            
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
            
        # converting progressss
        self.convert_btn.config(state=tk.DISABLED)
        self.progress.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.progress.start()
        self.is_converting = True
        
        # clear previous results
        self.text_output.delete(1.0, tk.END)
        if hasattr(self, 'image_output') and self.image_output.winfo_exists():
            self.image_output.config(image='')
        self.result_img = None
        
        gc.collect()
        
        # start conversion in a separate thread
        threading.Thread(target=self.convert_to_ascii, daemon=True).start()
    
    def convert_to_ascii(self):
        output_image = None
        im = None
        
        try:
            # get params
            output_name = self.output_name.get().strip()
            orientation = self.orientation.get()
            
            # load and enhance image - use a fresh copy from disk to avoid memleak
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
            output_image = Image.new('RGB', (self.oneCharWidth * width, self.oneCharHeight * height), color=(0, 0, 0))
            d = ImageDraw.Draw(output_image)
            
            # output ascii text - minimize string concatenation for memory efficiency
            text_lines = []
            
            # process line by line to reduce memory usage
            for i in range(height):
                line = []
                for j in range(width):
                    r, g, b = pix[j, i][:3]
                    h = int(r / 3 + g / 3 + b / 3)
                    pix[j, i] = (h, h, h)
                    char = self.getChar(h)
                    line.append(char)
                    d.text((j * self.oneCharWidth, i * self.oneCharHeight), char, font=fnt, fill=(r, g, b))
                text_lines.append(''.join(line))
                
                # every few lines, check if we should stop (if app is closing)
                if i % 20 == 0 and not self.is_converting:
                    raise InterruptedError("Conversion cancelled")
            
            text_output = '\n'.join(text_lines)
            
            # save output
            output_image.save(f"{output_name}.png")
            with open(f"{output_name}.txt", "w") as text_file:
                text_file.write(text_output)
            
            # update UI with results but keep limited copies in memory
            disp_image = output_image.copy()  # create copy for display
            disp_image.thumbnail((600, 400))  # resize for display
            
            # sched UI updates on main thread
            self.root.after(0, lambda: self.update_results(text_output, disp_image))
            
        except InterruptedError:
            # conversion was cancelled, do nothing
            pass
        except Exception as e:
            err_msg = str(e)
            self.root.after(0, lambda: messagebox.showerror("Conversion Error", f"Error during conversion: {err_msg}"))

        finally:
            # close images to free memory
            if im is not None:
                im.close()
            
            # hide progress bar if finished
            self.root.after(0, self.finish_conversion)
    
    def update_results(self, text_output, image):
        # update text output
        self.text_output.delete(1.0, tk.END)
        self.text_output.insert(tk.END, text_output)
        
        # cleanup old image reference
        if self.result_img is not None:
            self.image_output.config(image='')
            self.result_img = None
        
        # create photo image for display
        try:
            photo = ImageTk.PhotoImage(image)
            
            # update image output
            self.image_output.config(image=photo)
            self.result_img = photo  # Keep reference
            
            # close the thumbnail image now that we have the PhotoImage
            image.close()
        except Exception as e:
            print(f"Error creating result image: {e}")
        
        # select result tab
        self.result_tabs.select(0) 
        
        gc.collect()
        
        # show success message
        messagebox.showinfo("Success", f"Yay, Conversion complete!\nSaved as {self.output_name.get()}.txt and {self.output_name.get()}.png")
    
    def finish_conversion(self):
        self.progress.stop()
        self.progress.pack_forget()
        self.convert_btn.config(state=tk.NORMAL)
        self.is_converting = False
        
        gc.collect()
    
    def reset_interface(self):
        """reset the interface to allow for new image selection"""
        # clean up resources
        self.clean_image_references()
        
        # reset UI elements
        self.filename = None
        self.image_label.config(text="No image selected")
        self.preview_label.config(image="", text="Image preview will appear here")
        self.text_output.delete(1.0, tk.END)
        self.image_output.config(image="")
        self.show_drop_area()

        gc.collect()
    
    def on_closing(self):
        """handle window closing event"""
        # cancel any running conversion
        self.is_converting = False
        
        # cleanuup resources
        self.clean_image_references()
        
        # destroy the window
        self.root.destroy()

def main():
    # use TkinterDnD to enable drag and drop
    root = TkinterDnD.Tk()
    app = ASCIIArtConverterApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()