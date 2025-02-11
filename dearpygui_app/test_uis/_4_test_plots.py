import dearpygui.dearpygui as dpg
from math import sin, cos

dpg.create_context() # always the first thing

sindatax = [] # hold x axis data (can only have 1 of these)
sindatay = [] # hold y axis data (can have up to 3 of these)

# creates the signal (static)
for i in range(0, 500):
    sindatax.append(i/1000)
    sindatay.append(0.5 + 0.5*sin(50*i / 1000))

def update_series():
    cosdatax=[] 
    cosdatay=[] 
    for i in range(0,500): 
        cosdatax.append(i/1000) 
        cosdatay.append(0.5+0.5* cos(50*i/1000)) 
    dpg.set_value('series_tag',[cosdatax,cosdatay]) 
    dpg.set_item_label('series_tag',"0.5+0.5*cos(x)")

with dpg.window(label="Tutorial"):
    # add a button to the window to trigger a callback
    dpg.add_button(label="UpdateSeries", callback=update_series)
    with dpg.plot(label="line", height=400, width=600):
        
        dpg.add_plot_legend()
        dpg.add_plot_axis(dpg.mvXAxis, label="x")
        dpg.add_plot_axis(dpg.mvYAxis, label="y", tag="y_axis")

        #series belong to a yaxis  # a tag allows it to be found and updated
        dpg.add_line_series(sindatax,sindatay,label="0.5+0.5*sin(x)",parent="y_axis", tag="series_tag")

dpg.create_viewport(title='CustomTitle',width=800,height=600) 
dpg.setup_dearpygui() 
dpg.show_viewport() 
dpg.start_dearpygui() 
dpg.destroy_context()