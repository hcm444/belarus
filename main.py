import base64
import datetime
import sqlite3
import time
import geopandas as gpd
import requests


class FlightTracker:
    def __init__(self, boundary_file, db_file, auth_user, auth_pass):
        self.gdf = gpd.read_file(boundary_file)
        self.bbox = self.gdf.total_bounds
        self.conn = sqlite3.connect(db_file)
        self.c = self.conn.cursor()
        self.auth = (auth_user, auth_pass)

    def get_aircraft_data(self):
        url = f"https://opensky-network.org/api/states/all?lamin={self.bbox[1]}&lomin={self.bbox[0]}&lamax={self.bbox[3]}&lomax={self.bbox[2]}"
        headers = {'Authorization': 'Basic ' + base64.b64encode(f"{self.auth[0]}:{self.auth[1]}".encode()).decode()}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to retrieve data: {response.text}")
            return
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
                    point_in_gdf = self.gdf.contains(point[0])
                    if point_in_gdf.any():
                        log_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        table_name = f"aircraft_{icao24}_"
                        self.c.execute(f"CREATE TABLE IF NOT EXISTS {table_name} "
                                       "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                                       "callsign TEXT, "
                                       "time TEXT, "
                                       "latitude REAL, "
                                       "longitude REAL, "
                                       "altitude REAL, "
                                       "icao24 TEXT)")
                        self.c.execute(
                            f"INSERT INTO {table_name} (callsign, time, latitude, longitude, altitude, icao24) "
                            "VALUES (?, ?, ?, ?, ?, ?)", (callsign, log_time, lat, lon, altitude, icao24))
                        self.conn.commit()
                        print(f"Saved new data for: {icao24} | {callsign} at {log_time}")
        elif "error" in data:
            print(f"Error: {data['error']}")
        else:
            print("No data returned from API")

    def run(self, interval=120):
        while True:
            self.get_aircraft_data()
            time.sleep(interval)


if __name__ == "__main__":
    tracker = FlightTracker("gadm41_BLR_shp/gadm41_BLR_0.shp", "aircraft_positions.db", "OPENSKYUSERNAME", "OPENSKYPASSWORD")
    tracker.run()
