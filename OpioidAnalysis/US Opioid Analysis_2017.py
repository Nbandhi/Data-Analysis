#!/usr/bin/env python
# coding: utf-8

# ![image.png](attachment:image.png)
# 
# <h1 align=center><font size = 5>Capstone Project - Analysis of Opioid Addiction Data</font></h1>

# ## Table of contents
# * [Introduction](#introduction)
# * [Data](#data)
# * [Methodology](#methodology)
# * [Analysis](#analysis)
# * [Results and Discussion](#results)
# * [Conclusion](#conclusion)

# 
# 
# ## Introduction <a name="introduction"></a>

# Between 1999 and 2016, more than 630,000 people died from a drug overdose in the United States. The current epidemic of drug overdoses began in the 1990s with overdose deaths involving prescription opioids, driven by dramatic increases in prescribing of opioids for chronic pain.  
# 
# We will analyze data for 5 years (2013 to 2017) to understand the **opioid prescription rates of health care providers** based on their speciality and the death rates due to opioid addiction.  
# 
# We will aslo study the impact of **Socioeconomic indicators** like poverty rates, population change, unemployment rates, and education levels on opioid addiction
# 
# 

# ## Data <a name="data"></a>

# Based on definition of our problem, data that we need:
# * opioid drug prescriptions by doctors by speccialtiy
# * socioecnomic data
# * United states - State, County and Zipcode data
# 
# 
# Following data sources will be needed to extract/generate the required information:
# * The Centers for Medicare & Medicaid Services (CMS) has prepared a public data set, the Medicare Part D Opioid Prescriber Summary File
# * Scoioecnomic indicators from **https://www.ers.usda.gov/data-products/county-level-data-sets/**  
# 
# 
# http://datausa.io/api/data?Geography=01000US:children&measure=Household Income by Race,Household Income by Race Moe&Race=0

# In[109]:


import numpy as np # library to handle data in a vectorized manner

import pandas as pd # library for data analsysis
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

import json # library to handle JSON files
from pandas.io.json import json_normalize
import types

# Matplotlib and associated plotting modules
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


#!pip install folium
import folium
 
from folium.plugins import MarkerCluster
#from folium.plugins import CirclePattern

from geopy.geocoders import Nominatim 
import requests

import seaborn as sn

# import k-means from clustering stage
from sklearn.cluster import KMeans

import wget

import os

import os.path
from os import path

from sklearn import linear_model
import statsmodels.api as sm

print('Libraries imported.')


# ### Opioid Deaths Dataset

# Downloaded the data for opioid deaths from https://opioid.amfar.org/indicator/drugdeaths and stored it in Assessts of IBM Watson

# In[43]:



dest_folder  = os.getcwd()
file_name = dest_folder + '\Data\opioid_deaths.csv'
df_opioids = pd.read_csv(file_name)
df_opioids = df_opioids.fillna(0)
 


# In[44]:


#Filter data for years 2013 to 2017

df_opioid_deaths = df_opioids.drop(['STATE', 'STATEFP', 'COUNTYFP', 'INDICATOR'],axis=1)

df_opioid_deaths.rename(columns={'STATEABBREVIATION':'State',
                                'YEAR':'Year',
                                'VALUE':'Opioid Deaths'}, inplace=True)

df_opioid_deaths['COUNTY'] = df_opioid_deaths['COUNTY'].str.split(' ').str[0].str.strip()

df_US_opioid_deaths =  df_opioid_deaths[df_opioid_deaths.Year.isin([2013, 2014, 2015, 2016, 2017])]


df_US_opioid_deaths.head()


# In[36]:


def download_file(request, folder, file):
    
    destination = folder + file

    wget.download(request, out=destination) 
    


# ### Load State, County and Zip data

# In[52]:



file_name = file_name = dest_folder + '\Data\county_zip.csv'

if path.exists(file_name):
    print('File Exists: ' + str(path.exists(file_name)))
