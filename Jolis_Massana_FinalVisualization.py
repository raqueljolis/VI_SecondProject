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
    mass_shootings['Year'] = mass_shootings['Month_Year'].apply(lambda x: x.year)
    mass_shootings = mass_shootings.drop('Incident Date', axis=1)
 
    # grouping BY STATE AND MONTH
    mass_shootings_states = mass_shootings.groupby(['State', 'Month_Year', 'Year', 'Region', 'Population']).size().reset_index(name='Total Shootings')
    
    # grouping BY REGION AND MONTH
    mass_shootings_regions = mass_shootings.groupby(['Region', 'Month_Year', 'Year']).size().reset_index(name='Total Shootings')
    region_population = mass_shootings_states.drop_duplicates('State').groupby(['Region'])['Population'].sum()
    mass_shootings_regions = mass_shootings_regions.merge(region_population, on='Region')
    
    return mass_shootings_regions, mass_shootings_states

#################### Q1 ####################
# - linechart, 5 lines, a line per region, being able to choose years
# - map with regions, select state --> linechart with all states of the region


def second_question_barchart(mass_shootings_regions):
    #################### Q2 ####################
    # - grouped barcharts, pair of bars, one for 2014 and the other for the chosen year

    #################### DATA PREPARATION ####################
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


def second_question_slopechart(mass_shootings_regions):
    #################### Q2 ####################
    # - 5 juxtaposed region slope charts, each line a year comparison with 2014 (reference)

    #################### DATA PREPARATION ####################
    mass_shootings_regions = mass_shootings_regions.groupby(['Region', 'Year', 'Population'])['Total Shootings'].sum().reset_index()

    # defining the proportion by population
    mass_shootings_regions['Shootings per 10M citizens'] = mass_shootings_regions['Total Shootings'] / mass_shootings_regions['Population'] * 10**7
    mass_shootings_regions = mass_shootings_regions.drop(['Population', 'Total Shootings'], axis=1)

    # for the sake of correct slope chart plotting 
    mass_shootings_regions['Comparison'] = mass_shootings_regions['Year'].apply(lambda x: '2014' if x == 2014 else 'Comparison Year')

    mass_shootings_2014 = mass_shootings_regions[mass_shootings_regions['Year'] == 2014].drop(['Year', 'Comparison'], axis=1)
    mass_shootings_regions = mass_shootings_regions[mass_shootings_regions['Year'] != 2014]

    for region in mass_shootings_regions['Region'].unique():
        for year in mass_shootings_regions['Year'].unique():
        new_row = pd.DataFrame({
            'Region': [region],
            'Year': [year],
            'Comparison': ['2014'],
            'Shootings per 10M citizens': [mass_shootings_2014[mass_shootings_2014['Region'] == region]['Shootings per 10M citizens'].iloc[0]]
        })
        
        mass_shootings_regions = pd.concat([mass_shootings_regions, new_row], ignore_index=True)

    # separating the dataset by regions for posterior plot juxtaposition
    mass_shootings_midwest = mass_shootings_regions[mass_shootings_regions['Region'] == 'Midwest']
    mass_shootings_northeast = mass_shootings_regions[mass_shootings_regions['Region'] == 'Northeast']
    mass_shootings_southeast = mass_shootings_regions[mass_shootings_regions['Region'] == 'Southeast']
    mass_shootings_southwest = mass_shootings_regions[mass_shootings_regions['Region'] == 'Southwest']
    mass_shootings_west = mass_shootings_regions[mass_shootings_regions['Region'] == 'West']

    #################### SLOPECHART PLOTTING ####################
    select_year = alt.selection_point(encodings = ['color'])

    color = alt.condition(select_year,
                        alt.Color('Year:N', legend = None),
                        alt.value('rgba(169, 169, 169, 0.3)')) # different color and lower opacity

    slopecharts_regions = list()
    region_dfs = [mass_shootings_midwest, mass_shootings_northeast, mass_shootings_southeast, mass_shootings_southwest, mass_shootings_west]
    region_names = ['Midwest', 'Northeast', 'Southeast', 'Southwest', 'West']

    for i in range(len(region_dfs)):
        df = region_dfs[i]
        region = region_names[i]

        slopechart = alt.Chart(df).mark_line(point = True).encode(
            x = alt.X('Comparison:N', 
                    title = 'Time', 
                    axis = alt.Axis(labelAngle = 45)), # rotation for better readibility
            y = alt.Y('Shootings per 10M citizens:Q', 
                scale = alt.Scale(domain = [4,30]),  
                title = 'Shootings per 10M citizens'),
            color = color,
            tooltip = 'Shootings per 10M citizens:Q'
        ).properties(title = alt.TitleParams(
            text = f'{region}',
            fontSize = 15,
            color = 'black',
            fontWeight='bold'),
                    width = 150,
                    height = 400
        ).add_params(select_year)

        slopecharts_regions.append(slopechart)

    legend = alt.Chart(mass_shootings_regions).mark_circle(size = 70).encode(
        alt.Y('Year:N').axis(orient='right'),
        color = color,
    ).add_params(select_year)

    Q2_slopecharts = alt.hconcat(*slopecharts_regions)
    Q2_slopecharts_final = Q2_slopecharts | legend
    
    return Q2_slopecharts_final



