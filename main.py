import argparse
import gzip
import os
import re

import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage
import tilemapbase


tilemapbase.start_logging()
tilemapbase.init(create=True)
t = tilemapbase.tiles.build_OSM()


def unzip(src_name, dst_name):
    with gzip.open(src_name) as gfile:
        with open(dst_name, 'wb') as rawfile:
            rawfile.write(gfile.read())


def get_lat_lons(data, pattern, year=-1):
    """Returns a list of (lat, lons) contained in the given data."""
    points = []
    time_pattern = ".*[Tt]ime>[\\s]*([0-9]{4}).*"
    matched_year = year == -1
    for line in data.splitlines():
        if not matched_year:
            time_matches = re.match(time_pattern, line)
            if time_matches is not None:
                if int(time_matches[1]) == year:
                    matched_year = True
                else:
                    return []
        matches = re.match(pattern, line)
        if matches is not None:
            #match = matches[0]
            lat = float(matches[1])
            lon = float(matches[2])
            points.append((lat, lon))
    if matched_year:
        return points
    else:
        return []


def get_points_tcx(data, year=-1):
    pattern = '.*<Position><LatitudeDegrees>([-0-9.]+)</LatitudeDegrees><LongitudeDegrees>([-0-9.]+)</LongitudeDegrees></Position>.*'
    return get_lat_lons(data, pattern, year)


def get_points_gpx(data, year=-1):
    pattern = '[\\s]+<trkpt[\\s]+lat="([-0-9.]+)"[\\s]+lon="([-0-9.]+)">'
    return get_lat_lons(data, pattern, year)


def get_activity_filenames(path):
    activity_filenames = []
    for filename in next(os.walk(path))[2]:
        filename = os.path.join(path, filename)
        if filename.endswith('.gz'):
            dst_name = filename[:-3]
            unzip(filename, dst_name)
            filename = dst_name
        if filename.endswith(".tcx") or filename.endswith(".gpx"):
            activity_filenames.append(filename)

    return activity_filenames


def get_points(filename, year=-1):
    is_tcx = filename.endswith(".tcx")
    is_gpx = filename.endswith(".gpx")

    points = []
    if is_tcx or is_gpx:
        with open(filename, 'r') as infile:
            contents = infile.read()
        if is_tcx:
            points = get_points_tcx(contents, year)
        else:
            points = get_points_gpx(contents, year)

    return points


def get_points_in_range(act_fns, bl, tr, year=-1):
    xs = []
    ys = []
    for filename in act_fns:
        points = get_points(filename, year)
        if len(points) == 0:
            print("No points found in:", filename)
        else:
            for lat, lon in points:
            	x, y = tilemapbase.project(lon, lat)
            	if bl[0] <= lat <= tr[0] and bl[1] <= lon <= tr[1]:
            		xs.append(x)
            		ys.append(y)
    return xs, ys


def prep_map(bl, tr):
    extent = tilemapbase.Extent.from_lonlat(bl[1], tr[1], bl[0], tr[0])
    ax = plt.gca()
    plotter = tilemapbase.Plotter(extent, t, width=1200)
    plotter.plot(ax, t)
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    return extent


def bin_points(extent, xs, ys, pixels_x):
    min_x = extent.xmin
    max_x = extent.xmax
    min_y = extent.ymin
    max_y = extent.ymax
    span_y = max_y - min_y
    span_x = max_x - min_x
    pixels_y = int((span_y) / (span_x) * pixels_x) + 1
    grid = np.zeros((pixels_y, pixels_x))

    for i in range(len(xs)):
    	x = xs[i]
    	y = ys[i]
    	posx = int((x - min_x) / span_x * pixels_x)
    	posy = int((y - min_y) / span_y * pixels_y)
    	grid[min(posy, pixels_y-1), min(posx, pixels_x - 1)] += 1

    return grid, min_x, max_x, min_y, max_y


def blurred(grid, std):
    return ndimage.gaussian_filter(grid, std)


def get_range(grid, percentiles):
    return np.percentile(grid.reshape((-1,)), percentiles)


def main(args):
    path = args.path
    assert os.path.exists(path), "Invalid path: %s" % path

    bl = tuple(map(float, args.bl.strip().split(",")))
    tr = tuple(map(float, args.tr.strip().split(",")))

    extent = prep_map(bl, tr)
    act_fns = get_activity_filenames(path)
    xs, ys = get_points_in_range(act_fns, bl, tr, args.year)
    grid, min_x, max_x, min_y, max_y = bin_points(extent, xs, ys, args.width)
    grid = blurred(grid, 0.75)
    vmin, vmax = get_range(grid, [0, 90])
    if vmin == vmax:
        print("No two points fell in the same cell, use a coarser grid.")
        vmin = 0
        vmax = 1

    print("Number of points found:", len(xs))
    print("Single image coming up!")
    plt.imshow( grid, origin="lower", cmap="hot", vmin=vmin, vmax=vmax,
                extent=(min_x, max_x, min_y, max_y), alpha=0.45)

    plt.savefig("map.png", dpi=600, bbox_inches="tight")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=str, default=".",
                        help="path to an activities directory")
    parser.add_argument("-bl", type=str, nargs='?', default="-37.83,144.92",
                        help="lat,lon to use as the bottom left of output")
    parser.add_argument("-tr", type=str, nargs='?', default="-37.77, 145.01",
                        help="lat,lon to use as the top right of output")
    parser.add_argument("--year", type=int, nargs='?', default=-1,
                        help="the year for which data will be plotted")
    parser.add_argument("--width", type=int, nargs='?', default=400,
                        help="heatmap grid size in pixels")
    args = parser.parse_args()
    main(args)
