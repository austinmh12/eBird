from argparse import ArgumentParser
from bs4 import BeautifulSoup as Soup
from datetime import datetime as dt, timedelta as td
from time import sleep
import json
import pandas as pd
import re
import requests as r

def main(coord_file, year):
	"""Gets the bird data at each hotspot area in the coordinate file for the given year or newer,
	retrying each missed coordinate once. Saves to a CSV file in the results folder.
	:param: coord_file (str) - File path of the coordinate list CSV
	:param: year (int) - Year to filter bird sightings by, passed to parse_bird_data
	returns: None
	"""
	coord_list = pd.read_csv(coord_file)
	bird_data_rows, missed_hotspots_coords = get_data(coord_list.values.tolist(), year)
	if missed_hotspots_coords:
		missed_bird_data, missed_hotspots_coords_twice = get_data(missed_hotspots_coords, year)
		bird_data_rows.extend(missed_bird_data)
		if missed_hotspots_coords_twice:
			for y2, x1, y1, x2 in missed_hotspots_coords_twice:
				print(f'Couldn\'t get hotspots for {",".join([str(y2),str(x1),str(y1),str(x2)])}')
	print(bird_data_rows)
	df = pd.DataFrame(bird_data_rows, columns=['Hotspot_Name', 'Bird_Name'])
	df.to_csv(f'results/bird_data-{dt.now().strftime("%Y%m%d%H%M%S")}.csv', index=False)

def get_data(coords, year):
	"""Function that gets all the hotspots for a given set of coordinates.
	:param: coords (list) - List of coordinate pairs to get bird data from
	:param: year (int) - Year to filter bird sightings by, passed to parse_bird_data
	returns: [bird_data, missed_coordinates]
	"""
	data = []
	missed = []
	for y2, x1, y1, x2 in coords:
		try:
			hotspots = get_hotspots(x1, y1, x2, y2)
		except Exception:
			missed.append((y2, x1, y1, x2))
			continue
		print(f'Total hotspots at {",".join([str(y2),str(x1),str(y1),str(x2)])}: {len(hotspots)}')
		bird_data = get_birds(hotspots, year)
		data.extend(bird_data)
	return data, missed

def get_hotspots(x1, y1, x2, y2):
	"""Gets the hotspots from the ebird website
	:param: x1 (str or float) - The left longitude
	:param: y1 (str or float) - The lower latitude
	:param: x2 (str or float) - The right longitude
	:param: y2 (str or float) - The upper latitude
	returns: list(dict)
	"""
	url = f'https://ebird.org/mapServices/genHsForWindow.do?maxY={str(y2).ljust(16, "0")}&maxX={str(x2).ljust(16, "0")}&minY={str(y1).ljust(16, "0")}&minX={str(x1).ljust(16, "0")}&yr=all&m='
	resp = r.get(url)
	return resp.json()

def get_birds(hotspots, year):
	"""Retrieves the list of sighted birds from each hotspot passed, filtering by the
	year passed. Retries each missed hotspot once.
	:param: hotspots (list(dict)) - The list of hotspots to get the bird data from
	:param: year (int) - The year to filter sighted birds by, passed to parse_bird_data
	returns: list(tuple)
	"""
	missed = []
	ret = []
	for hotspot in hotspots:
		try:
			resp = r.get(f'https://ebird.org/hotspot/{hotspot["l"]}')
			soup = Soup(resp.content, 'html.parser')
		except Exception:
			missed.append(hotspot)
			sleep(.5)
			continue
		birds = parse_bird_data(soup, year)
		if birds:
			ret.extend([(hotspot['n'], bird) for bird in birds])
		sleep(.5)
	while missed:
		try:
			resp = r.get(f'https://ebird.org/hotspot/{missed[0]["l"]}')
			soup = Soup(resp.content, 'html.parser')
		except Exception:
			print(f'Unable to get data for {missed[0]["n"]}')
			missed.pop()
			sleep(.5)
			continue
		birds = parse_bird_data(soup, year)
		if birds:
			ret.extend([(hotspot['n'], bird) for bird in birds])
		missed.pop()
		sleep(.5)
	return ret

def parse_bird_data(html, year):
	"""Parses the html from eBird for the hotspot into a list of bird names,
	filtering out hybrids and unspecific bird species, as well as sighting year.
	:param: html (BeautifulSoup) - HTML of the hotspot page
	:param: year (int) - Year to filter sightings by.
	returns: list(str)
	"""
	ret = []
	lis = html.find_all(id=re.compile('has-det-\d*'))
	for li in lis:
		bird_name_div = li.find_next('div').find_next('div')
		bird_name = bird_name_div.span.string
		if re.match(r'.* x .*', bird_name): # Filtering hybrids (bird x bird)
			continue
		if re.match(r'.*(/|\(|sp\.).*', bird_name): # Filtering Bird/Bird, Bird sp., and Bird (hybrid)
			continue
		info_div = bird_name_div.find_next('div')
		date = list(info_div.stripped_strings)[2]
		if int(date[-4:]) >= year:
			ret.append(bird_name)
	return ret

CMD = ArgumentParser()
CMD.add_argument('-c', '--coord-file', default='rsc/coordList.csv', help='Path to the coordinate CSV file')
CMD.add_argument('-y', '--year', default=2010, type=int, help='Date to filter bird sightings by')

if __name__ == '__main__':
	args = vars(CMD.parse_args())
	main(args['coord_file'], args['year'])