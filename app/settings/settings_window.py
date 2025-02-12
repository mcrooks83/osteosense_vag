from customtkinter import CTkToplevel, CTkLabel, CTkFrame, CTkSlider, CTkOptionMenu

class SettingsWindow(CTkToplevel):
    def __init__(self, master, settings, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.geometry("400x800")
        self.title("Settings")
        
        self.s = settings
        
        # Main container frame
        self.container = CTkFrame(self)
        self.container.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.container.columnconfigure(0, weight=1)
        
        # Section: Audio Settings
        self.audio_frame = CTkFrame(self.container)
        self.audio_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        CTkLabel(self.audio_frame, text="Audio Settings", font=("Monserrat", 14, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # Section Divider
        self.divider1 = CTkFrame(self.container, height=2)
        self.divider1.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        # Section: Filter Settings
        self.filter_frame = CTkFrame(self.container)
        self.filter_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        CTkLabel(self.filter_frame, text="Filter Settings", font=("Monserrat", 14, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # Low Cutoff Slider
        self.low_cutoff_label = CTkLabel(self.filter_frame, text="Low Cut off: 100 Hz")
        self.low_cutoff_label.grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.low_cutoff_slider = CTkSlider(self.filter_frame, from_=10, to=500, command=self.update_low_cutoff, number_of_steps=49)
        self.low_cutoff_slider.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        self.low_cutoff_slider.set(self.s.get_low_cut_off())
        
        # High Cutoff Slider
        self.high_cutoff_label = CTkLabel(self.filter_frame, text="High Cut off: 1000 Hz")
        self.high_cutoff_label.grid(row=3, column=0, padx=5, pady=2, sticky="w")
        self.high_cutoff_slider = CTkSlider(self.filter_frame, from_=500, to=2000, command=self.update_high_cutoff, number_of_steps=150)
        self.high_cutoff_slider.grid(row=4, column=0, padx=5, pady=5, sticky="ew")
        self.high_cutoff_slider.set(self.s.get_high_cut_off())

        # Filter Order Option Menu
        self.filter_order_label = CTkLabel(self.filter_frame, text="Filter Order:")
        self.filter_order_label.grid(row=5, column=0, padx=5, pady=2, sticky="w")
        self.filter_order_menu = CTkOptionMenu(self.filter_frame, values=["2", "4", "5", "6"], command=self.update_filter_order)
        self.filter_order_menu.grid(row=6, column=0, padx=5, pady=5, sticky="ew")
        self.filter_order_menu.set(self.s.get_filter_order())

        self.spectrogrma_frame = CTkFrame(self.container)
        self.spectrogrma_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=5)
        CTkLabel(self.spectrogrma_frame, text="Spectrogram Settings", font=("Monserrat", 14, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")

        
    def update_low_cutoff(self, value):
        self.low_cutoff_label.configure(text=f"Low Cutoff: {int(value)} Hz")
    
    def update_high_cutoff(self, value):
        self.high_cutoff_label.configure(text=f"High Cutoff: {int(value)} Hz")

    def update_filter_order(self, value):
        print(f"Selected Filter Order: {value}")
        self.s.set_filter_order(value)