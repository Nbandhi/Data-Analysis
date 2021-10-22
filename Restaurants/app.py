# Application to explore areas to build or open a new restaurant
from flask import Flask, render_template, request, session

import os
from os import path
import json

import pandas as pd

import restaurant_logic as logic
import restaurant_utility as util
import foursquare as fs

app = Flask(__name__)

app.secret_key = logic.get_string()
cache = {}

errors = []


@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/comingsoon')
def comingsoon():
    return render_template('comingsoon.html')


@app.route('/restaurant_home')
def restaurant_home():
    """
       Display the starting page for restaurant application
       :param
       :return: the restaurant home page

    """
    file_name = os.getcwd() + '/data/rest_type.csv'
    df = pd.read_csv(file_name)
    typeList = sorted(df.rest_type)
    return render_template('restaurant_home.html', typeList=typeList)


@app.route('/explore_neighbourhood', methods=['GET', 'POST'])
def explore_neighbourhood():
    """
       Get the neighbourhoods that are considered for exploration.
       Save data in the sessions object
       :param
       :return: the page to display the map of the neighbourhoods under
                consideration for exploration and list of 10 addresses

       """
    errors = []
    locFile = 'candidates.json' # File to store the details of the neighbourhoods under consideration
    htmlFile = 'candidate_areas.html' # Map of the neighbourhoods under consideration
    if request.method == "POST":
        # get info that the user entered
        dict = request.form
        try:
            if 'neighbourhood' in dict.keys():
                neighbourhood = request.form['neighbourhood'].replace('%20',' ')
                session['neighbourhood'] = neighbourhood
                candidateJson_file = os.getcwd() + '/data/' + session['city'] + '/' + \
                                    session['neighbourhood'] + '/' + locFile
                candidateHtml_file = 'maps/' + session['city'] + '/' + session['neighbourhood'] + '/' + htmlFile
                neighbourhood_selected = True

            else:
                city = request.form['city']
                typeRest = request.form['typeRest'].replace('%20',' ')
                session['city'] = city
                candidateJson_file = os.getcwd() + '/data/' + session['city'] + '/' + locFile
                candidateHtml_file = 'maps/' + session['city'] + '/' + htmlFile
                neighbourhood_selected = False
                session['restType'] = typeRest
        except:
            errors.append(
                "Unable to process data for selected city and restaurant.  Please try again."
            )
            return render_template('error.html', errors=errors)

        if neighbourhood_selected:
            # Get latitude and longitude of the center of the neighbourhoud
            center = logic.get_neigh_center(session['neighbourhood'], session['city'])
            session['neigh_center'] = center
        else:
            if city == "NewYorkCity":
                address = "Woodside, " + city + ", USA"
            else:
                address = city + ", USA"
            # Get latitude and longitude of the center of the city
            center = logic.get_coordinates(address)
            session['city_center'] = center

        if not path.exists(candidateJson_file):
            if center:
                # Get latitudes and longitudes of all the neighbourhoods from city center
                # Get candidate area centers
                if neighbourhood_selected:
                    latitudes, longitudes, distances, xs, ys = logic.get_candidate_centers(center,
                                                                session['city'], session['neighbourhood'])
                else:
                    latitudes, longitudes, distances, xs, ys = logic.get_candidate_centers(center, session['city'])
                # store the return values in the cache variable
                cache['LATITUDES'] = latitudes
                cache['LONGITUDES'] = longitudes
                cache['DISTANCES'] = distances
                cache['xs'] = xs
                cache['ys'] = ys
                # Get candidate area addresses
                if neighbourhood_selected:
                    logic.get_candidate_addresses(cache, session['city'], session['neighbourhood'])
                    logic.get_candidate_map(session['neigh_center'], session['city'], session['neighbourhood'])
                else:
                    logic.get_candidate_addresses(cache, session['city'])
                    logic.get_candidate_map(session['city_center'], session['city'])

        with open(candidateJson_file, 'rb') as f:
            df = json.load(f)
            locations = pd.json_normalize(df['data'])
            if 'level_0' in locations.columns:
                locations.drop(['level_0'], axis=1)
            temp = locations.filter(items=['Address', 'Latitude', 'Longitude', 'X', 'Y', 'Distance from center'])
            df = temp[1:11]

    else:
        errors.append(
            "Unable to get data for city and restaurant.  Please try again."
        )
        return render_template('error.html', errors=errors)

    if neighbourhood_selected:
        return render_template('neighbour_candidates.html', location_table=df.to_html(classes='location'),
                            neighMap=candidateHtml_file, city=session['city'], neighbourhood=session['neighbourhood'],
                            totalNeighs=len(locations), type=session['restType'], distance=0.5)
    else:
        return render_template('neighbour_candidates.html', location_table=df.to_html(classes='location'),
                               neighMap=candidateHtml_file, city=session['city'], totalNeighs=len(locations),
                               type=session['restType'], distance=3.5)


