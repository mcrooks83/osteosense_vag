import dearpygui.dearpygui as dpg


# doesnt work

# Grid settings
GRID_ROWS = 5
GRID_COLS = 5

# Function to draw the grid
def draw_grid():
    """Draw the grid lines from the very edge of the viewport."""
    # Get current width and height of the viewport
    width, height = dpg.get_viewport_width(), dpg.get_viewport_height()

    # Calculate the size of each grid cell
    cell_width = width // GRID_COLS
    cell_height = height // GRID_ROWS

    # Add a drawlist to draw the grid on the background
    with dpg.drawlist(width=width, height=height, parent=dpg.add_window(tag="Background Grid", no_move=True, no_background=True, no_title_bar=True)):
        # Draw vertical lines (grid columns)
        for col in range(GRID_COLS + 1):
            x = col * cell_width
            dpg.draw_line((x, 0), (x, height), color=(200, 200, 200, 100), thickness=1)

        # Draw horizontal lines (grid rows)
        for row in range(GRID_ROWS + 1):
            y = row * cell_height
            dpg.draw_line((0, y), (width, y), color=(200, 200, 200, 100), thickness=1)

# Function to update grid when the window is resized
def update_grid_on_resize(sender, app_data):
    """Callback function to update the grid layout and redraw when the window is resized."""
    # Clear the old grid before redrawing
    dpg.delete_item("Background Grid",)
    draw_grid()  # Redraw the grid with new dimensions

# Create the Dear PyGui context
dpg.create_context()

# Setup viewport for the application
dpg.create_viewport(title="5x5 Grid", width=1000, height=800, resizable=True)

# Add a handler for resizing the window to update grid
dpg.set_viewport_resize_callback(update_grid_on_resize)


# Draw the grid for the first time
draw_grid()

# Setup Dear PyGui and show the viewport
dpg.setup_dearpygui()
dpg.show_viewport()

# Start the Dear PyGui event loop
dpg.start_dearpygui()

# Cleanup after closing
dpg.destroy_context()
