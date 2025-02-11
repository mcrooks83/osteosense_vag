import dearpygui.dearpygui as dpg

class ComponentA:
    def __init__(self):
        self.window = None

    def create(self):
        with dpg.window(label="Component A", width=300, height=200) as self.window:
            dpg.add_text("This is Component A")
            dpg.add_button(label="Click Me", callback=self.on_button_click)

    def on_button_click(self, sender, app_data):
        dpg.set_value("status_text", "Button in Component A clicked!")

class ComponentB:
    def __init__(self):
        self.window = None

    def create(self, screen_width):
        """ Create window using dynamic position """
        with dpg.window(label="Component B", width=300, height=200, pos=(screen_width // 2, 0)) as self.window:
            dpg.add_text("This is Component B")
            dpg.add_input_text(label="Enter something")

class App:
    def __init__(self):
        self.components = []

    def setup(self):
        """ Initialize and display all components dynamically """
        dpg.create_viewport(title="My DPG App", resizable=True)  # Allow resizing
        dpg.maximize_viewport()  # Fullscreen the viewport

        dpg.setup_dearpygui()
        dpg.show_viewport()

        # Now get fullscreen size
        screen_width = dpg.get_viewport_width()
        screen_height = dpg.get_viewport_height()

        component_a = ComponentA()
        component_b = ComponentB()

        self.components.extend([component_a, component_b])

        component_a.create()
        component_b.create(screen_width)

        # Global UI elements
        with dpg.window(label="Status", width=300, height=100, pos=(screen_width // 4, screen_height - 120)):
            dpg.add_text("", tag="status_text")

    def run(self):
        """ Start the DPG UI loop """
        dpg.create_context()
        self.setup()
        dpg.start_dearpygui()
        dpg.destroy_context()


# Run the app
if __name__ == "__main__":
    app = App()
    app.run()
