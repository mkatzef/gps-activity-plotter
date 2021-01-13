# GPS Activity Plotter
Generate heatmaps of your .tcx and .gpx files!

## Requirements
This tool requires `python3` and the following standard packages:
* `numpy`
* `scipy`
* `matplotlib`

Along with the following 3rd-party tool:
* [`TileMapBase`](https://github.com/MatthewDaws/TileMapBase)

## Usage
This tool may be run as
`$ py main.py --path=<path to activities>`
Where `<path to activities>` is the path to a directory containing (possibly gzipped) .tcx and .gpx files.

Additional command line arguments allow you to specify coordinates, grid resolution, and year for the plotted data.

## Acknowledgements
Written by [Marc Katzef](https://www.github.com/mkatzef)
Using packages from:
* [Matthew Daws](https://github.com/MatthewDaws)
