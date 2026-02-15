import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext, messagebox
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageTk
import math
import os
import threading
import gc
import psutil
import numpy as np
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
        
        # setup traces for sliders
        self.setup_traces()
    
    def setup_traces(self):
        """Set up traces to update slider labels when values change"""
        self.scaleFactor.trace_add("write", lambda *args: self.update_slider_labels())
        self.brightness.trace_add("write", lambda *args: self.update_slider_labels())
        self.contrast.trace_add("write", lambda *args: self.update_slider_labels())
        self.saturation.trace_add("write", lambda *args: self.update_slider_labels())
        
        # Initial update
        self.update_slider_labels()

    def update_slider_labels(self):
        """Update the text labels showing current slider values"""
        if hasattr(self, 'scale_val_label'):
            self.scale_val_label.config(text=f"{self.scaleFactor.get():.2f}")
        if hasattr(self, 'brightness_val_label'):
            self.brightness_val_label.config(text=f"{self.brightness.get():.2f}")
        if hasattr(self, 'contrast_val_label'):
            self.contrast_val_label.config(text=f"{self.contrast.get():.2f}")
        if hasattr(self, 'saturation_val_label'):
            self.saturation_val_label.config(text=f"{self.saturation.get():.2f}")
    
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
        scale_label_frame = tk.Frame(advanced_frame, bg="#2d2d2d")
        scale_label_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
        tk.Label(scale_label_frame, text="Scale Factor:", fg="white", bg="#2d2d2d").pack(side=tk.LEFT)
        self.scale_val_label = tk.Label(scale_label_frame, text="0.10", fg="#aaaaaa", bg="#2d2d2d")
        self.scale_val_label.pack(side=tk.RIGHT)
        
        scale_slider = ttk.Scale(advanced_frame, from_=0.1, to=1.0, variable=self.scaleFactor, orient=tk.HORIZONTAL)
        scale_slider.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # brightness
        brightness_label_frame = tk.Frame(advanced_frame, bg="#2d2d2d")
        brightness_label_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
        tk.Label(brightness_label_frame, text="Brightness:", fg="white", bg="#2d2d2d").pack(side=tk.LEFT)
        self.brightness_val_label = tk.Label(brightness_label_frame, text="1.20", fg="#aaaaaa", bg="#2d2d2d")
        self.brightness_val_label.pack(side=tk.RIGHT)
        
        brightness_slider = ttk.Scale(advanced_frame, from_=0.5, to=2.0, variable=self.brightness, orient=tk.HORIZONTAL)
        brightness_slider.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # contrast
        contrast_label_frame = tk.Frame(advanced_frame, bg="#2d2d2d")
        contrast_label_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
        tk.Label(contrast_label_frame, text="Contrast:", fg="white", bg="#2d2d2d").pack(side=tk.LEFT)
        self.contrast_val_label = tk.Label(contrast_label_frame, text="1.30", fg="#aaaaaa", bg="#2d2d2d")
        self.contrast_val_label.pack(side=tk.RIGHT)
        
        contrast_slider = ttk.Scale(advanced_frame, from_=0.5, to=2.0, variable=self.contrast, orient=tk.HORIZONTAL)
        contrast_slider.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # saturation
        saturation_label_frame = tk.Frame(advanced_frame, bg="#2d2d2d")
        saturation_label_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
        tk.Label(saturation_label_frame, text="Saturation:", fg="white", bg="#2d2d2d").pack(side=tk.LEFT)
        self.saturation_val_label = tk.Label(saturation_label_frame, text="1.30", fg="#aaaaaa", bg="#2d2d2d")
        self.saturation_val_label.pack(side=tk.RIGHT)
        
        saturation_slider = ttk.Scale(advanced_frame, from_=0.5, to=2.0, variable=self.saturation, orient=tk.HORIZONTAL)
        saturation_slider.pack(fill=tk.X, padx=5, pady=(0, 10))
        
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
            
            # Convert to numpy array for faster processing
            im_np = np.array(im.convert('RGB'))
            
            # Calculate brightness (grayscale) using numpy
            # formula: 0.299 R + 0.587 G + 0.114 B (standard luminance)
            # here we use the app's previous simple average for consistency, or standard
            r, g, b = im_np[:,:,0], im_np[:,:,1], im_np[:,:,2]
            grayscale = (r.astype(np.uint16) + g.astype(np.uint16) + b.astype(np.uint16)) // 3
            
            # Map grayscale to ASCII characters using numpy indexing
            # interval = self.charLength / 256
            indices = (grayscale * self.interval).astype(np.int32)
            indices = np.clip(indices, 0, self.charLength - 1)
            
            # Create a character array from the map
            ascii_chars_np = np.array(self.charArray)
            char_mapped = ascii_chars_np[indices]
            
            # Output image creation
            output_image = Image.new('RGB', (self.oneCharWidth * width, self.oneCharHeight * height), color=(0, 0, 0))
            d = ImageDraw.Draw(output_image)
            
            # Optimization: Process per line for drawing and text file
            text_lines = []
            for i in range(height):
                line_chars = "".join(char_mapped[i])
                text_lines.append(line_chars)
                
                # Further optimization: Group consecutive characters with the same color
                # to reduce d.text calls.
                if width > 0:
                    j = 0
                    while j < width:
                        start_j = j
                        color = tuple(im_np[i, j])
                        # Find how many following characters have the same color
                        while j + 1 < width and tuple(im_np[i, j+1]) == color:
                            j += 1
                        
                        # Draw the group of characters
                        group_text = "".join(char_mapped[i, start_j:j+1])
                        d.text((start_j * self.oneCharWidth, i * self.oneCharHeight), group_text, font=fnt, fill=color)
                        j += 1
                
                # Check for cancellation
                if i % 50 == 0 and not self.is_converting:
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
            # close images and clear large numpy arrays
            im_np = None
            grayscale = None
            indices = None
            char_mapped = None
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