else:
    url = 'https://query.data.world/s/dobz6iqykhxrdkmvndle4qb2j2ny3w'
    download_file(url, dest_folder, '\Data\county_zip.csv')

df_counties = pd.read_csv(file_name,names=['ZIP','COUNTY','STATE','STCOUNTYFP','CLASSFP'],
                             dtype={"ZIP": str},header=1)
df_county_zip = df_counties.drop(['STATE', 'STCOUNTYFP', 'CLASSFP'], axis=1) 

df_county_zip['COUNTY'] = df_county_zip['COUNTY'].str.split(' ').str[0].str.strip()

df_county_zip.head()


# In[38]:


# Get State Name and State Code

file_name = dest_folder + '\Data\state_abb.csv'
df_states = pd.read_csv(file_name)
df_states.rename(columns={'State':'State Name',
                         'Abbreviation':'State'}, inplace=True)
df_states.head()


# ### Opioid Prescription dataset

# 
# This dataset is about Medicare Part D Opioid Prescriber Summary File 2017. https://data.cms.gov/api/views/sakz-a2rp/rows.csv?accessType=DOWNLOAD  
# This dataset is about Medicare Part D Opioid Prescriber Summary File 2016. https://data.cms.gov/api/views/6wg9-kwip/rows.csv?accessType=DOWNLOAD  
# This dataset is about Medicare Part D Opioid Prescriber Summary File 2015. https://data.cms.gov/api/views/6i2k-7h8p/rows.csv?accessType=DOWNLOAD  
# This dataset is about Medicare Part D Opioid Prescriber Summary File 2014. https://data.cms.gov/api/views/e4ka-3ncx/rows.csv?accessType=DOWNLOAD  
# This dataset is about Medicare Part D Opioid Prescriber Summary File 2013. https://data.cms.gov/api/views/yb2j-f3fp/rows.csv?accessType=DOWNLOAD  
# 
# 
# The **Opioid_data.csv** data set includes details  on the individual opioid prescribing rates of health providers . It includes following fields:  
# 
# | Field                     | Description                         |
# |---------------------------|-------------------------------------|
# | NPI                       | Provider Identification Number      |
# | NPPES Provider Last Name  | Provider Last Name                  |
# | NPPES Provider First Name | Provider First Name                 |
# | NPPES Provider Zip Code   | Provider Zip Code                   |
# | NPPES Provider State      | Provider State                      |
# | Speciality Description    | Provider Speciality                 |
# | Total Claim Count         | Total Claims for by provider                   |
# | Opioid Claim Count        | Opioid Claim by provider                  |
# | Opioid Prescribing Rate   | Opioid Prescribing Rate             |
# | Long Acting Opioid Count  | Long Acting Opioid Claim by provider           |
# | Long Acting Opioid Prescribing Rate | Long Acting Opioid Prescribing Rate |
# |                           |                                     |
# 
# 
# NJ Zip code JSON https://raw.githubusercontent.com/OpenDataDE/State-zip-code-GeoJSON/master/nj_new_jersey_zip_codes_geo.min.json  
# 
# 

# In[41]:


url = 'https://raw.githubusercontent.com/deldersveld/topojson/master/countries/us-states/NJ-34-new-jersey-counties.json'

download_file(url, dest_folder, '/Data/nj_zipcode_geojson')


# ### Load Opioid Prescription data for 2013 through 2017 from Medicare Part D

# #### 2017 Data

# In[54]:


### Load Opioid Prescription data for 2014 from Medicare Part D

# Create a dataframe with the loaded cvs file
    
    
file_name = file_name = dest_folder + '\Data\opioid_data_2017.csv'
    
df_opioid_2017 = pd.read_csv(file_name,names=['NPI','NPPES_last_name','NPPES_first_name','NPPES_zip_code','NPPES_state','Speciality_Description','Total_Claim_Count','Opioid_Claim_Count',
                                                           'Opioid_Prescribing_Rate','Long-Acting_Opioid_Claim_Count','Long-Acting_Opioid_Prescribing_Rate'],
                             dtype={"NPPES_zip_code": str, "NPI":str},header=1)

