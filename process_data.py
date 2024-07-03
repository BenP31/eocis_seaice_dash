import os
import re

# import sys
from datetime import datetime
from glob import glob

import cartopy.crs as ccrs
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from netCDF4 import Dataset  # pylint:disable=no-name-in-module

# from scipy.ndimage import uniform_filter1d
from shapely.geometry import Point

file_years_re = re.compile("[0-9]{6}")

csv_columns = ["code", "period", "midpoint", "basin", "Raw SEC"]


def plot_arco_thickness(
    x,
    y,
    values,
):
    crs_new = ccrs.NorthPolarStereo(central_longitude=0)

    fig = plt.figure(figsize=(9, 7))
    ax = plt.axes(facecolor="white", projection=crs_new)

    ax.coastlines(resolution="110m", linewidth=0.5)

    gl = ax.gridlines(draw_labels=True, color="black", alpha=0.4, linestyle="dashed")
    ax.set_extent([-180, 180, 50, 90], crs=ccrs.PlateCarree())
    gl.ylabel_style = {
        "color": "black",
    }

    cs = ax.pcolormesh(
        x,
        y,
        values,
        vmax=3.5,
        vmin=0,
        cmap="Blues",
        transform=ccrs.Stereographic(
            central_latitude=90, central_longitude=-45, true_scale_latitude=70
        ),
        shading="gouraud",
    )
    fig.colorbar(cs, ax=ax)

    return fig


def get_data_files(folder: str):
    for f in sorted(glob(os.path.join(folder, "*.nc"))):
        yield f


def get_mean_data(gp_dataframe: gpd.GeoDataFrame) -> float:
    mean_thickness = gp_dataframe[gp_dataframe.notna()]["Thickness"].mean()
    return mean_thickness


def time_to_ts(time):
    start_of_year = datetime(year=int(time // 1), month=1, day=1)
    end_of_year = datetime(year=int(time // 1) + 1, month=1, day=1)
    seconds_in_year = (end_of_year - start_of_year).total_seconds()

    return datetime(year=int(time // 1), month=1, day=1).timestamp() + time % 1 * seconds_in_year


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser("EOCIS data processing script")
    parser.add_argument("-d", "--data_file_dir", help="Directory of input .nc files")
    parser.add_argument(
        "-p", "--processed_file_dir", help="Directory for processed files made here"
    )
    parser.add_argument(
        "-t", "--time_series_file", help="Path to the csv file containing the time series data"
    )

    argv = parser.parse_args()

    image_dir = argv.processed_file_dir
    data_file_dir = argv.data_file_dir
    time_series_file = argv.time_series_file

    image_files = glob("*.png", root_dir=image_dir)

    seaice_files = get_data_files(data_file_dir)

    crs = "epsg:3413"

    all_data = []

    try:
        for file_name in seaice_files:
            print("Processing ", file_name, end="", flush=True)

            years = file_years_re.findall(file_name)
            if len(years) == 0:
                continue
            file_year: str = years[0]
            # 199107-199607
            fmt_year = f"{file_year[0:4]}/{file_year[4:6]}"

            # load nc
            nc = Dataset(file_name)
            x_values = nc["xc"][:].data
            y_values = nc["yc"][:].data
            thickness = nc["sea_ice_thickness"][:].data[0, :, :]
            time_bounds = nc["time_bnds"][0, :]

            x_coords, y_coords = np.meshgrid(x_values, y_values, indexing="xy")
            coords_arr = [Point(x, y) for x, y in zip(x_coords.flatten(), y_coords.flatten())]

            # make dataframe here
            my_data = gpd.GeoDataFrame(
                data={
                    "Thickness": thickness.flatten(),
                    "geometry": coords_arr,
                },
                crs=crs,
            )

            ts_data = get_mean_data(my_data)
            midpoint = datetime.fromtimestamp(time_bounds[0] + time_bounds[1] / 2)

            all_data.append(
                {"code": file_year, "period": fmt_year, "midpoint": midpoint, "thickness": ts_data}
            )

            if file_year + ".png" not in image_files:
                # generate image and save in images folder
                fig = plot_arco_thickness(x_values, y_values, thickness)

                fig_file_path = os.path.join(image_dir, file_year + ".png")
                print(f"\nSaving figure to {fig_file_path}", end="")
                fig.savefig(fig_file_path)
                plt.close()

            print("")

    except KeyboardInterrupt as e:
        print("\nRecieved KeyboardInterrupt" + str(e))
    finally:
        # print all data to csv file
        # keyboard interrupt still writes all collected data
        df = pd.DataFrame(all_data)
        # df["Smooth SEC"] = np.zeros(len(df))
        # df["dH"] = np.zeros(len(df))

        # for basin_no in df["basin"].unique():
        #     basin_sec = df[df["basin"] == basin_no]["Raw SEC"]
        #     smooth_basins = uniform_filter1d(basin_sec, size=5)
        #     df.loc[df["basin"] == basin_no, "Smooth SEC"] = smooth_basins

        #     dh_values = np.zeros(len(basin_sec))

        #     for i in range(len(basin_sec)):
        #         dh_values[i] = np.trapz(basin_sec[: i + 1])

        #     df.loc[df["basin"] == basin_no, "dH"] = dh_values

        # df["Raw SEC"] = df["Raw SEC"].round(3)
        # df["Smooth SEC"] = df["Smooth SEC"].round(3)

        # save dataframe
        df.to_csv(time_series_file, sep=",")
