the_big_plot.py = used a function to find the average, median, and Standard deviation of each unique sensor that counts PM10. The data was then created in Clean_PlotData.csv
(not being used in project) tellus_PM10_sensor_frame.py = was my first attempt to find all of the locations for sensors and map them. this created the masterframe.csv
(not being used in project) plotting.py = was my first attempt to map out all unique sensors. uses the masterframe.csv
six_maps.py = this is the maps of the 6 seasons of data I have using Clean_PlotData.csv. I also plan on using contourf to make those maps look a lot more like a heat map, but first need to adapt it into a 2D array, currently it's in a 1D array.
six_maps_in_jup.ipynb = This is a replica of six_maps.py but in jupiter, I used this to test some code that I don't want added into the main file and also to have the maps to directly compare in the code.
La_graphs.py = is my city comparable graphs from the data of the last two years. This is my pride, joy, and headache. My goal with this is to find spikes in each city and use the code from my six_maps.py to create a heat map of the anomolies. 
la_graphs_in_jup.ipynb = This is a replica of La_graphs.py but in jupiter, I used this to test some code that I don't want added into the main file and also to have the graphs to directly compare in the code.
(not being used in project) finding_sensors.py = this was an attempt to reverse geo to find all of the sensors in their uniqe city.