df_opioid_2017 = df_opioid_2017[df_opioid_2017['Long-Acting_Opioid_Claim_Count'].notnull()]
df_opioid_2017 = df_opioid_2017[df_opioid_2017['Long-Acting_Opioid_Claim_Count'] != 0]


df_opioid_2017.head()


# #### 2106 Data

# In[55]:


### Load Opioid Prescription data for 2016 from Medicare Part D

# Create a dataframe with the loaded cvs file

file_name = dest_folder + '\Data\opioid_data_2016.csv'

df_opioid_2016 = pd.read_csv(file_name,names=['NPI','NPPES_last_name','NPPES_first_name','NPPES_zip_code','NPPES_state','Speciality_Description','Total_Claim_Count','Opioid_Claim_Count',
                                                           'Opioid_Prescribing_Rate','Long-Acting_Opioid_Claim_Count','Long-Acting_Opioid_Prescribing_Rate'],
                             dtype={"NPPES_zip_code": str},header=1)

df_opioid_2016 = df_opioid_2016[df_opioid_2016['Long-Acting_Opioid_Claim_Count'].notnull()]
df_opioid_2016 = df_opioid_2016[df_opioid_2016['Long-Acting_Opioid_Claim_Count'] != 0]

df_opioid_2016.head()


# #### 2015 Data

# In[58]:


### Load Opioid Prescription data for 2015 from Medicare Part D
    
# Create a dataframe with the loaded cvs file

file_name = dest_folder + '\Data\opioid_data_2015.csv'

df_opioid_2015 = pd.read_csv(file_name,names=['NPI','NPPES_last_name','NPPES_first_name','NPPES_zip_code','NPPES_state','Speciality_Description','Total_Claim_Count','Opioid_Claim_Count',
                                                           'Opioid_Prescribing_Rate','Long-Acting_Opioid_Claim_Count','Long-Acting_Opioid_Prescribing_Rate'],
                             dtype={"NPPES_zip_code": str},header=1)

df_opioid_2015 = df_opioid_2015[df_opioid_2015['Long-Acting_Opioid_Claim_Count'].notnull()]
df_opioid_2015 = df_opioid_2015[df_opioid_2015['Long-Acting_Opioid_Claim_Count']!= 0]


df_opioid_2015.head()


# #### 2014 Data

# In[60]:


### Load Opioid Prescription data for 2014 from Medicare Part D
   
# Create a dataframe with the loaded cvs file

file_name = dest_folder + '\Data\opioid_data_2014.csv'


df_opioid_2014 = pd.read_csv(file_name,names=['NPI','NPPES_last_name','NPPES_first_name','NPPES_zip_code','NPPES_state','Speciality_Description','Total_Claim_Count','Opioid_Claim_Count',
                                                           'Opioid_Prescribing_Rate','Long-Acting_Opioid_Claim_Count','Long-Acting_Opioid_Prescribing_Rate'],
                             dtype={"NPPES_zip_code": str},header=1)

df_opioid_2014 = df_opioid_2014[df_opioid_2014['Long-Acting_Opioid_Claim_Count'].notnull()]
df_opioid_2014 = df_opioid_2014[df_opioid_2014['Long-Acting_Opioid_Claim_Count']!= 0]


df_opioid_2014.head()


# #### 2013 Data

# In[61]:


### Load Opioid Prescription data for 2013 from Medicare Part D
   
# Create a dataframe with the loaded cvs file

file_name = dest_folder + '\Data\opioid_data_2013.csv'


df_opioid_2013 = pd.read_csv(file_name,names=['NPI','NPPES_last_name','NPPES_first_name','NPPES_zip_code','NPPES_state','Speciality_Description','Total_Claim_Count','Opioid_Claim_Count',
                                                           'Opioid_Prescribing_Rate','Long-Acting_Opioid_Claim_Count','Long-Acting_Opioid_Prescribing_Rate'],
                             dtype={"NPPES_zip_code": str},header=1)

