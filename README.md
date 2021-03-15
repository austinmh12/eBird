# eBird
![license](https://img.shields.io/badge/license-GPL%203.0-brightgreen)

eBird is a tool to get bird names from hotspots in a coordinate region from [ebird](https://ebird.org/home, "eBird's website"). The tool parses through a list of coordinates and exports the data to a CSV file with the hotspot name and bird names.

# Requirements
ebird requires pandas, BeautifulSoup, and requests to retrieve and parse the data from eBird.org
They can be installed individually or via
```
pip install -r requirements.txt
```

# Usage
ebird comes with a default coordinate list and a default year (2010) to filter the data by. This default coordinate list is **rsc/coordList.csv**. The data it retrieves will be saved in the **results** folder.
```
ebird.py
```
You can pass a custom coordinate list (or modify the default one) and a custom year to filter by via
```
ebird.py -c path/to/coordlist.csv -y 2015
```

# Coordinate Lists
The coodinate list is a CSV file where each row is a pair of latitudes and longitudes. Coordinates in the list are the upper-right latitude, longitude, then the bottom-left latitude, longitude. These are labeled as Y2, X1, Y1, X2

![coord region](../rsc/EbirdHotspots.png)

## Obtaining Coordinates
The easiest way to obtain the coordinates is to use [google maps](https://www.google.com/maps, "Google Maps"). By going to the area that you want to get the data for and right-clicking, you can copy the coordinates in the LAT, LONG format that the coordinate list requires.

![coords from google](../rsc/GoogleMaps.png)