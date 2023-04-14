import base64
import datetime
import sqlite3
import time
import geopandas as gpd
import requests
from colorama import init, Fore, Style

# datetime
formatted_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
print(Fore.GREEN + "Started tracking script at:", formatted_datetime + Style.RESET_ALL)

# Initialize colorama
init()

# Load the GeoDataFrame
gdf = gpd.read_file("gadm41_BLR_shp/gadm41_BLR_0.shp")

# get the bounding box coordinates
bbox = gdf.total_bounds

# print the bounding box coordinates
print("Geographic boundary:", bbox)

# Extract the bounding box coordinates from the GeoDataFrame
lamin, lomin, lamax, lomax = bbox[1], bbox[0], bbox[3], bbox[2]

# Connect to SQLite3 database
conn = sqlite3.connect('aircraft_positions.db')
c = conn.cursor()

while True:
    # Make a request to retrieve all the flights within the bounding box
    params = {'lamin': lamin, 'lamax': lamax, 'lomin': lomin, 'lomax': lomax}
    # Belarus boundary
    url = f"https://opensky-network.org/api/states/all?lamin={lamin}&lomin={lomin}&lamax={lamax}&lomax={lomax}"

    auth_bytes = b'OPENSKYUSERNAME:OPENSKYPASSWORD'
    auth_b64_bytes = base64.b64encode(auth_bytes)
    auth_b64_str = auth_b64_bytes.decode('ascii')
    headers = {'Authorization': f'Basic {auth_b64_str}'}

    response = requests.get(url, params=params, headers=headers)

    # Check if the response is successful
    if response.status_code != 200:
        print(f"Failed to retrieve data: {response.text}")
        exit()

    # Extract the callsign and lat/lon coordinates for each aircraft in Belarus
    data = response.json()
    if data is not None:
        for aircraft in data["states"]:
            if aircraft[5] is not None and aircraft[6] is not None:
                icao24 = aircraft[0]
                callsign = aircraft[1]
                lat = aircraft[6]
                lon = aircraft[5]
                altitude = aircraft[7]
                point = gpd.points_from_xy([lon], [lat])
                point_in_gdf = gdf.contains(point[0])
                if point_in_gdf.any():
                    log_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    table_name = f"aircraft_{icao24}_"
                    c.execute(f"CREATE TABLE IF NOT EXISTS {table_name} "
                              "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                              "callsign TEXT, "
                              "time TEXT, "
                              "latitude REAL, "
                              "longitude REAL, "
                              "altitude REAL, "
                              "icao24 TEXT)")
                    c.execute(f"INSERT INTO {table_name} (callsign, time, latitude, longitude, altitude, icao24) "
                              "VALUES (?, ?, ?, ?, ?, ?)", (callsign, log_time, lat, lon, altitude, icao24))
                    conn.commit()
                    print(Fore.GREEN + f"Saved new data for: {icao24} | {callsign} at {log_time}" + Style.RESET_ALL)
    elif "error" in data:
        print(Fore.RED + f"Error: {data['error']}" + Style.RESET_ALL)
        exit()
    else:
        print(Fore.RED + "No data returned from API" + Style.RESET_ALL)
    # 2 mins wait because Opensky only gives 1000 API calls per day (get multiple accounts)
    time.sleep(120)