df_opioid_2013 = df_opioid_2013[df_opioid_2013['Long-Acting_Opioid_Claim_Count'].notnull()]
df_opioid_2013 = df_opioid_2013[df_opioid_2013['Long-Acting_Opioid_Claim_Count']!= 0]

df_opioid_2013.head()


# In[62]:


df_opioid_2017['YEAR'] = 2017
df_opioid_2016['YEAR'] = 2016
df_opioid_2015['YEAR'] = 2015
df_opioid_2014['YEAR'] = 2014
df_opioid_2013['YEAR'] = 2013


# ### Clean and extract Opioid Prescription Data

# In[67]:


# Concatanate all the dtaframes into a single one

df_opioid_total = pd.concat([df_opioid_2017, df_opioid_2016, df_opioid_2015, df_opioid_2014, df_opioid_2013])       .groupby(['NPI','NPPES_last_name','NPPES_first_name','NPPES_zip_code','NPPES_state','Speciality_Description','YEAR'])['Total_Claim_Count',
                                                                                                                             'Opioid_Claim_Count','Long-Acting_Opioid_Claim_Count']\
       .sum().reset_index()
df_opioid_US = pd.merge(df_opioid_total,df_county_zip, left_on='NPPES_zip_code',right_on='ZIP')

df_opioid_US.head(10)


# In[70]:


# Filter Columns needed for analysis

df_opioid_US_data_c = df_opioid_US.filter(items=['NPI','NPPES_last_name','NPPES_first_name','NPPES_zip_code','NPPES_state','Speciality_Description',
                                                         'YEAR','COUNTY','Total_Claim_Count','Opioid_Claim_Count','Long-Acting_Opioid_Claim_Count'])

df_opioid_US_data_c.rename(columns={'NPPES_zip_code':'ZIP', 'NPPES_state': 'State', 'Long-Acting_Opioid_Claim_Count': 'Opioid Prescription Count',
                                'Speciality_Description':'Speciality','YEAR':'Year'}, inplace=True)

df_opioid_US_data=pd.merge(df_opioid_US_data_c,df_states)
df_opioid_US_data.head()


# In[71]:


# Group opioid death data at COUNTY level and filer for NJ

df_opioidDeaths_US_Couty = df_US_opioid_deaths.groupby(['State','COUNTY','Year'])['Opioid Deaths'].sum().reset_index()

df_opioidDeaths_US_Couty.head()


# #### Merge opioid Prescription data and opioid death data

# In[72]:


# Group opioid prescription data at COUNTY level

df_opioidPres_US_county = df_opioid_US_data.groupby(['State','State Name','COUNTY','Year'])['Total_Claim_Count','Opioid_Claim_Count','Opioid Prescription Count'].sum().reset_index()

df_US_county_data = pd.merge(df_opioidPres_US_county,df_opioidDeaths_US_Couty)

df_US_county_data.head()


# In[74]:


# Data at the State level

df_US_county_data_c = df_US_county_data.filter(items=['State','State Name','COUNTY','Total_Claim_Count','Opioid_Claim_Count','Opioid Prescription Count','Opioid Deaths'])

df_OpiodDeaths = df_US_county_data_c.groupby(['State','State Name'])['Total_Claim_Count','Opioid_Claim_Count','Opioid Prescription Count','Opioid Deaths'].sum().reset_index()

#df_OpiodDeaths = df_OpioidDeaths_county[df_OpioidDeaths_county.State != 'PR']

# Calcualate the rates
df_OpiodDeaths['Opioid Prescription Rate'] = 100/ df_OpiodDeaths['Total_Claim_Count'] * df_OpiodDeaths['Opioid_Claim_Count']
df_OpiodDeaths['Opioid Death Rate'] = 100/ df_OpiodDeaths['Opioid Prescription Count'] * df_OpiodDeaths['Opioid Deaths']

