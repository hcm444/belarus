import sqlite3
import geopandas as gpd
import matplotlib.pyplot as plt

# Connect to the SQLite3 database
conn = sqlite3.connect('aircraft_positions.db')

# Load the GeoDataFrame containing the map
gdf = gpd.read_file("gadm41_BLR_shp/gadm41_BLR_0.shp")

# Set up the plot
fig, ax = plt.subplots(figsize=(10, 10))
gdf.plot(ax=ax, edgecolor='black', facecolor='none')

# Query the database for all tables that start with "aircraft_"
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'aircraft_%'")
tables = c.fetchall()

# Loop through each table and plot the flight route
for table in tables:
    table_name = table[0]
    c.execute(f"SELECT latitude, longitude FROM {table_name}")
    rows = c.fetchall()
    if len(rows) > 1:
        lats, lons = zip(*rows)
        ax.plot(lons, lats, label=table_name)

# Add a legend and title to the plot
ax.legend(loc='upper left')
ax.set_title('Flight Routes')

plt.savefig(f"map.png", dpi=300)
