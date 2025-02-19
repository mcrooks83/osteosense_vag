from customtkinter import CTkFrame, CTkLabel, CTkImage
from PIL import Image


class Footer(CTkFrame):
    def __init__(self, master, logo1_path, logo2_path, logo3_path,  *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.configure(height=50, fg_color="gray90")
        self.grid(row=2, column=0, sticky='nsew')

        # Center everything horizontally
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Content frame centered in footer
        content_frame = CTkFrame(self, fg_color="transparent")
        content_frame.grid(row=0, column=0)
        content_frame.grid_columnconfigure((0, 1, 2), weight=0)
        content_frame.grid_rowconfigure(0, weight=1)

        # Load logos
        logo1_image = CTkImage(Image.open(logo1_path), size=(95, 20))
        logo2_image = CTkImage(Image.open(logo2_path), size=(30, 20))
        logo3_image = CTkImage(Image.open(logo3_path), size=(15,15) )

        # First logo (bottom aligned)
        logo1_label = CTkLabel(content_frame, image=logo1_image, text="")
        logo1_label.grid(row=0, column=0, sticky="sn", padx=10)

        # Thin vertical divider (not a large frame)
        divider = CTkLabel(content_frame, image=logo3_image, height=20, text="", )
        divider.grid(row=0, column=1, sticky="sn", padx=10)  # Small gap

        # Second logo (bottom aligned)
        logo2_label = CTkLabel(content_frame, image=logo2_image, text="")
        logo2_label.grid(row=0, column=2, sticky="sn", padx=10)
