import dearpygui.dearpygui as dpg
import dearpygui_grid as dpg_grid


dpg.create_context()
dpg.setup_dearpygui()
dpg.create_viewport()
dpg.show_viewport()

window = dpg.add_window(width=400, height=400)

grid = dpg_grid.Grid(3, 3, window)
# Can optionally be applied per component, as `grid.offsets[i] = ...`
grid.offsets = 8, 18 + 8, 8, 8

grid.push(dpg.add_button(parent=window), 1, 0)  # middle col, top row
grid.push(dpg.add_button(parent=window), 0, 1)  # left col, middle row
grid.push(dpg.add_button(parent=window), 1, 1)  # middle col, middle row
grid.push(dpg.add_button(parent=window), 2, 1)  # right col, middle row
grid.push(dpg.add_button(parent=window), 1, 2)  # middle col, bottom row

with dpg.item_handler_registry() as window_hr:
    dpg.add_item_visible_handler(callback=grid)
dpg.bind_item_handler_registry(window, window_hr)

dpg.start_dearpygui()