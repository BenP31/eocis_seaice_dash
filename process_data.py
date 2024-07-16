import os
import re

# import sys
from datetime import datetime
from glob import glob

import cartopy
import cartopy.crs as ccrs
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from netCDF4 import Dataset  # pylint:disable=no-name-in-module

file_years_re = re.compile("[0-9]{6}")

month_key = {
    "10": {"month": 0, "winter_year": 0},
    "11": {"month": 1, "winter_year": 0},
    "12": {"month": 2, "winter_year": 0},
    "01": {"month": 3, "winter_year": 1},
    "02": {"month": 4, "winter_year": 1},
    "03": {"month": 5, "winter_year": 1},
    "04": {"month": 6, "winter_year": 1},
}


def plot_arco_thickness(x, y, values):
    crs_new = ccrs.NorthPolarStereo(central_longitude=0)

    fig = plt.figure(figsize=(9, 7))
    ax = plt.axes(facecolor="whitesmoke", projection=crs_new)

    ax.coastlines(resolution="110m", linewidth=0.5)

    gl = ax.gridlines(draw_labels=True, color="black", alpha=0.4, linestyle="dashed", linewidth=0.5)
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
    ax.add_feature(cartopy.feature.LAND, color="gainsboro", zorder=1)
    fig.colorbar(cs, ax=ax)

    return fig


def get_data_files(folder: str):
    for f in sorted(glob(os.path.join(folder, "*.nc"))):
        yield f


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
        "-x", "--aux_file_dir", help="Directory where auxiliary files are kept (shapefiles, ...)"
    )

    argv = parser.parse_args()

    image_dir = os.path.join(argv.processed_file_dir, "images")
    data_file_dir = argv.data_file_dir
    time_series_file = os.path.join(argv.processed_file_dir, "time_series_data.csv")
    aux_file_dir = argv.aux_file_dir

    image_files = glob("*.png", root_dir=image_dir)

    seaice_files = get_data_files(data_file_dir)

    all_data = []

    arctic_regions = gpd.read_file(
        os.path.join(aux_file_dir, "our_arctic_regions", "arctic_regions.shp")
    )

    for file_name in seaice_files:
        print("Processing ", file_name, flush=True)

        file_dates_search = file_years_re.findall(file_name)
        if len(file_dates_search) == 0:
            continue
        file_date: str = file_dates_search[0]
        # 199107-199607
        file_year = file_date[0:4]
        file_month = file_date[4:6]
        fmt_year = f"{file_year}/{file_month}"

        # load nc
        nc = Dataset(file_name)
        x_values = nc["xc"][:].data
        y_values = nc["yc"][:].data
        thickness = nc["sea_ice_thickness"][:].data[0, :, :]
        time_bounds = nc["time_bnds"][0, :]

        mean_thickness = np.nanmean(thickness)

        midpoint = datetime.fromtimestamp((time_bounds[0] + time_bounds[1]) / 2)

        all_data.append(
            {
                "code": file_date,
                "year": file_year,
                "season_year": int(file_year) - month_key[str(file_month)]["winter_year"],
                "month": midpoint.strftime("%B"),
                "region": "Arctic",
                "thickness": mean_thickness,
            }
        )

        if file_date + ".png" not in image_files:
            # generate image and save in images folder
            fig = plot_arco_thickness(x_values, y_values, thickness)

            fig_file_path = os.path.join(image_dir, file_date + ".png")
            print(f"Saving figure to {fig_file_path}")
            fig.savefig(fig_file_path)
            plt.close()

    # print all data to csv file
    # keyboard interrupt still writes all collected data
    df = pd.DataFrame(all_data)

    # save dataframe
    df.to_csv(time_series_file, sep=",", index=False)
