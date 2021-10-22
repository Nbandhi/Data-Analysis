import os
from os import path
import math
import random
import string
from pyproj import Transformer

import requests
from requests.exceptions import HTTPError
import pandas as pd



# ID and KEY for Four Square API
foursquare_client_id = 'WLG2AFJIJUUYJXUWRRCBF4MXWNGUXAD3BTRR1VALEFPXM15M'
foursquare_client_secret = '14ICLYSBIB3RGLNQOQLFOUPCWBWJFYXWO1J30H35BULGUVK5'
version = '20180724'
food_category = '4d4b7105d754a06374d81259'


def get_random_string():
    letters = string.ascii_letters
    random_string = ''.join(random.choice(letters) for i in range(10))
    return random_string


def create_directories(city, neighbourhood=None):
    """
    Create the necessary folder under data and static to suppor the city
    :param city: The city being explored
    :param neighbourhood: Boolean to create a directory for the selected neighbourhood
    :return: True - if directories are created successfully

    """
    dest_folder = os.getcwd()
    if neighbourhood is not None:
        data_directory = dest_folder + '/data/' + city + '/' + neighbourhood
        map_directory = dest_folder + '/static/maps/' + city + '/' + neighbourhood
    else:
        data_directory = dest_folder + '/data/' + city
        map_directory = dest_folder + '/static/maps/' + city

    if not(path.exists(data_directory)):
        try:
            os.makedirs(data_directory)
        except OSError as error:
            return False

    if not (path.exists(map_directory)):
        try:
            os.makedirs(map_directory)
        except OSError as error:
            return False

    return True


def is_restaurant(category_name):
    """

    Identify restaurants of the type selected by the user
    :param category_name used to filter out fast foods, bakery type establishments
    :return: True if type of restaurant is the selected type

    """

    restaurant_words = ['restaurant', 'diner', 'taverna', 'steakhouse']
    restaurant = False
    for r in restaurant_words:
        if r in category_name.lower():
            restaurant = True
    if 'fast food' in category_name.lower():
        restaurant = False

    return restaurant

def get_categories(categories):
    return [(cat['name'], cat['id']) for cat in categories]


def format_address(location):
    address = ', '.join(location['formattedAddress'])
    address = address.replace(', NYC', '')
    address = address.replace(', USA', '')
    return address


def get_venues_near_location(lat, lon, category, client_id, client_secret, fs_version, radius, limit):
    """

    Get the restaurant information near the locoation of interest
    :param lat: The latitude of interest
    :param lon:  The longitude of interest
    :param category: The Four Square category for Food
    :param client_id: The Four Square client id
    :param client_secret: The Four Square client key
    :param fs_version: The Four Square API version
    :param radius: The radius of search
    :param limit: The number of results returned by Four Square API
    :return: A list of venues

    """

    url = 'https://api.foursquare.com/v2/venues/explore?client_id={}&client_secret={}&v={}&ll={},{}&categoryId={}&radius={}&limit={}'.format(
        client_id, client_secret, fs_version, lat, lon, category, radius, limit)


    try:
        results = requests.get(url).json()['response']['groups'][0]['items']
        venues = [(item['venue']['id'],
                   item['venue']['name'],
                   item['venue']['categories'][0]['id'],
                   item['venue']['categories'][0]['name'],
                   item['venue']['location']['lat'],
                   item['venue']['location']['lng'],
                   format_address(item['venue']['location']),
                   item['venue']['location']['distance']) for item in results]
    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
    except Exception as err:
        print(f'Other error occurred: {err}')
        venues = []
    return venues


def get_restaurants(lats, lons):
    """

    Get the list of restaurants for the various neighbourhoods to create a heat map to start with
    :param lats: latitiude of the center of the neighbourhood
    :param lons: longitude of the center of the neighbourhood
    :return: a data frame with the restaurants information

    """

    venue_ids = []
    venue_names = []
    venue_category_ids = []
    venue_category_names = []
    venue_latitudes = []
    venue_longitudes = []
    venue_addresses = []
    venue_distance = []
    venue_x = []
    venue_y = []
    candidate_lat = []
    candidate_lon = []


    for lat, lon in zip(lats, lons):
        # Using radius=300 and a limit of 250
        venues = get_venues_near_location(lat, lon, food_category, foursquare_client_id,
                                              foursquare_client_secret, version, radius=350, limit=250)

        if len(venues) > 0:
            for venue in venues:
                is_rest = is_restaurant(venue[3])
                if is_rest:
                    x, y = lonlat_to_xy(venue[5], venue[4])
                    venue_ids.append(venue[0])
                    venue_names.append(venue[1])
                    venue_category_ids.append(venue[2])
                    venue_category_names.append(venue[3])
                    venue_latitudes.append(venue[4])
                    venue_longitudes.append(venue[5])
                    venue_addresses.append(venue[6])
                    venue_distance.append(venue[7])
                    venue_x.append(x)
                    venue_y.append(y)
                    candidate_lat.append(lat)
                    candidate_lon.append(lon)
        else:
            print('No venues returned for')

    df_restaurants = pd.DataFrame({'Area Latitude': candidate_lat,
                                    'Area Longitude': candidate_lon,
                                    'Venue Id': venue_ids,
                                    'Venue Name': venue_names,
                                    'Venue Category Id': venue_category_ids,
                                    'Venue Category Name': venue_category_names,
                                    'Venue Address': venue_addresses,
                                    'Venue Latitude': venue_latitudes,
                                    'Venue Longitude': venue_longitudes,
                                    'Venue Distance': venue_distance,
                                    'Venue X': venue_x,
                                    'Venue Y': venue_y})


    return df_restaurants

