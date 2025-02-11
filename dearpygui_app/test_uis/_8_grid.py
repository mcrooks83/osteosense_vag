import dearpygui.dearpygui as dpg

# Grid settings
GRID_ROWS = 5
GRID_COLS = 5
MARGIN = 0  # No margin between grid cells, to start from edge of the viewport
graph_windows = []  # Store graph window IDs
grid_positions = []  # Store grid positions
cell_width, cell_height = 200, 200  # Default size, will be updated dynamically

def update_grid():
    """Update grid layout, resize windows, and redraw grid background."""
    global cell_width, cell_height, grid_positions

    # Get the current viewport size
    width, height = dpg.get_viewport_width(), dpg.get_viewport_height()

    # Compute new grid cell size to fully fill the screen (account for margins)
    cell_width = (width - (GRID_COLS - 1) * MARGIN) // GRID_COLS
    cell_height = (height - (GRID_ROWS - 1) * MARGIN) // GRID_ROWS

    # Compute new grid positions (grid layout)
    grid_positions = [
        (col * (cell_width + MARGIN), row * (cell_height + MARGIN))
        for row in range(GRID_ROWS) for col in range(GRID_COLS)
    ]

    # Move and resize graph windows
    for i, window in enumerate(graph_windows):
        if i < len(grid_positions):
            dpg.set_item_pos(window, grid_positions[i])
            dpg.set_item_width(window, cell_width)
            dpg.set_item_height(window, cell_height)

    # Redraw the grid background
    draw_grid()

def draw_grid():
    """Draws a grid background with properly aligned lines."""
    dpg.delete_item("grid_layer", children_only=True)  # Clear previous drawings

    # Get the current viewport size
    width, height = dpg.get_viewport_width(), dpg.get_viewport_height()

    with dpg.draw_layer(parent="grid_layer"):
        # Draw vertical lines (grid columns)
        for col in range(GRID_COLS + 1):
            x = col * (cell_width + MARGIN)  # Align grid lines properly
            dpg.draw_line((x, 0), (x, height), color=(200, 200, 200, 100), thickness=1)

        # Draw horizontal lines (grid rows)
        for row in range(GRID_ROWS + 1):
            y = row * (cell_height + MARGIN)  # Align grid lines properly
            dpg.draw_line((0, y), (width, y), color=(200, 200, 200, 100), thickness=1)

def snap_to_grid():
    """Snap all graph windows to the closest grid position when mouse is released."""
    for window in graph_windows:
        pos = dpg.get_item_pos(window)
        new_pos = min(grid_positions, key=lambda p: (p[0] - pos[0]) ** 2 + (p[1] - pos[1]) ** 2)
        dpg.set_item_pos(window, new_pos)

def on_resize():
    """Handles viewport resizing and updates the grid and window sizes."""
    update_grid()

# Create the Dear PyGui context
dpg.create_context()

# Setup viewport
dpg.create_viewport(title="5x5 Grid with Snapping", width=1000, height=800, resizable=True)
dpg.set_viewport_resize_callback(lambda sender, app_data: on_resize())

# Create a window for the background grid
with dpg.window(tag="grid_bg", no_collapse=True, no_move=True, no_bring_to_front_on_focus=True, no_background=True, no_title_bar=True):
    with dpg.drawlist(width=1000, height=800, tag="grid_layer"):
        pass  # The grid will be drawn dynamically here

# Create graph windows
for i in range(25):  # Create one window for each cell in the 5x5 grid
    with dpg.window(label=f"Graph {i+1}", tag=f"graph_{i+1}", no_collapse=True, no_title_bar=False):
        dpg.add_text(f"Graph {i+1}")
    
    graph_windows.append(f"graph_{i+1}")

# Add a handler to detect mouse release and snap windows to grid
with dpg.handler_registry():
    dpg.add_mouse_release_handler(callback=lambda: snap_to_grid())

# Setup Dear PyGui and show viewport
dpg.setup_dearpygui()
dpg.show_viewport()

# Initialize the grid after showing the viewport
update_grid()

# Start event loop
dpg.start_dearpygui()

# Clean up after closing
dpg.destroy_context()
