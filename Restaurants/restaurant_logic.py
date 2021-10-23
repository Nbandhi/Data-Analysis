import os
from os import path

import folium
from folium.plugins import HeatMap, MarkerCluster
from geojson_utils import centroid
import branca
from googlemaps import Client as GoogleMaps

import pandas as pd
import json

import restaurant_utility as util

google_api_key = ''
gmaps = GoogleMaps(google_api_key)

def get_string():
    return util.get_random_string()


def get_coordinates(address):
    """
    Get the coordinates of the city using google maps api
    :param address: address of the center of the city
    :return: latitue and longitude

    """
    #address = city + ", USA"
    geocode_result = gmaps.geocode(address)
    geographical_data = geocode_result[0]['geometry']['location']  # get geographical coordinates
    lat = geographical_data['lat']
    lon = geographical_data['lng']
    return [lat, lon]


def get_neigh_center(neighbourhood, city):
    """
    Get the latitude and longitude of the city center
    :param neighbourhood: Name of the neighbourhood
    :param city: Name of the city
    return lattiude and longitude as a list
    """
    neighFile = os.getcwd() + '/data/' + city + '/' + city +'_neighbourhood.json'
    with open(neighFile, 'rb') as f:
        df = json.load(f)
        locations = pd.json_normalize(df['data'])
    #neigh = locations.loc[locations['Neighbourhood Name'] == neighbourhood]
    lat = locations.loc[locations['Neighbourhood Name'] == neighbourhood, 'Latitude'].iloc[0]
    lon = locations.loc[locations['Neighbourhood Name'] == neighbourhood, 'Longitude'].iloc[0]
    center = [lat,lon]

    return center

def get_candidate_centers(center, city, neighbourhood=None):
    """
    Get the candidate area and cnters of each area around 6km from neigh_center
    : param center: The latitude and longitude of the neighbourhood
    : param city: The name of the city under consideration
    : param neighbourhood: The name of the neighbourhood (optional
    : return latitude, longitudes, distance from the center, xs ys, and htmlFile: the name of the file - folium map saved as an html
    """

    if neighbourhood is not None:
        util.create_directories(city, neighbourhood)
    else:
        util.create_directories(city)

    center_x, center_y = util.lonlat_to_xy(center[1], center[0])  # Neighbourhood center in Cartesian coordinates
    latitudes, longitudes, distances_from_center, xs, ys = util.get_latitudes_longitudes(center_x, center_y, neighbourhood)


    return latitudes, longitudes, distances_from_center, xs, ys



def get_candidate_addresses(cache, city, neighbourhood=None):
    """
    Get the address of the center of each candidate area
    :param cache: the cached information for each candidate area
    :param city: Name of the city
    :param neighbourhood: Name of the neighbourhood (optional)
    """
    addresses = []
    latitudes = cache['LATITUDES']
    longitudes = cache['LONGITUDES']

    for lat, lon in zip(latitudes, longitudes):
        address = util.get_address(gmaps, lat, lon)
        if address is None:
            address = 'NO ADDRESS'
        address = address.replace(', USA', '')  # We don't need country part of address
        addresses.append(address)

    df_locations = pd.DataFrame({'Address': addresses,
                                 'Latitude': cache['LATITUDES'],
                                 'Longitude': cache['LONGITUDES'],
                                 'X': cache['xs'],
                                 'Y': cache['ys'],
                                 'Distance from center': cache['DISTANCES']})

    locFile = 'candidates.json'
    if neighbourhood is not None:
        file_name = os.getcwd() + '/data/' + city + '/' + neighbourhood + '/' + locFile
    else:
        file_name = os.getcwd() + '/data/' + city + '/' + locFile

    df_locations.to_json(file_name, orient='table')

    return


def get_candidate_map(center, city, neighbourhood=None):
    locFile = 'candidates.json'
    htmlFile = 'candidate_areas.html'
    if neighbourhood is not None:
        candidateJson_file = os.getcwd() + '/data/' + city + '/' + neighbourhood + '/' + locFile
        candidateHtml_file = os.getcwd() + '/static/maps/' + city + '/' + neighbourhood + '/' + htmlFile
        radius = 150
        city_map = folium.Map(location=center, zoom_start=15)
    else:
        candidateJson_file = os.getcwd() + '/data/' + city + '/' + locFile
        candidateHtml_file = os.getcwd() + '/static/maps/' + city + '/' + htmlFile
        radius = 300
        city_map = folium.Map(location=center, zoom_start=13)

    with open(candidateJson_file, 'rb') as f:
        df = json.load(f)
        df_locations = pd.json_normalize(df['data'])


    folium.Marker(center).add_to(city_map)
    for idx, row in df_locations.iterrows():
        lat = row['Latitude']
        lon = row['Longitude']
        color = 'blue'
        html = util.map_candidate_popup(row)
        iframe = branca.element.IFrame(html=html, width=300, height=200)
        popup = folium.Popup(iframe, parse_html=True)
        folium.CircleMarker([lat, lon], radius=4, color=color, fill=True, fill_color=color, fill_opacity=1,
                            popup=popup).add_to(city_map)
        folium.Circle([lat, lon], radius=radius, color='green', fill=False).add_to(city_map)
        city_map.save(candidateHtml_file)

    return

