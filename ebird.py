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
	:param: year (int) - Year to filter bird sightings by
	returns: None
	"""
	coord_list = pd.read_csv(coord_file)
	bird_data_rows = []
	missed_hotspots_coords = []
	for y2, x1, y1, x2 in coord_list.values.tolist():
		try:
			hotspots = get_hotspots(x1, y1, x2, y2)
		except Exception:
			missed_hotspots_coords.append((y2, x1, y1, x2))
			continue
		print(f'Total hotspots at {",".join([str(y2),str(x1),str(y1),str(x2)])}: {len(hotspots)}')
		bird_data = get_birds(hotspots, year)
		bird_data_rows.extend(bird_data)
	while missed_hotspots_coords:
		y2, x1, y1, x2 = missed_hotspots_coords[0]
		try:
			hotspots = get_hotspots(x1, y1, x2, y2)
		except Exception:
			print(f'Couldn\'t get hotspots for {",".join([str(y2),str(x1),str(y1),str(x2)])}')
			missed_hotspots_coords.pop()
			continue
		print(f'Total hotspots at {",".join([str(y2),str(x1),str(y1),str(x2)])}: {len(hotspots)}')
		bird_data = get_birds(hotspots)
		bird_data_rows.extend(bird_data)
		missed_hotspots_coords.pop()
	df = pd.DataFrame(bird_data_rows, columns=['Hotspot_Name', 'Bird_Name'])
	df.to_csv(f'results/bird_data-{dt.now().strftime("%Y%m%d")}.csv', index=False)


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
	:param: year (int) - The year to filter sighted birds by
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
		lis = soup.find_all(id=re.compile('has-det-\d*'))
		for li in lis:
			bird_name_div = li.find_next('div').find_next('div')
			bird_name = bird_name_div.span.string
			info_div = bird_name_div.find_next('div')
			date = list(info_div.stripped_strings)[2]
			if int(date[-4:]) >= 2010:
				ret.append((hotspot['n'], bird_name))
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
		lis = soup.find_all(id=re.compile('has-det-\d*'))
		for li in lis:
			bird_name_div = li.find_next('div').find_next('div')
			bird_name = bird_name_div.span.string
			info_div = bird_name_div.find_next('div')
			date = list(info_div.stripped_strings)[2]
			if int(date[-4:]) >= 2010:
				ret.append((missed[0]['n'], bird_name))
		missed.pop()
		sleep(.5)
	return ret

CMD = ArgumentParser()
CMD.add_argument('-c', '--coord-file', default='rsc/coordList.csv', help='Path to the coordinate CSV file')
CMD.add_argument('-y', '--year', default=2010, type=int, help='Date to filter bird sightings by')

if __name__ == '__main__':
	args = vars(CMD.parse_args())
	main(args['coord_file'], args['year'])