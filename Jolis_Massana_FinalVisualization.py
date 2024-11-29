import streamlit as st
import pandas as pd
import altair as alt
from vega_datasets import data

# for County choropleths 
import geopandas as gpd
from shapely.geometry import Point
from shapely.geometry import Polygon, MultiPolygon

def general_data_preparation(mass_shootings):

    mass_shootings['Incident Date'] = pd.to_datetime(mass_shootings['Incident Date'])
    mass_shootings['Month_Year'] = mass_shootings['Incident Date'].dt.to_period('M')
    mass_shootings = mass_shootings.drop('Incident Date', axis=1)
 
    # grouping BY STATE AND MONTH
    mass_shootings_states = mass_shootings.groupby(['State', 'Month_Year', 'Region', 'Population']).size().reset_index(name='Total Shootings')
    
    # grouping BY REGION AND MONTH
    mass_shootings_regions = mass_shootings.groupby(['Region', 'Month_Year']).size().reset_index(name='Total Shootings')
    region_population = mass_shootings_states.drop_duplicates('State').groupby(['Region'])['Population'].sum()
    mass_shootings_regions = mass_shootings_regions.merge(region_population, on='Region')
    
    return mass_shootings_regions, mass_shootings_states

#################### Q1 ####################
# - linechart, 5 lines, a line per region, being able to choose years
# - map with regions, select state --> linechart with all states of the region


def second_question(mass_shootings_regions):
    #################### Q2 ####################
    # - grouped barcharts, pair of bars, one for 2014 and the other for the chosen year
    # - scatterplot with 12 points (1 per month), 2014 in x-axis, chosen year in y-axis

    #################### DATA PREPARATION ####################
    mass_shootings_regions['Year'] = mass_shootings_regions['Month_Year'].apply(lambda x: x.year)
    mass_shootings_regions = mass_shootings_regions.drop('Month_Year', axis=1)
    mass_shootings_regions = mass_shootings_regions.groupby(['Region', 'Year', 'Population'])['Total Shootings'].sum().reset_index()
    mass_shootings_regions['Shootings per 10M citizens'] = mass_shootings_regions['Total Shootings'] / mass_shootings_regions['Population'] * 10**7

    #################### BARCHART PLOTTING ####################
    selection_year = alt.selection_point(encodings = ['color'])
    color = alt.condition(selection_year,
                        alt.Color('Year:O', legend = None),
                        alt.value('lightgray')
    )

    Q2_years_barchart = alt.Chart(mass_shootings_regions).mark_bar().encode(
        x = 'Year:O',
        y = 'Shootings per 10M citizens:Q',
        color = color,
        tooltip = 'Shootings per 10M citizens:Q'
    ).properties(
        width = 155,
        height = 400
    ).add_params(selection_year)

    Q2_2014_barchart = alt.Chart(mass_shootings_regions).mark_bar().encode(
        x = 'Year:O',
        y = 'Shootings per 10M citizens:Q',
        color = alt.condition(
            alt.datum.Year == 2014,
            alt.value('#bcdcec'),
            alt.value('transparent')
        ),
        tooltip = 'Shootings per 10M citizens:Q'
    )

    legend_2014 = alt.Chart(mass_shootings_regions).transform_filter(
        alt.datum.Year == 2014
    ).mark_circle().encode(
        alt.Y('Year:O', title='Reference Year').axis(orient='right'),
        color = 'Year:O',
    )

    legend = alt.Chart(mass_shootings_regions).transform_filter(
        alt.datum.Year > 2014
    ).mark_circle().encode(
        alt.Y('Year:O').axis(orient='right'),
        color = color,
    ).add_params(selection_year)

    Q2_barchart_final = (Q2_years_barchart + Q2_2014_barchart).facet(column = 'Region:N') | (legend_2014 & legend)

    return Q2_barchart_final 


#################### Q3 ####################
# - map of states, select state and show a map for counties, slider to see years 

def main():
    mass_shootings = pd.read_csv('MassShootings.csv')
    counties_gdf = gpd.read_file('Counties.geojson')

    mass_shootings_regions, mass_shootings_states = general_data_preparation(mass_shootings)
    Q2_barchart_final = second_question(mass_shootings_regions)

    st.set_page_config(layout = 'wide')
    st.markdown('## Analysis of the evolution of Mass Shootings in the US')
    st.markdown('**Authors:** Raquel Jolis Carné and Martina Massana Massip')

    st.altair_chart(Q2_barchart_final, use_container_width=True)

if __name__ == '__main__':
    main()