@app.route('/restaddresses')
def restaddresses():
    locFile = 'candidates.json'
    htmlFile = session['restType'] + '.html'
    if not session.get('neighbourhood') is None:
        candidateFile = os.getcwd() + '/data/' + session['city'] + '/' + session['neighbourhood'] + '/' + locFile
        restFile = os.getcwd() + '/data/' + session['city'] + '/' + session['neighbourhood'] + '/' + 'restaurants.json'
        restaurant_htmlFile = 'maps/' + session['city'] + '/' + session['neighbourhood'] + '/' + htmlFile
        restaurantFile = os.getcwd() + '/static/maps/' + session['city'] + '/' + session['neighbourhood'] + '/' + \
                         htmlFile
        neighbourhood = True
    else:
        candidateFile = os.getcwd() + '/data/' + session['city'] + '/' + locFile
        restFile = os.getcwd() + '/data/' + session['city'] + '/' + 'restaurants.json'
        restaurant_htmlFile = 'maps/' + session['city'] + '/' + htmlFile
        restaurantFile = os.getcwd() + '/static/maps/' + session['city'] + '/' + htmlFile
        neighbourhood = False

    try:
        with open(candidateFile, 'rb') as f:
            df = json.load(f)
            candidates = pd.json_normalize(df['data'])
        latitudes = candidates['Latitude']
        longitudes = candidates['Longitude']
    except:
        errors.append(
            "Unable to load candidate location info.  Please try again."
        )
        return render_template('error.html', errors=errors)

    if not os.path.exists(restFile):
        restaurants = logic.get_neighbourhood_restaurants(latitudes, longitudes)
        restaurants.to_json(restFile, orient='table')

    try:
        with open(restFile, 'rb') as f:
            df = json.load(f)
            df_restaurants = pd.json_normalize(df['data'])
    except:
        errors.append(
            "Unable to load restaurant information for the neighbourhood - " + session['neighborhood']
        )
        return render_template('error.html', errors=errors)

    # Calculate some basic metrics
    if 'Total Restaurants' not in candidates.columns:
        area_restaurants = df_restaurants[df_restaurants['Venue Distance'] <= 300]
        count_area = area_restaurants.groupby(['Area Latitude', 'Area Longitude'])['Venue Id'].count().reset_index()
        count_area.sort_values(by=['Area Latitude', 'Area Longitude'], inplace=True)
        candidates.sort_values(by=['Latitude', 'Longitude'], inplace=True)
        candidates.reset_index()
        candidates['Total Restaurants'] = count_area['Venue Id']
        candidates.to_json(candidateFile, orient='table')

    if 'Type Of' in df_restaurants.columns:
        df = df_restaurants.drop(['Type Of'], axis=1)
    else:
        df = df_restaurants
    rest_type = session['restType'] #+ ' Restaurant'
    category_ids = fs.extract_categories(rest_type)
    venue_type = []
    for idx, row in df.iterrows():
        if row['Venue Category Id'] in category_ids:
            restType = True
        else:
            restType = False
        venue_type.append(restType)
    df['Type Of'] = venue_type
    if 'level_0' in df.columns:
        df_drop = df.drop(['level_0'], axis=1)
    else:
        df_drop = df
    df_drop.to_json(restFile, orient='table')

    tmp_rest = df.filter(items=['Venue Name', 'Venue Address', 'Venue Category Name', 'Venue Distance'])
    restaurants = tmp_rest[1:11]
    area_restaurants = df[df['Venue Distance'] <= 300]
    tmp_rest = area_restaurants.filter(items=['Venue Name', 'Venue Address', 'Venue Category Name', 'Venue Distance'])
    tmp_area_restaurants = tmp_rest[1:11]
    type_rest = df[df['Type Of']]
    tmp_rest = type_rest.filter(items=['Venue Name', 'Venue Address', 'Venue Category Name', 'Venue Distance'])
    tmp_type_rest = tmp_rest[1:11]

    metrics = {'Total': df.shape[0],
                'typeTotal': type_rest.shape[0],
                'Percent': round(type_rest.shape[0] / df.shape[0] * 100, 2),
               'Average': df.groupby(['Area Latitude', 'Area Longitude'])['Venue Id'].
                   count().reset_index()['Venue Id'].mean()}

    if not path.exists(restaurantFile):
        if neighbourhood:
            logic.get_neigh_map(session['city'], session['restType'], session['neigh_center'], session['neighbourhood'])
        else:
            logic.get_neigh_map(session['city'], session['restType'], session['city_center'])

    return render_template('restaddresses.html',
                           restMap=restaurant_htmlFile, metrics=metrics, type=session['restType'],
                           restaurant_table=restaurants.to_html(classes='location'),
                           area_restaurant_table=tmp_area_restaurants.to_html(classes='location'),
                           type_restaurant_table=tmp_type_rest.to_html(classes='location'),
                           city=session['city'])

