import base64
import os
import geopandas as gpd
import pandas as pd
import requests
import time
import datetime

if not os.path.exists("data"):
    os.mkdir("data")
    print("Made data directory")

# datetime
formatted_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
print("Started tracking planes at:",formatted_datetime)

# Load the GeoDataFrame
gdf = gpd.read_file("gadm41_BLR_shp/gadm41_BLR_0.shp")

# get the bounding box coordinates
bbox = gdf.total_bounds

# print the bounding box coordinates
print(bbox)

# Extract the bounding box coordinates from the GeoDataFrame
lamin, lomin, lamax, lomax = bbox[1],bbox[0],bbox[3],bbox[2]

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
                    # Create a new CSV file for the callsign if it doesn't exist
                    filename = f"data/{callsign}.csv"
                    log_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    if not os.path.isfile(filename):
                        df = pd.DataFrame(columns=["Time", "Latitude", "Longitude", "Altitude"])
                        df.to_csv(filename, index=False)
                        new_row = {"Time": log_time, "Latitude": lat, "Longitude": lon, "Altitude": altitude}
                        df = df._append(new_row, ignore_index=True)
                        print(f"New plane detected:\nICAO24: {icao24}\nCallsign: {callsign}")
                    # Append new lat/lon data to the existing CSV file for the callsign
                    df = pd.read_csv(filename)
                    new_row = {"Time": log_time, "Latitude": lat, "Longitude": lon, "Altitude": altitude}
                    df = df._append(new_row, ignore_index=True)
                    df.to_csv(filename, index=False)
                    print(f"Saved new data for {icao24} at {log_time}")
    elif "error" in data:
        print(f"Error: {data['error']}")
        exit()
    else:
        print("No data returned from API")
    # 2 mins wait because Opensky only gives 1000 API calls per day (get multiple accounts)
    time.sleep(120)
