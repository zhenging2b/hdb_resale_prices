import argparse
import geopandas
import pandas
from pathlib import Path

import pandas as pd
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("year", nargs="?", type=int, default=2025, choices=[2025, 2014])
args = parser.parse_args()
year = args.year

curr_dir = Path.cwd()
pd.set_option('display.max_columns', None)
DATA_DIR = curr_dir / "data"
if year == 2025:
    gdf_mrt_station = geopandas.read_file(DATA_DIR / "MasterPlan2025RailStationNameLayer.geojson")
elif year == 2014:
    gdf_mrt_station = geopandas.read_file(DATA_DIR / "MasterPlan2014RailStation.geojson")
    gdf_mrt_station[gdf_mrt_station["TYPE"].isin(["MRT", "CCL"])]
gdf_address = geopandas.read_file(DATA_DIR / "geocoded_addresses.csv").drop(columns="field_1")
gdf_address.replace("", np.nan, inplace=True)
gdf_address_nona = gdf_address.dropna(subset=["longitude", "latitude"]).reset_index(drop=True)
gdf_address_point = geopandas.GeoDataFrame(
    gdf_address_nona,
    geometry=geopandas.points_from_xy(gdf_address_nona["longitude"], gdf_address_nona["latitude"]),
    crs="EPSG:4326"
)

primary_school_gdf = geopandas.read_file(DATA_DIR / 'primary_school.geojson')
shopping_mall = pd.read_csv(DATA_DIR / "shopping_mall_coordinates.csv")
shopping_mall_gdf = geopandas.GeoDataFrame(
    shopping_mall, 
    geometry = geopandas.points_from_xy(shopping_mall["LONGITUDE"], shopping_mall["LATITUDE"]),
    crs="EPSG:4326"
)


shopping_mall_gdf = shopping_mall_gdf.to_crs(epsg=3414)
primary_school_gdf = primary_school_gdf.to_crs(epsg=3414)
gdf_address_point = gdf_address_point.to_crs(epsg=3414)
gdf_mrt_station = gdf_mrt_station.to_crs(epsg=3414)
popular_primary_school_gdf = primary_school_gdf[primary_school_gdf["popular"]].reset_index(drop=True)
if year ==2025:
    gdf_mrt_station.rename(columns={"TEXTSTRING": "Mrt Name"}, inplace=True)
elif year ==2014:
    gdf_mrt_station.rename(columns={"NAME": "Mrt Name"}, inplace=True)
popular_primary_school_gdf.rename(columns={"school_name":"popular school name"}, inplace=True)
gdf_address_point1 = gdf_address_point.sjoin_nearest(
    primary_school_gdf[["school_name", "geometry"]],
    how="left",
    distance_col="dist_to_school"
).drop(columns=['index_right'])

gdf_address_point2 = gdf_address_point1.sjoin_nearest(
    gdf_mrt_station[["Mrt Name", "geometry"]],
    how="left",
    distance_col="dist_to_MRT"
).drop(columns=['index_right'])

gdf_address_point3 = gdf_address_point2.sjoin_nearest(
    shopping_mall_gdf[["Mall Name", "geometry"]],
    how="left",
    distance_col="dist_to_Mall"
).drop(columns=['index_right'])

gdf_address_point4 = gdf_address_point3.sjoin_nearest(
    popular_primary_school_gdf[["popular school name", "geometry"]],
    how="left",
    distance_col="dist_to_pop_school"
).drop(columns=['index_right'])
gdf_address_point_final = gdf_address_point4[~gdf_address_point4.index.duplicated(keep='first')]

output_path = DATA_DIR / f"geo_addresses_with_poi_{year}.csv"
gdf_address_point_final.to_csv(output_path, index=False)
print(f"Saved to {output_path}")