@app.route('/restheatmap')
def restheatmap():
    locFile = 'candidates.json'
    htmlFile = session['restType'] + '_HeatMap.html'
    if not session.get('neighbourhood') is None:
        candidateFile = os.getcwd() + '/data/' + session['city'] + '/' + session['neighbourhood'] + '/' + locFile
        restFile = os.getcwd() + '/data/' + session['city'] + '/' + session['neighbourhood'] + '/' + 'restaurants.json'
        restHeatMap_htmlFile = 'maps/' + session['city'] + '/' + session['neighbourhood'] + '/' + htmlFile
        restHeatMapFile = os.getcwd() + '/static/maps/' + session['city'] + '/' + session['neighbourhood'] + '/' + \
                         htmlFile
        neighbourhood = True
        min_distance = 5000
    else:
        candidateFile = os.getcwd() + '/data/' + session['city'] + '/' + locFile
        restFile = os.getcwd() + '/data/' + session['city'] + '/' + 'restaurants.json'
        restHeatMap_htmlFile = 'maps/' + session['city'] + '/' + htmlFile
        restHeatMapFile = os.getcwd() + '/static/maps/' + session['city'] + '/' + htmlFile
        neighbourhood = False
        min_distance = 10000

    with open(candidateFile, 'rb') as f:
        df = json.load(f)
        locations = pd.json_normalize(df['data'])

    with open(restFile, 'rb') as f:
        df = json.load(f)
        df_restaurants = pd.json_normalize(df['data'])

    area_restaurants = df_restaurants[df_restaurants['Venue Distance'] <= 300]
    count_area = area_restaurants.groupby(['Area Latitude', 'Area Longitude'])['Venue Id'].count().reset_index()
    locations['Total Restaurants'] = count_area['Venue Id']

    type_restaurants = df_restaurants[df_restaurants['Type Of'] == True]

    distances_to_italian_restaurant = []

    for area_x, area_y in zip(locations['X'], locations['Y']):
        for idx, row in type_restaurants.iterrows():
            res_x = row['Venue X']
            res_y = row['Venue Y']
            d = util.calc_xy_distance(area_x, area_y, res_x, res_y)
            if d < min_distance:
                min_distance = d
        distances_to_italian_restaurant.append(min_distance)

    locations['Distance to Italian restaurant'] = distances_to_italian_restaurant
    tmp_file = locations[1:11]
    avg_dist = locations['Distance to Italian restaurant'].mean()

    if not path.exists(restHeatMapFile):
        if neighbourhood:
            logic.get_heat_map(session['city'], session['restType'], session['neigh_center'], session['neighbourhood'])
        else:
            logic.get_heat_map(session['city'], session['restType'], session['city_center'])


    geoFile = session['city'] + '_districts.geojson'
    geojsonFile = os.getcwd() + '/data/' + session['city'] + '/' + geoFile
    with open(geojsonFile, 'r') as f:
        df = json.load(f)
    df_districts = pd.json_normalize(df['features'])
    neighList = sorted(df_districts['properties.NTAName'])

    if neighbourhood:
        return render_template('restHeatMap.html', restHeatMap=restHeatMap_htmlFile,
                               restaurant_table=tmp_file.to_html(classes='location'),
                               avg_dist=avg_dist, neighbour=session['neighbourhood'],
                               type=session['restType'], city=session['city'])
    else:
        return render_template('restHeatMap.html', restHeatMap=restHeatMap_htmlFile,
                           restaurant_table=tmp_file.to_html(classes='location'),
                           avg_dist=avg_dist, neighList=neighList,
                           type=session['restType'],city=session['city'])

if __name__ == '__main__':
    app.run(debug=True)