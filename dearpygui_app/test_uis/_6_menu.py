import dearpygui.dearpygui as dpg

class App:
    def __init__(self):
        self.windows = {}  # Store window states

    def toggle_window(self, window_name):
        """ Show or hide windows dynamically """
        if window_name in self.windows:
            is_visible = dpg.is_item_shown(self.windows[window_name])
            dpg.configure_item(self.windows[window_name], show=not is_visible)

    def setup(self):
        """ Create UI components and menu """
        dpg.create_viewport(title="Dynamic Windows", width=800, height=600)
        dpg.setup_dearpygui()
        dpg.show_viewport()

        # Menu Bar
        with dpg.viewport_menu_bar():
            with dpg.menu(label="View"):
                dpg.add_menu_item(label="Toggle Component A", callback=lambda: self.toggle_window("Component A"))
                dpg.add_menu_item(label="Toggle Component B", callback=lambda: self.toggle_window("Component B"))

        # Component A Window (Initially Hidden)
        with dpg.window(label="Component A", show=False) as win_a:
            dpg.add_text("This is Component A")
            dpg.add_button(label="Close", callback=lambda: dpg.configure_item(win_a, show=False))
        self.windows["Component A"] = win_a

        # Component B Window (Initially Hidden)
        with dpg.window(label="Component B", show=False) as win_b:
            dpg.add_text("This is Component B")
            dpg.add_button(label="Close", callback=lambda: dpg.configure_item(win_b, show=False))
        self.windows["Component B"] = win_b

    def run(self):
        """ Start the DPG UI loop """
        dpg.create_context()
        self.setup()
        dpg.start_dearpygui()
        dpg.destroy_context()


if __name__ == "__main__":
    app = App()
    app.run()