df_OpiodDeaths.head(10)


# #### Socio Economic Data

# In[85]:



file_name = dest_folder + '\Data\state_abb.csv'

if path.exists(file_name):
    print('File Exists: ' + str(path.exists(file_name)))
else:
    url = 'https://raw.githubusercontent.com/jasonong/List-of-US-States/master/states.csv'
    download_file(url, dest_folder, '\Data\state_abb.csv')


# In[86]:


# Get Disablitiy data

file_name = dest_folder + '\Data\SocioEconomicData.csv'

df_socioeconomic = pd.read_csv(file_name, dtype={'Unemployed': int,'Employed':int, 'Homeless':int, 'Population':int,
                                                               'In Poverty':int, 'Not In Poverty':int, 'Depression Count':int, 'Insured':int,
                                                               'Uninsured':int, 'No high school diploma':int,'Bachelor\'s degree or higher':int,
                                                               'Bachelor\'s degree or higher':int,'Median Inome':int})

df_socioeconomic_data = df_socioeconomic.drop('Depression Rate',axis=1)
df_socioeconomic_data.head()


# In[80]:


df_data_analysis = pd.merge(df_OpiodDeaths,df_socioeconomic_data)
df_data_analysis.head()


# ## Analysis <a name="analysis"></a>

# In[81]:


df_data_analysis['Opioid Prescription Rate'] = 100/ df_data_analysis['Population'] * df_data_analysis['Opioid Prescription Count']
df_data_analysis['Opioid Death Rate'] = 100/ df_data_analysis['Population'] * df_data_analysis['Opioid Deaths']
df_data_analysis['Unemployment Rate'] = 100/ df_data_analysis['Population'] * df_data_analysis['Unemployed']
df_data_analysis['Employment Rate'] = 100/ df_data_analysis['Population'] * df_data_analysis['Employed']
df_data_analysis['Homeless Rate'] = 100/ df_data_analysis['Population'] * df_data_analysis['Homeless']
df_data_analysis['Poverty Rate'] = 100/ df_data_analysis['Population'] * df_data_analysis['In Poverty']
df_data_analysis['Depression Rate'] = 100/ df_data_analysis['Population'] * df_data_analysis['Depression Count']
df_data_analysis['Insured Rate'] = 100/ df_data_analysis['Population'] * df_data_analysis['Insured']
df_data_analysis['Uninsured Rate'] = 100/ df_data_analysis['Population'] * df_data_analysis['Uninsured']
df_data_analysis['HS Dropout Rate'] = 100/ df_data_analysis['Population'] * df_data_analysis['No high school diploma']
df_data_analysis['Degree Rate'] = 100/ df_data_analysis['Population'] * df_data_analysis['Bachelor\'s degree or higher']
''
df_data_analysis_slice = df_data_analysis.filter(items=['State','State Name','Population','Opioid Prescription Rate','Opioid Death Rate', 'Unemployment Rate','Employment Rate',
                                                       'Homeless Rate','Poverty Rate','Depression Rate',
                                                       'Insured Rate','Uninsured Rate','HS Dropout Rate','Degree Rate'])  
df_data_analysis_slice.head()
                                                                                        


# #### Add Latitude and Logitute data for the States

# In[88]:


file_name = dest_folder + '\Data\state_geo'

if path.exists(file_name):
    print('File Exists: ' + str(path.exists(file_name)))
else:
    url = 'https://raw.githubusercontent.com/python-visualization/folium/master/examples/data/us-states.json'
    download_file(url, dest_folder, '\Data\state_geo')


# In[90]:



file_name = dest_folder + '\Data\county_geo'

if path.exists(file_name):
    print('File Exists: ' + str(path.exists(file_name)))
else:
    print('Downloading File: ' + str(path.exists(file_name)))
    url = 'https://raw.githubusercontent.com/python-visualization/folium/master/tests/us-counties.json'
    download_file(url, dest_folder, '\Data\county_geo')


