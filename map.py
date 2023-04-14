import os
import random
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

# Load the GeoDataFrame
gdf = gpd.read_file("gadm41_BLR_shp/gadm41_BLR_0.shp")

# Create a list of all the CSV files containing flight data
data_dir = "data"
flight_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith(".csv")]

# Define a list of 20 distinct colors
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
          '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
          '#FF5733', '#33FF57', '#5733FF', '#FF33C7', '#FFB933',
          '#9F33FF', '#E7FF33', '#33FFE7', '#FF3333', '#33FFC4',
          '#1f4f99', '#e65c00', '#238c23', '#b30000', '#6a00b3',
          '#664d33', '#b32d8c', '#4d4d4d', '#8c8c00', '#008fb3',
          '#b37400', '#33b373', '#4c4cff', '#b30086', '#ffcc00',
          '#8040ff', '#00ffcc', '#ff4d4d', '#4dffcc', '#ffd9b3']

# Shuffle the list of colors
random.shuffle(colors)

# Create a dictionary to map each callsign to a unique color
color_dict = {}

# Plot each flight's position data as a line on a map
fig, ax = plt.subplots(figsize=(10, 10))
gdf.plot(ax=ax, color='lightgray', edgecolor='black')
ax.grid()  # Add grid lines
for file in flight_files:
    # Extract the callsign from the file name
    callsign = os.path.splitext(os.path.basename(file))[0]
    # Load the flight data into a pandas DataFrame
    df = pd.read_csv(file)
    # Assign a random color to each flight
    if callsign in color_dict:
        color = color_dict[callsign]
    else:
        color = colors[len(color_dict) % len(colors)]
        color_dict[callsign] = color
    ax.plot(df['Longitude'], df['Latitude'], color=color, linewidth=2, label=callsign)
ax.legend()
plt.savefig("flight_paths.png")
