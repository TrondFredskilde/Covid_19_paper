#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#"""
#Created on Tue May 12 11:16:28 2020

#@author: trond
#"""

import pandas as pd
import numpy as np
import math
from datetime import datetime

df2 = pd.read_csv("Data/us_states_covid19_daily.csv") #

#Calculating the date as the days since the first outbreak was recorded .
df2["DateTime"] = pd.to_datetime(df2['date'], format='%Y%m%d', errors='ignore')
d0 = datetime(2020, 1, 22)
df2['DayNumber'] = df2.apply(lambda x : (x["DateTime"]-d0).days, axis=1)
df2 = df2.drop(columns=['DateTime'])

df_map = pd.DataFrame(df2[["DayNumber","state","positive","negative",
                           "hospitalizedCurrently","onVentilatorCurrently","recovered",
                          "death","totalTestResults"]])

# Import libraries
import geopandas
import json

from bokeh.io import output_notebook, show, output_file
from bokeh.plotting import figure
from bokeh.models import GeoJSONDataSource, LinearColorMapper, ColorBar, NumeralTickFormatter
from bokeh.palettes import brewer

from bokeh.io.doc import curdoc
from bokeh.models import Slider, HoverTool, Select
from bokeh.layouts import widgetbox, row, column

df_map.describe()

# Read the geojson map file for Realtor Neighborhoods into a GeoDataframe object
usa = geopandas.read_file('cb_2018_us_state_20m/cb_2018_us_state_20m.shp')
usa = usa.drop(columns = ["STATEFP","STATENS","AFFGEOID","GEOID","LSAD","ALAND","AWATER"])
usa = usa.rename({'STUSPS': 'state'}, axis='columns')
usa = usa.loc[~usa['NAME'].isin(['Alaska','Hawaii','Puerto Rico'])]

# This dictionary contains the formatting for the data in the plots
format_data = [('positive', 0, 142143,'0,0', 'Positive'),
               ('negative', 0, 395425,'0,0', 'Negative'),
               ('hospitalizedCurrently', 0, 8825,'0,0', 'Hospitalized'),
               ('onVentilatorCurrently', 0, 705,'0,0', 'In Ventilator'),
               ('recovered', 0, 13887,'0,0', 'Recovered'),
               ('death', 0, 10000,'0,0', 'Death'),
               ('totalTestResults', 0, 777568,'0,0', 'Total Test')]
 
#Create a DataFrame object from the dictionary 
format_df = pd.DataFrame(format_data, columns = ['field' , 'min_range', 'max_range' , 'format', 'verbage'])

# Create a function the returns json_data for the day selected by the user
def json_data(selectedDay):
    day = selectedDay
    
    # Pull selected year from df map summary data
    df_day = df_map[df_map['DayNumber'] == day]
    
    # Merge the GeoDataframe object (usa) with the df_map summary data (neighborhood)
    merged = pd.merge(usa, df_day, on='state', how='left')
    
    # Fill the null values
    values = {'DayNumber': day, 'positive': 0, 'negative': 0, 'hospitalizedCurrently': 0,
            'onVentilatorCurrently': 0, 'recovered': 0, 'death': 0, 'totalTestResults': 0}
    merged = merged.fillna(value=values)
    
    # Bokeh uses geojson formatting, representing geographical features, with json
    # Convert to json
    merged_json = json.loads(merged.to_json())
    
    # Convert to json preferred string-like object 
    json_data = json.dumps(merged_json)
    return json_data

# Define the callback function: update_plot
def update_plot(attr, old, new):
    # The input day is the day selected from the slider
    day = slider.value
    new_data = json_data(day)
    
    # The input cr is the criteria selected from the select box
    cr = select.value
    input_field = format_df.loc[format_df['verbage'] == cr, 'field'].iloc[0]
    
    # Update the plot based on the changed inputs
    p = make_plot(input_field)
    
    # Update the layout, clear the old document and display the new document
    layout = column(p, widgetbox(select), widgetbox(slider))
    #curdoc().clear()
    #curdoc().add_root(layout)
    
    # Update the data
    geosource.geojson = new_data 
    
def update_plot1(attr, old, new):
    # The input day is the day selected from the slider
    day = slider.value
    new_data = json_data(day)
    
    # The input cr is the criteria selected from the select box
    cr = select.value
    input_field = format_df.loc[format_df['verbage'] == cr, 'field'].iloc[0]
    
    # Update the plot based on the changed inputs
    p = make_plot(input_field)
    
    # Update the layout, clear the old document and display the new document
    layout = column(p, widgetbox(select), widgetbox(slider))
    curdoc().clear()
    curdoc().add_root(layout)
    
    # Update the data
    geosource.geojson = new_data 
    
    # Create a plotting function
def make_plot(field_name):    
  # Set the format of the colorbar
  min_range = format_df.loc[format_df['field'] == field_name, 'min_range'].iloc[0]
  max_range = format_df.loc[format_df['field'] == field_name, 'max_range'].iloc[0]
  field_format = format_df.loc[format_df['field'] == field_name, 'format'].iloc[0]

  # Instantiate LinearColorMapper that linearly maps numbers in a range, into a sequence of colors.
  color_mapper = LinearColorMapper(palette = palette, low = min_range, high = max_range)

  # Create color bar.
  format_tick = NumeralTickFormatter(format=field_format)
  color_bar = ColorBar(color_mapper=color_mapper, label_standoff=18, formatter=format_tick,
  border_line_color=None, location = (0, 0))

  # Create figure object.
  verbage = format_df.loc[format_df['field'] == field_name, 'verbage'].iloc[0]

  p = figure(title = verbage + ' for each state', 
             plot_height = 500, plot_width = 700,
             toolbar_location = None)
  p.xgrid.grid_line_color = None
  p.ygrid.grid_line_color = None
  p.axis.visible = False

  # Add patch renderer to figure. 
  p.patches('xs','ys', source = geosource, fill_color = {'field' : field_name, 'transform' : color_mapper},
          line_color = 'black', line_width = 0.25, fill_alpha = 1)
  
  # Specify color bar layout.
  p.add_layout(color_bar, 'right')

  # Add the hover tool to the graph
  p.add_tools(hover)
  return p

# Input geojson source that contains features for plotting for:
# initial day 1 and initial criteria positive
geosource = GeoJSONDataSource(geojson = json_data(0))
input_field = 'positive'

# Define a sequential multi-hue color palette.
palette = brewer['Blues'][8]

# Reverse color order so that dark blue is highest obesity.
palette = palette[::-1]

# Add hover tool
hover = HoverTool(tooltips = [('State','@NAME'),
                               ('Positive', '@positive'),
                                 ('Negative','@negative'),
                                ('Hospitalized','@hospitalizedCurrently'),
                                ('In Ventilator','@onVentilatorCurrently'),
                                ('Recovered','@recovered'),
                                  ('Deaths','@death'),
                                  ('Total Tests','@totalTestResults')
                             
                             
                             ])

# Call the plotting function
p = make_plot(input_field)

# Make a slider object: slider 
slider = Slider(title = 'Day',start = 0, end = 94, step = 1, value = 0)
slider.on_change('value', update_plot)

# Make a selection object: select
select = Select(title='Select Criteria:', value='Positive', options=['Positive', 'Negative','Hospitalized',
                                                                    'In Ventilator','Recovered','Death','Total Test'])
select.on_change('value', update_plot1)

# Make a column layout of widgetbox(slider) and plot, and add it to the current document
# Display the current document
layout = column(p, widgetbox(select), widgetbox(slider))
curdoc().add_root(layout)

#output_notebook()
#show(p)
