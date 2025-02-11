import dearpygui.dearpygui as dpg

dpg.create_context()
dpg.configure_app(docking=True, docking_space=True) # must be called before create_viewport
dpg.create_viewport()
dpg.setup_dearpygui()

# generate IDs - the IDs are used by the init file, they must be the
#                same between sessions
left_window = dpg.generate_uuid()
right_window = dpg.generate_uuid()
top_window = dpg.generate_uuid()
bottom_window = dpg.generate_uuid()
center_window = dpg.generate_uuid()

dpg.add_window(label="Left", tag=left_window)
dpg.add_window(label="Right", tag=right_window)
dpg.add_window(label="Top", tag=top_window)
dpg.add_window(label="Bottom", tag=bottom_window)
dpg.add_window(label="Center", tag=center_window)

with dpg.window(label="Temporary Window"):
    dpg.add_button(label="Save Ini File", callback=lambda: dpg.save_init_file("custom_layout.ini"))


# main loop
dpg.show_viewport()
while dpg.is_dearpygui_running():
    dpg.render_dearpygui_frame()  

dpg.destroy_context()