def third_question(mass_shootings, counties_gdf):
    #################### Q3 ####################
    # - map of states, select state and show a map for counties, slider to see years 

    # to perform spatial join and intersect shooting coordinates with actual counties
    geometry = [Point(lon_lat) for lon_lat in zip(mass_shootings['Longitude'], mass_shootings['Latitude'])]
    mass_shootings_gdf = gpd.GeoDataFrame(mass_shootings[['State', 'FIPS']], geometry=geometry)

    counties_gdf = counties_gdf[['STATEFP', 'GEOID', 'NAME', 'geometry']] # reducing dimensionality
    # dropping Puerto Rico, because it is outside of the North America region
    counties_gdf = counties_gdf[counties_gdf['STATEFP'] != '72'] 

    # swapping coordinates
    def swap_coordinates(geometry):
        if isinstance(geometry, Polygon): 
            return Polygon([(lon, lat) for lat, lon in geometry.exterior.coords])
        elif isinstance(geometry, MultiPolygon): 
            return  MultiPolygon([Polygon([(lat, lon) for (lat, lon) in polygon.exterior.coords]) for polygon in geometry.geoms])

    counties_gdf['geometry'] = counties_gdf['geometry'].apply(swap_coordinates) # swapping each row of the geometry column

    # setting and ensuring the use of the same coordinate system 
    mass_shootings_gdf.set_crs(epsg=4326, inplace=True)
    counties_gdf = counties_gdf.to_crs(mass_shootings_gdf.crs)

    coordinates_w_counties = mass_shootings_gdf.sjoin(counties_gdf, how='right', predicate='within')
    # 'how=right' to ensure we keep all counties and their FIPS, even if there's no coordinate data for them in the mass_shootings dataframe
    coordinates_w_counties = coordinates_w_counties[['GEOID', 'FIPS']]
    coordinates_w_counties = coordinates_w_counties.set_axis(['FIPS', 'STATEFIPS'], axis=1)
    coordinates_w_counties['FIPS'] = coordinates_w_counties['FIPS'].astype(int)

    county_population = county_population[['FIPStxt', 'Area_Name', 'State', 'POP_ESTIMATE_2023']]
    # to take into account same County names in different States
    county_population['County'] = county_population['Area_Name'] + ', ' + county_population['State']
    county_population = county_population[['FIPStxt', 'County', 'POP_ESTIMATE_2023']]
    county_population = county_population.set_axis(['FIPS', 'COUNTYNAME', 'COUNTYPOPULATION'], axis=1)
    
    coordinates_w_counties = coordinates_w_counties.merge(county_population, on='FIPS')

    county_shootings = {county: [0, 0, 0] for county in set(coordinates_w_counties['COUNTYNAME'])}
                              # ['County FIPS', 'Shootings', 'County Population']
    for _, row in coordinates_w_counties.iterrows():
        current_county = row['COUNTYNAME']
        current_county_FIPS = row['FIPS']
        current_county_population = row['COUNTYPOPULATION']
        if current_county_population is None:
            current_county_population = 0
        elif current_county_population is not None and type(current_county_population) == str: 
            current_county_population = int(row['COUNTYPOPULATION'].replace(',', ''))
        
        county_shootings[current_county][0] = current_county_FIPS 
        
        # we only want to sum occurrences if we have shooting data for it
        if pd.notna(row['STATEFIPS']):
            county_shootings[current_county][1] += 1 # occurrence count
        # if there's no data for this county in the original dataset, we keep the 'count' at 0

        county_shootings[current_county][2] = current_county_population

    county_shootings = pd.DataFrame.from_dict(county_shootings, orient='index',
                                              columns=['County FIPS', 'Total Shootings', 'County Population'])

    county_shootings['Shootings per 100K habitants'] = county_shootings['Total Shootings'] * 1 / county_shootings['County Population'] * 10**5 # 10**5 is a scaling factor
    county_shootings.fillna(0, inplace=True)

    full_FIPS_list = data.unemployment() # contains all FIPS inside the USA area in the column 'id', plottable in Altair
    # adding the remaining rows of 'unemployment_df['id']' to have all plotable county FIPS
    for f in full_FIPS_list['id']:
        if f not in set(county_shootings['County FIPS']):  
            num_of_rows = county_shootings.shape[0] 
            county_shootings.loc[num_of_rows] = [f, 0, 0, 0]

    # only keeping County FIPS
    county_shootings = county_shootings[county_shootings['County FIPS'].isin(set(full_FIPS_list['id']))]
    
    county_shootings = county_shootings.reset_index().rename(columns={'index': 'County'})

def main():
    mass_shootings = pd.read_csv('MassShootings.csv')
    counties_gdf = gpd.read_file('Counties.geojson')

    mass_shootings_regions, mass_shootings_states = general_data_preparation(mass_shootings)
    Q2_barchart_final = second_question_barchart(mass_shootings_regions)
    Q2_slopecharts_final = second_question_slopechart(mass_shootings_regions)

    st.set_page_config(layout = 'wide')
    st.markdown('## Analysis of the evolution of Mass Shootings in the US')
    st.markdown('**Authors:** Raquel Jolis Carné and Martina Massana Massip')

    st.altair_chart(Q2_slopecharts_final, use_container_width=True)

if __name__ == '__main__':
    main()
