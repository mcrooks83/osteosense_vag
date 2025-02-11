import dearpygui.dearpygui as dpg

dpg.create_context()

width = 800
height = 600

with dpg.window(label="Tabs Window", no_title_bar=False, no_collapse=False, no_move=False, width=width, height=height):  # Create a window container
            with dpg.group(horizontal=True):  # Create a group for horizontal layout
                with dpg.tab_bar():
                    with dpg.tab(label="Stream"):
                        with dpg.plot(label="Plot 1", width=width, height=300):
                                dpg.add_plot_legend()
                                x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="X Axis")
                                y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Y Axis")
                                x = [0, 1, 2]
                                y = [1, 2, 3]
                                dpg.add_line_series(x, y, label="Series 1", parent=y_axis)
                        with dpg.group(horizontal=False):  # Stack vertically
                            pass
                    with dpg.tab(label="Analyse"):
                        dpg.add_text("This is the content of Tab 2")

dpg.create_viewport(title='Custom Title', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()