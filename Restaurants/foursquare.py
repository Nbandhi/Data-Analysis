import json
import os


dest_folder  = os.getcwd()

file_name =  dest_folder + '\\data\\foursquare_categories.json'

def extract_categories(restType):
    with open(file_name, 'r') as f:
        fs_categories = json.load(f)

    dictRest = fs_categories['response']['categories'][3]
    category = dictRest['categories']

    restaurant_categories = []
    restaurant_categories_id = []

    for x in category:
        if x['name'] == restType:
            restaurant_categories.append(x)
            restaurant_categories_id.append(x['id'])
            for i in x['categories']:
                restaurant_categories_id.append(i['id'])


    return restaurant_categories_id