def boroughs_style(feature):
    return {'color': 'blue', 'fill': False }


def map_rest_popup(row):
    left_col_colour = "#2A799C"
    right_col_colour = "#C5DCE7"
    name = row['Venue Name']
    address = row['Venue Address']

    html = """<!DOCTYPE html>
<html>

<head>
<h4 style="margin-bottom:0"; width="300px;">Restaurant</h4>
</head>
    <table style="height: 126px; width: 300px;">
    <tbody>
    <tr>
        <td style="background-color: """ + left_col_colour + """;"><span style="color: #ffffff;">Name</span></td>
        <td style="width: 200px;background-color: """ + right_col_colour + """;">{}</td>""".format(name) + """</tr><tr>
        <td style="background-color: """ + left_col_colour + """;""><span style="color: #ffffff;">Address</span></td>
        <td style="width: 200px;background-color: """ + right_col_colour + """;">{}</td>""".format(address) + """</tr>
</table>
</tbody></html>" """

    return html

def get_latitudes_longitudes(city_center_x, city_center_y, neighbourhood=None):
    if neighbourhood is not None:
        #print("Retrieving Neighbourhood lats and lons")
        k = math.sqrt(3) / 2  # Vertical offset for hexagonal grid cells
        x_min = city_center_x - 1000
        x_step = 300
        y_min = city_center_y - 1000 - (int(21 / k) * k * 300 - 2000) / 2
        y_step = 300 * k
        latitudes = []
        longitudes = []
        distances_from_center = []
        xs = []
        ys = []
        for i in range(0, int(21 / k)):
            y = y_min + i * y_step
            x_offset = 150 if i % 2 == 0 else 0
            for j in range(0, 21):
                x = x_min + j * x_step + x_offset
                distance_from_center = calc_xy_distance(city_center_x, city_center_y, x, y)
                if distance_from_center <= 1001:
                    lon, lat = xy_to_lonlat(x, y)
                    latitudes.append(lat)
                    longitudes.append(lon)
                    distances_from_center.append(distance_from_center)
                    xs.append(x)
                    ys.append(y)
    else:
        #print("Retrieving City lats and lons")
        k = math.sqrt(3) / 2  # Vertical offset for hexagonal grid cells
        x_min = city_center_x - 6000
        x_step = 600
        y_min = city_center_y - 6000 - (int(21 / k) * k * 600 - 12000) / 2
        y_step = 600 * k
        latitudes = []
        longitudes = []
        distances_from_center = []
        xs = []
        ys = []
        for i in range(0, int(21 / k)):
            y = y_min + i * y_step
            x_offset = 300 if i % 2 == 0 else 0
            for j in range(0, 21):
                x = x_min + j * x_step + x_offset
                distance_from_center = calc_xy_distance(city_center_x, city_center_y, x, y)
                if distance_from_center <= 6001:
                    lon, lat = xy_to_lonlat(x, y)
                    #print("Lat: {}, Lon: {}".format(lat, lon))
                    latitudes.append(lat)
                    longitudes.append(lon)
                    distances_from_center.append(distance_from_center)
                    xs.append(x)
                    ys.append(y)


    return latitudes, longitudes, distances_from_center, xs, ys

def lonlat_to_xy(lon, lat):
    transformer = Transformer.from_crs('epsg:4326','epsg:32618',always_xy=True)
    xy = transformer.transform(lon, lat)
    return xy[0], xy[1]

def xy_to_lonlat(x, y):
    transformer = Transformer.from_crs('epsg:32618','epsg:4326',always_xy=True)
    lonlat = transformer.transform(x,y)
    return lonlat[0], lonlat[1]

def calc_xy_distance(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    return math.sqrt(dx*dx + dy*dy)

def get_address(gmaps,lat, lon):
    reverse = gmaps.reverse_geocode((lat, lon))
    address = reverse[0]['formatted_address']
    return address


def map_candidate_popup(row):
    left_col_colour = "#2A799C"
    right_col_colour = "#C5DCE7"
    address = row['Address']
    distance = row['Distance from center']
    latitude = row['Latitude']
    longitude = row['Longitude']

    html = """<!DOCTYPE html>
<html>

<head>
<h4 style="margin-bottom:0"; width="300px;">Candidate Area</h4>
</head>
    <table style="height: 126px; width: 300px;">
    <tbody>
    <tr>
        <td style="background-color: """ + left_col_colour + """;"><span style="color: #ffffff;">Address</span></td>
        <td style="width: 200px;background-color: """ + right_col_colour + """;">{}</td>""".format(address) + """</tr><tr>
        <td style="background-color: """ + left_col_colour + """;""><span style="color: #ffffff;">Distance from center</span></td>
        <td style="width: 200px;background-color: """ + right_col_colour + """;">{:.2f}</td>""".format(distance) + """</tr>
        <tr>
        <td style="background-color: """ + left_col_colour + """;""><span style="color: #ffffff;">Latitude &amp; Longitude</span></td>
        <td style="width: 200px;background-color: """ + right_col_colour + """;">{}, {}</td>""".format(latitude, longitude) + """</tr>
</table>
</tbody></html>" """

    return html
