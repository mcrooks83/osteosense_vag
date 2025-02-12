from customtkinter import CTkToplevel, CTkLabel, CTkFrame, CTkSlider, CTkOptionMenu, CTkRadioButton, IntVar

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

        # Section: Protocol Settings
        self.protocol_frame = CTkFrame(self.container)
        self.protocol_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        CTkLabel(self.protocol_frame, text="Protocol Settings", font=("Monserrat", 14, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # Filter Order Option Menu
        self.cycle_label = CTkLabel(self.protocol_frame, text="Half cycle time:")
        self.cycle_label.grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.cycle_time_menu = CTkOptionMenu(self.protocol_frame, values=["2", "4", "8",], command=self.update_cycle_time)
        self.cycle_time_menu.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.cycle_time_menu.set(self.s.get_half_cycle_time())

        # Section Divider
        self.divider0 = CTkFrame(self.container, height=2)
        self.divider0.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        # Section: Audio Settings
        self.audio_frame = CTkFrame(self.container)
        self.audio_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        CTkLabel(self.audio_frame, text="Audio Settings", font=("Monserrat", 14, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")

         # Aduify/Sonify Radio Buttons
        self.audio_choice_label = CTkLabel(self.audio_frame, text="Audio Mode:", font=("Monserrat", 12))
        self.audio_choice_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        self.audio_mode_var = IntVar(value=self.s.get_audio_mode())

        self.sonify_radio = CTkRadioButton(self.audio_frame, text="Sonify", 
                                            font=("Montserrat", 14),
                                           variable=self.audio_mode_var, value=1, command=self.update_audio_mode)
        self.sonify_radio.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        
        self.aduify_radio = CTkRadioButton(self.audio_frame, text="Audify",
                                            font=("Montserrat", 14),
                                            variable=self.audio_mode_var, value=0, command=self.update_audio_mode)
        self.aduify_radio.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        
        # Section Divider
        self.divider1 = CTkFrame(self.container, height=2)
        self.divider1.grid(row=3, column=0, sticky="ew", padx=5, pady=5)
        
        # Section: Filter Settings
        self.filter_frame = CTkFrame(self.container)
        self.filter_frame.grid(row=4, column=0, sticky="ew", padx=5, pady=5)
        CTkLabel(self.filter_frame, text="Filter Settings", font=("Monserrat", 14, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # Low Cutoff Slider
        self.low_cutoff_label = CTkLabel(self.filter_frame, text=f"Low Cut off: {self.s.get_low_cut_off()} Hz")
        self.low_cutoff_label.grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.low_cutoff_slider = CTkSlider(self.filter_frame, from_=10, to=500, command=self.update_low_cutoff, number_of_steps=49)
        self.low_cutoff_slider.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        self.low_cutoff_slider.set(self.s.get_low_cut_off())
        
        # High Cutoff Slider
        self.high_cutoff_label = CTkLabel(self.filter_frame, text=f"High Cut off: {self.s.get_high_cut_off()} Hz")
        self.high_cutoff_label.grid(row=3, column=0, padx=5, pady=2, sticky="w")
        self.high_cutoff_slider = CTkSlider(self.filter_frame, from_=500, to=1000, command=self.update_high_cutoff, number_of_steps=150)
        self.high_cutoff_slider.grid(row=4, column=0, padx=5, pady=5, sticky="ew")
        self.high_cutoff_slider.set(self.s.get_high_cut_off())

        # Filter Order Option Menu
        self.filter_order_label = CTkLabel(self.filter_frame, text="Filter Order:")
        self.filter_order_label.grid(row=5, column=0, padx=5, pady=2, sticky="w")
        self.filter_order_menu = CTkOptionMenu(self.filter_frame, values=["2", "4", "5", "6"], command=self.update_filter_order)
        self.filter_order_menu.grid(row=5, column=1, padx=5, pady=5, sticky="ew")
        self.filter_order_menu.set(self.s.get_filter_order())

        # Section Divider
        self.divider2 = CTkFrame(self.container, height=2)
        self.divider2.grid(row=5, column=0, sticky="ew", padx=5, pady=5)

        """
        self.spectrogrma_frame = CTkFrame(self.container)
        self.spectrogrma_frame.grid(row=6, column=0, sticky="ew", padx=5, pady=5)
        CTkLabel(self.spectrogrma_frame, text="Spectrogram Settings", font=("Monserrat", 14, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        """
    def update_low_cutoff(self, value):
        self.low_cutoff_label.configure(text=f"Low Cutoff: {int(value)} Hz")
        self.s.set_low_cut_off(value)
    
    def update_high_cutoff(self, value):
        self.high_cutoff_label.configure(text=f"High Cutoff: {int(value)} Hz")
        self.s.set_high_cut_off(value)

    def update_filter_order(self, value):
        self.s.set_filter_order(value)

    def update_cycle_time(self, value):
        self.s.set_half_cycle_time(value)

    def update_audio_mode(self):
        audio_mode = self.audio_mode_var.get()
        print(f"Selected Audio Mode: {audio_mode}")
        self.s.set_audio_mode(audio_mode)