# In[92]:


file_name = dest_folder + '\Data\statelatlong.csv'

df_US_latlon = pd.read_csv(file_name)
#df_US_latlon.head(10)

df_data_analysis_US = pd.merge(df_data_analysis_slice, df_US_latlon)

df_data_analysis_US.head(10)


# #### Opioid Prescription Rate vs Opioid Death Rates

# #### Correlatioin

# In[93]:


df_data_analysis_slice.corr()


# In[94]:


from matplotlib.pyplot import figure
figure(num=None, figsize=(20,8), dpi=80, facecolor='w', edgecolor='k')
ax = plt.gca()

#plt.figure()
#fig = plt.figure(figsize=(3,10)

df_data_analysis_US.plot(kind='bar',x='State Name', figsize=(20,8), y='Opioid Prescription Rate', ax=ax)
df_data_analysis_US.plot(kind='line',x='State Name', y='Opioid Death Rate', color='red',ax=ax)

ax.set_title('Opioid Prescription Rates and Death Rates', fontsize=16)
plt.rcParams.update({'font.size': 14})
plt.xticks(rotation='vertical')

plt.show()


# In[95]:


#==============================================================================
#  Plots on two different Figures and sets the size of the figures
#==============================================================================

# figure size = (width,height)
f1 = plt.figure(figsize=(30,20))
#f2 = plt.figure(figsize=(30,10))

#------------------------------------------------------------------------------
#  Figure 1 with 6 plots
#------------------------------------------------------------------------------

# plot one
# Plot column labeled Unemploymnet Rate
# subplot(4 Rows, 3 Columns, First subplot,)
ax1 = f1.add_subplot(4,3,1)
ax1 = sn.regplot(x="Unemployment Rate", y="Opioid Death Rate", data=df_data_analysis_US)

# plot two
# plot column labeled Employment Rate
# subplot(4 Rows, 3 Columns, Second subplot)
ax2 = f1.add_subplot(4,3,2)
ax2 = sn.regplot(x="Employment Rate", y="Opioid Death Rate", data=df_data_analysis_US)

# plot three
# plot column Homeless Rate
# subplot(4 Rows, 3 Columns, Third subplot)
ax3 = f1.add_subplot(4,3,3)
ax3 = sn.regplot(x="Homeless Rate", y="Opioid Death Rate", data=df_data_analysis_US)

# plot four
# plot column labeled Poverty Rate
# subplot(4 Rows, 3 Columns, Fourth subplot)
ax4 = f1.add_subplot(4,3,4)
ax4 = sn.regplot(x="Poverty Rate", y="Opioid Death Rate", data=df_data_analysis_US)

# plot five
# plot column labeled Depression Rate
# subplot(4 Rows, 3 Columns, Fifth subplot)
ax5 = f1.add_subplot(4,3,5)
ax5 = sn.regplot(x="Depression Rate", y="Opioid Death Rate", data=df_data_analysis_US)

# plot six
# plot column labeled Insured Rate
# subplot(4 Rows, 3 Columns, Sixth subplot)
ax6 = f1.add_subplot(4,3,6)
ax6 = sn.regplot(x="Insured Rate", y="Opioid Death Rate", data=df_data_analysis_US)

# plot seven
# Curve 1: plot column labeled Uninsured Rate
# subplot(4 Rows, 3 Columns, Seventh subplot)
ax7 = f1.add_subplot(4,3,7)
ax7 = sn.regplot(x="Uninsured Rate", y="Opioid Death Rate", data=df_data_analysis_US)

# plot eight
# Curve 1: plot column labeled HS Dropout Rate
# subplot(4 Rows, 3 Columns, Eight subplot)
ax8 = f1.add_subplot(4,3,8)
ax8 = sn.regplot(x="HS Dropout Rate", y="Opioid Death Rate", data=df_data_analysis_US)