def get_neighbourhood_restaurants(lats, lons):
    df_restaurants = util.get_restaurants(lats, lons)
    return df_restaurants

def get_neigh_map(city, restType, center, neighbourhood=None):
    if neighbourhood is not None:
        locFile = 'restaurants.json'
        restDataFile = os.getcwd() + '/data/' + city + '/' + neighbourhood + '/' + locFile
        htmlFile = restType + '.html'
        restHtmlFile = os.getcwd() + '/static/maps/' + city + '/' + neighbourhood + '/' + htmlFile
    else:
        locFile = 'restaurants.json'
        restDataFile = os.getcwd() + '/data/' + city + '/' + locFile
        htmlFile = restType + '.html'
        restHtmlFile = os.getcwd() + '/static/maps/' + city + '/' + htmlFile

    with open(restDataFile, 'rb') as f:
        df = json.load(f)
        df_restaurants = pd.json_normalize(df['data'])

    # Generate the restaurants map
    if not path.exists(restHtmlFile):
        if neighbourhood is not None:
            city_map = folium.Map(location=center, zoom_start=15)
        else:
            city_map = folium.Map(location=center, zoom_start=13)
        folium.Marker(center).add_to(city_map)
        for idx, row in df_restaurants.iterrows():
            lat = row['Venue Latitude']
            lon = row['Venue Longitude']
            color = 'red' if row['Type Of'] else 'blue'
            html = util.map_rest_popup(row)
            iframe = branca.element.IFrame(html=html, width=300, height=200)
            popup = folium.Popup(iframe, parse_html=True)
            folium.CircleMarker([lat, lon], radius=3, color=color, fill=True, fill_color=color, fill_opacity=1,
                                popup=popup).add_to(city_map)
        city_map.save(restHtmlFile)

    return

def get_heat_map(city, restType, center, neighbourhood=None):
    print(restType)
    if neighbourhood is not None:
        locFile = 'restaurants.json'
        restDataFile = os.getcwd() + '/data/' + city + '/' + neighbourhood + '/' + locFile
        htmlFile = restType + '_HeatMap.html'
        restHtmlFile = os.getcwd() + '/static/maps/' + city + '/' + neighbourhood + '/' + htmlFile
    else:
        locFile = 'restaurants.json'
        restDataFile = os.getcwd() + '/data/' + city + '/' + locFile
        htmlFile = restType + '_HeatMap.html'
        restHtmlFile = os.getcwd() + '/static/maps/' + city + '/' + htmlFile

    with open(restDataFile, 'rb') as f:
        df = json.load(f)
        df_restaurants = pd.json_normalize(df['data'])

    type_restaurants = df_restaurants[df_restaurants['Type Of'] == True]
    type_latlons = type_restaurants[['Venue Latitude', 'Venue Longitude']]

    geoFile = city + '_districts.geojson'
    geojsonFile = os.getcwd() + '/data/' + city + '/' + geoFile
    with open(geojsonFile, 'r') as f:
        df = json.load(f)
        df_districts = pd.json_normalize(df['features'])

    # Generate the restaurants map
    if not path.exists(restHtmlFile):
        if neighbourhood is not None:
            city_map = folium.Map(location=center, zoom_start=14)
            folium.Circle(center, radius=375, fill=False, color='white').add_to(city_map)
            folium.Circle(center, radius=750, fill=False, color='white').add_to(city_map)
            folium.Circle(center, radius=1500, fill=False, color='white').add_to(city_map)
        else:
            city_map = folium.Map(location=center, zoom_start=13)
            folium.Circle(center, radius=1000, fill=False, color='white').add_to(city_map)
            folium.Circle(center, radius=2000, fill=False, color='white').add_to(city_map)
            folium.Circle(center, radius=3000, fill=False, color='white').add_to(city_map)
        HeatMap(data=type_latlons).add_to(city_map)
        popup = folium.Popup('City Center', parse_html=True)
        folium.Marker(center, popup=popup, icon=folium.Icon(color='green', icon='info-sign')).add_to(city_map)
        for idx, row in df_districts.iterrows():
            try:
                box_str = '{"type": "Polygon","coordinates":' + str(row['geometry.coordinates']) + '}'
                box = json.loads(box_str)
                lon = centroid(box)['coordinates'][0]
                lat = centroid(box)['coordinates'][1]
                html = "<a href='/templates/restaurant-temp.html' target=>" + row['properties.NTAName'] + "</a>"
                popup = folium.Popup(html)
                folium.Marker([lat, lon], popup=popup).add_to(city_map)
            except:
                continue

        folium.GeoJson(df, style_function=util.boroughs_style, name='geojson').add_to(city_map)
        city_map.save(restHtmlFile)

    return