# plot nine
# Curve 1: plot column labeled Degree Rate
# subplot(4 Rows, 3 Columns, Nitnth subplot)
ax9 = f1.add_subplot(4,3,9)
ax9 = sn.regplot(x="Degree Rate", y="Opioid Death Rate", data=df_data_analysis_US)

# plot ten
# Curve 1: plot column labeled Degree Rate
# subplot(4 Rows, 3 Columns, Tenth subplot)
ax10 = f1.add_subplot(4,3,10)
ax10 = sn.regplot(x="Opioid Prescription Rate", y="Opioid Death Rate", data=df_data_analysis_US)


plt.show()


# #### Plot the data on US Map

# In[97]:


COORDINATES = (37, -102)
MAX_COUNT = len(df_data_analysis_US)

file_name = dest_folder + '\Data\state_geo'

map_opioid = folium.Map(location=COORDINATES, zoom_start=5)

map_opioid.choropleth(
 geo_data=file_name,
 name='choropleth',
 data=df_data_analysis_US,
 columns=['State', 'Opioid Prescription Rate'],
 key_on='feature.id',
 fill_color='YlGn',
 fill_opacity=0.9,
 line_opacity=0.5,
 legend_name='Opioid Prescription Rate vs Death Rate'
)
folium.LayerControl().add_to(map_opioid)

for each in df_data_analysis_US[0:MAX_COUNT].iterrows():
   folium.Circle(
      location=[each[1]['Latitude'], each[1]['Longitude']],
      popup=each[1]['State'],
      radius=each[1]['Opioid Death Rate']*1000000,
      color='red',
      fill=True,
      fill_color='red'
   ).add_to(map_opioid)

map_opioid

map_opioid.save('US_Opioid_2017.html')


# #### Top 5 States - Opioid Death Rates

# In[98]:


df_data_analysis_sorted = df_data_analysis_US.sort_values('Opioid Death Rate', ascending=False)
df_data_analysis_sorted.head()


# #### Bottom 5 States - Opioid Death Rates

# In[99]:


df_data_analysis_sorted.tail()


# #### Regression Analysis - Opioid Death Rate

# In[106]:


X = df_data_analysis_US[['Unemployment Rate', 'Employment Rate', 'Homeless Rate', 'Poverty Rate', 'Depression Rate', 'Insured Rate', 'Uninsured Rate', 'HS Dropout Rate', 'Degree Rate']]
Y = df_data_analysis_US[['Opioid Death Rate']]

# with sklearn
regr = linear_model.LinearRegression()
regr.fit(X, Y)

# with statsmodels
X = sm.add_constant(X) # adding a constant
 
model = sm.OLS(Y, X).fit()
predictions = model.predict(X) 
 
print_model = model.summary()
print(print_model)


# In[112]:


plt.scatter(df_data_analysis_US['Opioid Death Rate'].astype(float),df_data_analysis_US['Unemployment Rate'].astype(float), color = 'r')
plt.title('Opioid Death Rate Vs Unemployment Rate', fontsize=14)
plt.xlabel('Unemployment Rate', fontsize=14)
plt.ylabel('Opioid Death Rate', fontsize=14)
plt.grid(True)
plt.show()


# #### Regression Analysis - Opioid Prescription Rate

# In[113]:


X = df_data_analysis_US[['Unemployment Rate', 'Employment Rate', 'Homeless Rate', 'Poverty Rate', 'Depression Rate', 'Insured Rate', 'Uninsured Rate', 'HS Dropout Rate', 'Degree Rate']]
Y = df_data_analysis_US[['Opioid Prescription Rate']]

# with sklearn
regr = linear_model.LinearRegression()
regr.fit(X, Y)

# with statsmodels
X = sm.add_constant(X) # adding a constant
 
model = sm.OLS(Y, X).fit()
predictions = model.predict(X) 
 
print_model = model.summary()
print(print_model)


# In[115]:


plt.scatter(df_data_analysis_US['Opioid Prescription Rate'].astype(float),df_data_analysis_US['Homeless Rate'].astype(float), color = 'r')
plt.title('Opioid Prescription Rate Vs Homeless Rate', fontsize=14)
plt.xlabel('Homeless Rate', fontsize=14)
plt.ylabel('Opioid Prescription Rate', fontsize=14)
plt.grid(True)
plt.show()


# ## Results and Discussion <a name="results"></a>

# When you compare **West Virginia** the state with the **highest opioid death rate**  with the **North Dakota** the state with the **lowest opioid death rate** one notices that the socio-economic factors <br>
# 
# <table>
#     <tr><td></td><td><b>West Virginia</b></td><td><b>North Dakota</b></td></tr>
#     <tr><td><b>Unemployment rate</b></td><td>39.099</td><td>20.651</td></tr> 
#     <tr><td><b>Employment rate</b></td><td>30.509</td><td>40.243</td></tr>
#     <tr><td><b>Homeless rate</b></td><td>0.0103</td><td>0.0048</td></tr> 
#     <tr><td><b>Poverty rate</b></td><td>17.952</td><td>10.987</td></tr>
#     <tr><td><b>Depression rate</b></td><td>8.260</td><td>6.800</td></tr>
#     <tr><td><b>Insured rate</b></td><td>92.573</td><td>91.607</td></tr>
#     <tr><td><b>Uninsured rate</b></td><td>7.324</td><td>7.678</td></tr>
#     <tr><td><b>HS Dropout Rate rate</b></td><td>15.309</td><td>9.134</td></tr>
#     <tr><td><b>Degree rate</b></td><td>16.410</td><td>22.637</td></tr>
#     <tr><td><b>Opioid Prescription rate</b></td><td>3.733</td><td>3.428</td></tr>
# </table>
# 
# have an impact on the opioid death rate.The state with the highest opioid death rate has the highest enemploymnet rate, homless rate, por=verty rate, depression rate, High School Dropout rate and Opioid Prescripi=tion rate.

# Further analysis of the linear dependencies on the two variables - opioid death rate and individual socio-economic factors - results shown below
# 
# <table>
#     <tr><td></td><td><b>Pearson Correlation Coefficient</b></td><td><b>P-value</b></td></tr>
#     <tr><td><b>Unemployment Rate vs Opioid Death Rate</b></td><td>0.28010068903143265</td><td>0.04650549259363219</td></tr> 
#     <tr><td><b>Employment Rate vs Opioid Death Rate</b></td><td>0.10425512143745068</td><td>0.46657670297060405</td></tr>
#     <tr><td><b>Homeless Rate vs Opioid Death Rate</b></td><td>0.16816118599253874</td><td>0.23817466877861332</td></tr> 
#     <tr><td><b>Poverty Rate vs Opioid Death Rat</b></td><td>0.007456071165732117</td><td>0.9585863588975125</td></tr>
#     <tr><td><b>Depression Rate vs Opioid Death Rate</b></td><td>0.1427173514015973</td><td>0.3177635047469663</td></tr>
#     <tr><td><b>Insured Rate vs Opioid Death Rate</b></td><td>0.30178300346351755</td><td>0.03138253740135453</td></tr>
#     <tr><td><b>Uninsured Rate vs Opioid Death Rate</b></td><td>-0.3017031801271633</td><td>0.031429597696551494</td></tr>
#     <tr><td><b>HS Dropout Rate vs Opioid Death Ratee</b></td><td>-0.02998984442396571</td><td>0.8345202835700284</td></tr>
#     <tr><td><b>Degree Rate vs Opioid Death Rate</b></td><td>0.1427173514015973</td><td>0.3177635047469663</td></tr>
#     <tr><td><b>Opioid Prescription Rate vs Opioid Death Rate</b></td><td>-0.10350138706867021</td><td>0.4698224383106909</td></tr>
# </table>
# 
# indicate moderate evidence that the correlation is significant on the impact of **unemployment and insurance rate** on opioid death rate 

# In[ ]:




