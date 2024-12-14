import streamlit as st
import pandas as pd
import altair as alt
import datetime as dt
from vega_datasets import data

st.set_page_config(layout = 'wide')

def general_data_preparation(mass_shootings):

    mass_shootings['Incident Date'] = pd.to_datetime(mass_shootings['Incident Date'])
    mass_shootings['Month_Year'] = mass_shootings['Incident Date'].dt.to_period('M').dt.to_timestamp()
    mass_shootings['Year'] = mass_shootings['Month_Year'].apply(lambda x: x.year)
    mass_shootings = mass_shootings.drop('Incident Date', axis=1)
 
    # grouping BY STATE AND MONTH
    mass_shootings_states = mass_shootings.groupby(['State', 'Month_Year', 'Year', 'FIPS', 'Region', 'Population']).size().reset_index(name='Total Shootings')
    
    # grouping BY REGION AND MONTH
    mass_shootings_regions = mass_shootings.groupby(['Region', 'Month_Year', 'Year']).size().reset_index(name='Total Shootings')
    region_population = mass_shootings_states.drop_duplicates('State').groupby(['Region'])['Population'].sum()
    mass_shootings_regions = mass_shootings_regions.merge(region_population, on='Region')
    
    return mass_shootings_regions, mass_shootings_states

def line_chart_states(mass_shootings_states, region_name, date_selection):

    state_selection = alt.selection_point(fields = ['State'])
    region_selection = alt.selection_point(fields = ['Region'])

    color_west = ['#6f0036','#e80576', '#d3088c', '#f967ae', '#68028b',  '#a80686', '#9c4088', '#dc09e3', '#920597', '#bd02f3', '#b20258']
    midwest_scale = alt.Scale(scheme='oranges')
    northeast_scale = alt.Scale(scheme='tealblues')
    southest_scale = alt.Scale(scheme='greens')
    southwest_scale = alt.Scale(scheme='blues')
    color_southwest = ['#020560', '#2b30c4', '#0072B2', '#7637f4']
    
    color_params_west = alt.condition(state_selection, alt.Color('State:N', scale = alt.Scale(range = color_west), legend = None), alt.value('lightgray'))
    color_params_midwest = alt.condition(state_selection, alt.Color('State:N', scale =  midwest_scale, legend = None), alt.value('lightgray'))
    color_params_northeast = alt.condition(state_selection, alt.Color('State:N', scale = northeast_scale, legend = None), alt.value('lightgray'))
    color_params_seast = alt.condition(state_selection, alt.Color('State:N', scale = southest_scale, legend = None), alt.value('lightgray'))
    color_params_swest = alt.condition(state_selection, alt.Color('State:N', scale = alt.Scale(range = color_southwest), legend = None), alt.value('lightgray'))
    
    if region_name == 'West':
        color = color_params_west
    elif region_name == 'Midwest':
        color = color_params_midwest
    elif region_name == 'Northeast':
        color = color_params_northeast
    elif region_name == 'Southwest':
        color = color_params_swest
    else:
        color = color_params_seast

    background_lines_states = alt.Chart(mass_shootings_states).mark_line(opacity=0.2).add_params(
        state_selection
    ).encode(
        alt.X('Month_Year:T', axis = alt.Axis(title = 'Date', format='%b %Y', labelAngle=-45, titleColor = 'black', labelColor = 'black', titleFontSize = 14, labelFontSize = 12)),
        alt.Y('Total Shootings:Q', axis = alt.Axis(titleColor = 'black', labelColor = 'black', titleFontSize = 14, labelFontSize = 12)),
        tooltip = ['State:N', 'Region:N', 'Month_Year:T', 'Total Shootings:Q'],
        color = color
    ).properties(
        width = 800,
        height = 400
    )  

    highlighted_line_states = alt.Chart(mass_shootings_states).mark_line().encode(
        alt.X('Month_Year:T'),
        alt.Y('Total Shootings:Q'),
        color=color,
        tooltip= ['State:N', 'Region:N', 'Month_Year:T', 'Total Shootings:Q'],
    ).transform_filter(
        state_selection 
    ) 

    upper_states = (background_lines_states  + highlighted_line_states).encode(
        alt.X('Month_Year:T', axis=alt.Axis(title = 'Date', format='%b %Y', labelAngle=-45, titleColor = 'black', labelColor = 'black', titleFontSize = 14, labelFontSize = 12)).scale(domain = date_selection)
    )

    legend = alt.Chart(mass_shootings_states).mark_circle(size=100).encode(
        alt.Y('State:N', axis = alt.Axis(title = region_name, titleColor = 'black', labelColor = 'black', titleFontSize = 14, labelFontSize = 12)),
        color = color
    ).add_params(
        state_selection
    )

    return upper_states, legend

def line_chart_regions(mass_shootings_regions, region_selection, date_selection, color_region):

    """ Returns the line chart of mass shootings over the years, differentiating the regions"""
    # Lines for all regions
    background_lines_regions = alt.Chart(mass_shootings_regions).mark_line(opacity=0.2).encode(
        alt.X('Month_Year:T', axis=alt.Axis(title = 'Date', format='%b %Y', labelAngle=-45, titleColor = 'black', labelColor = 'black', titleFontSize = 14, labelFontSize = 12)),
        alt.Y('Total Shootings:Q',axis = alt.Axis(titleColor = 'black', labelColor = 'black', titleFontSize = 14, labelFontSize = 12)),
        color = color_region,
        tooltip = ['Region:N', 'Month_Year:T', 'Total Shootings:Q']
    ).add_params(
        region_selection
    ).properties(
        width = 800,
        height = 400
    )  
    
    # Lines for all regions with reduced opacity (background lines)
    highlighted_line_regions = alt.Chart(mass_shootings_regions).mark_line().encode(
        alt.X('Month_Year:T'),
        alt.Y('Total Shootings:Q'),
        color=color_region,
        tooltip=['Region:N', 'Month_Year:T', 'Total Shootings:Q']
    ).transform_filter(
        region_selection  
    ) 

    # Upper chart: Combine background and highlighted lines
    upper_regions = (background_lines_regions + highlighted_line_regions).encode(
        alt.X('Month_Year:T', axis=alt.Axis(title = 'Date', format='%b %Y', labelAngle=-45, titleColor = 'black', labelColor = 'black', titleFontSize = 14, labelFontSize = 12)).scale(domain = date_selection)
    )

    # Lower chart: Range date selector
    lower_regions = (background_lines_regions + highlighted_line_regions).properties(
        height = 60
    ).add_params(date_selection)

    # Legend 
    legend = alt.Chart(mass_shootings_regions).mark_circle(size=100).encode(
        alt.Y('Region:N', axis = alt.Axis(title = 'Region', titleColor = 'black', labelColor = 'black', titleFontSize = 14, labelFontSize = 12)),
        color = color_region 
    ).add_params(region_selection)

    line_chart_regions = upper_regions & lower_regions

    Q1_first_chart = alt.hconcat(line_chart_regions, legend)

    return Q1_first_chart




def first_question(mass_shootings_regions, mass_shootings_states):
    
    #--------------- DATA PREPARATION ---------------#

    mass_shootings_regions = mass_shootings_regions.groupby(['Region', 'Month_Year', 'Year'])['Total Shootings'].sum().reset_index()
    mass_shootings_states = mass_shootings_states.groupby(['State', 'Region', 'Month_Year', 'Year','FIPS'])['Total Shootings'].sum().reset_index()

    mass_shootings_states['FIPS'] = pd.to_numeric(mass_shootings_states['FIPS'], errors='coerce')

    state_selection = alt.selection_point(fields = ['State'])
    region_selection = alt.selection_point(fields = ['Region'])
    date_selection = alt.selection_interval(encodings=['x'])

    color_palette = ['#E69F00', '#56B4E9', '#009E73', '#0072B2', '#CC79A7']
    region_order = sorted(mass_shootings_regions['Region'].unique())
    color_region = alt.condition(region_selection, alt.Color('Region:N', scale = alt.Scale(range = color_palette, domain = region_order), legend = None), alt.value('lightgray'))

    #--------------- REGION LINE CHART PLOTTING ---------------#
    Q1_first_chart = line_chart_regions(mass_shootings_regions, region_selection, date_selection, color_region)
    

    #--------------- CHOROPLETH PLOTTING ---------------#

    USA_states = alt.topo_feature(data.us_10m.url, 'states')

    state_shootings_map = alt.Chart(USA_states).transform_lookup(
        lookup = 'id',
        from_ = alt.LookupData(mass_shootings_states, 'FIPS', ['Region', 'State'])
    ).mark_geoshape(stroke = 'darkgray').encode(
        color=color_region,
        tooltip = ['Region:N', 'State:N']
    ).add_params(
        region_selection
    ).add_params(
        state_selection
    ).properties(
        title = 'US States by Region'
    ).project(type='albersUsa')


    #--------------- STATE LINE CHART PLOTTING ---------------#    
    chart_west, legend_west = line_chart_states(mass_shootings_states[mass_shootings_states['Region'] == 'West'],'West', date_selection)
    chart_seast, legend_seast = line_chart_states(mass_shootings_states[mass_shootings_states['Region'] == "Southeast"], "Southeast", date_selection)
    chart_swest, legend_swest = line_chart_states(mass_shootings_states[mass_shootings_states['Region'] == "Southwest"], "Southwest", date_selection)
    chart_midwest, legend_midwest = line_chart_states(mass_shootings_states[mass_shootings_states['Region'] == "Midwest"],  "Midwest", date_selection)
    chart_northeast, legend_northeast = line_chart_states(mass_shootings_states[mass_shootings_states['Region'] == "Northeast"], "Northeast", date_selection)

    all_chart_states = alt.layer(
        chart_west,
        chart_midwest,
        chart_northeast,
        chart_seast,
        chart_swest
    ).properties(
        width=800,
        height=400
    ).transform_filter(
        region_selection
    ).resolve_scale(color = 'independent')

    legend2 = alt.hconcat(legend_west, legend_midwest, legend_northeast, legend_seast, legend_swest).resolve_scale(color = 'independent').add_params(region_selection)

    Q1_second_line_chart = alt.hconcat(all_chart_states, legend2)

    Q1_final_chart_2 = alt.hconcat(Q1_first_chart, state_shootings_map)
    Q1_final_chart_2 = alt.vconcat(Q1_final_chart_2, Q1_second_line_chart)

    return Q1_final_chart_2


def second_question_barchart(mass_shootings_regions):
    #################### Q2 ####################
    # - grouped barcharts, pair of bars, one for 2014 and the other for the chosen year

    #--------------- DATA PREPARATION ---------------#

    mass_shootings_regions = mass_shootings_regions.drop('Month_Year', axis=1)
    mass_shootings_regions = mass_shootings_regions.groupby(['Region', 'Year', 'Population'])['Total Shootings'].sum().reset_index()
    mass_shootings_regions['Shootings per 10M citizens'] = mass_shootings_regions['Total Shootings'] / mass_shootings_regions['Population'] * 10**7

    
    #--------------- BAR CHART PLOTTING ---------------#

    Q2a_selection_year = alt.selection_point(encodings = ['color'])
    color = alt.condition(Q2a_selection_year,
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
    ).add_params(Q2a_selection_year)

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
    ).add_params(Q2a_selection_year)

    Q2_barchart_final = (Q2_years_barchart + Q2_2014_barchart).facet(column = 'Region:N') | (legend_2014 & legend)

    return Q2_barchart_final 


def second_question_slopechart(mass_shootings_regions):
    #################### Q2 ####################
    # - 5 juxtaposed region slope charts, each line a year comparison with 2014 (reference)

    #--------------- DATA PREPARATION ---------------#

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

    #--------------- SLOPE CHART PLOTTING ---------------#

    Q2b_year_selection = alt.selection_point(encodings = ['color'])

    color = alt.condition(Q2b_year_selection,
                        alt.Color('Year:N', legend = None, scale = alt.Scale(scheme='category10')),
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
        ).add_params(Q2b_year_selection)

        slopecharts_regions.append(slopechart)

    legend = alt.Chart(mass_shootings_regions).mark_circle(size = 70).encode(
        alt.Y('Year:N').axis(orient='right'),
        color = color,
    ).add_params(Q2b_year_selection)

    Q2_slopecharts = alt.hconcat(*slopecharts_regions)
    Q2_slopecharts_final = Q2_slopecharts | legend
    
    return Q2_slopecharts_final



def third_question(mass_shootings_states, mass_shootings, county_population, Q3_selection_year):
    #################### Q3 ####################
    # - map of states, select state and show a map for counties, slider to see years 

    #--------------- DATA PREPARATION ---------------#
    
    mass_shootings_states = mass_shootings_states.groupby(['FIPS', 'State'])['Total Shootings'].sum().reset_index()
    mass_shootings_states['Average Shootings'] = round(mass_shootings_states['Total Shootings'] / 10) # 10 years in 2014-2023

    missing_counties = pd.DataFrame([
        {'County FIPS': 2201, 'County Name': 'Prince of Wales-Outer Ketchikan, AK', 'County Population': 5696},
        {'County FIPS': 2232, 'County Name': 'Skagway-Hoonah-Angoon, AK', 'County Population': 2262},
        {'County FIPS': 2261, 'County Name': 'Valdez-Cordova, AK', 'County Population': 9202},
        {'County FIPS': 2270, 'County Name': 'Wade Hampton, AK', 'County Population': 8001},
        {'County FIPS': 2280, 'County Name': 'Wrangell-Petersburg, AK', 'County Population': 2064},
        {'County FIPS': 46113, 'County Name': 'Shannon County, SD', 'County Population': 13672},
        {'County FIPS': 51515, 'County Name': 'Bedford, VA', 'County Population': 6777},
    ])
    county_population = pd.concat([county_population, missing_counties], ignore_index=True)
    county_population = county_population[county_population['County FIPS']%1000 != 0] # erasing State FIPS

    #--------------- AVERAGE SHOOTINGS CHOROPLETH PLOTTING ---------------#

    USA_counties = alt.topo_feature(data.us_10m.url, 'counties')
    USA_states = alt.topo_feature(data.us_10m.url, 'states')

    domain = [2000, 100000, 1000000, 5000000, 10000000]
    color_range = ['#e0e0e0', '#b3b3b3', '#808080', '#4d4d4d', '#2d2d2d']

    Q3_state_selection = alt.selection_point(fields = ['State'])

    Q3_average_shootings = alt.Chart(USA_states).transform_lookup(
        lookup = 'id',
        from_ = alt.LookupData(mass_shootings_states, 'FIPS', list(mass_shootings_states.columns))
    ).mark_geoshape(
        stroke = 'darkgray',
        strokeWidth = 0.5
    ).encode(
        color = alt.Color(
            'Average Shootings:Q',
            legend = alt.Legend(
                title = 'Average Shootings per Year',
                titleColor = 'black',
                labelColor = 'black'
            ),
            scale = alt.Scale(scheme = 'lighttealblue')
        ),
        tooltip = ['State:N', 'Average Shootings:Q']
    ).properties(
        title = alt.TitleParams(
            text = 'Distribution of average shootings per year, by state',
            fontSize = 18,
            fontWeight = 'bold',
            color = 'black'),
        width = 650,
        height = 500
    ).project(type = 'albersUsa').add_params(Q3_state_selection)


    #--------------- YEARLY EVOLUTION CHOROPLETH PLOTTING ---------------#

    
    state_shape_base = alt.Chart(USA_states).transform_lookup(
        lookup = 'id',
        from_ = alt.LookupData(mass_shootings, 'FIPS', list(mass_shootings.columns))
    ).mark_geoshape(
        stroke = 'black',
        fill = 'transparent'
    ).encode(tooltip = ['State:N']).project(type = 'albersUsa')


    Q3_county_population_map = alt.Chart(USA_counties).transform_lookup(
        lookup = 'id',
        from_ = alt.LookupData(county_population, 'County FIPS', list(county_population.columns))
    ).mark_geoshape(
        stroke = 'darkgray',
        strokeWidth = 0.5,
        opacity = 0.7
    ).encode(
        color = alt.Color(
            'County Population:Q',
            legend = alt.Legend(
                title = 'County Population',
                titleColor = 'black',
                labelColor = 'black',
                labelLimit = 500
            ),
            scale=alt.Scale(domain=domain, range=color_range),
        ),
        tooltip = ['County Name:N', 'County Population:Q']
    ).project(type = 'albersUsa')


    Q3_county_shootings = alt.Chart(mass_shootings).mark_circle().encode(
        longitude = 'Longitude:Q',
        latitude = 'Latitude:Q',
        size = alt.value(12),
        color = alt.value('#003E5C'),
        opacity = alt.condition(alt.datum.Year == Q3_selection_year, alt.value(1), alt.value(0))
    ).project(type = 'albersUsa')


    selected_state_overlay = alt.Chart(USA_states).transform_lookup(
        lookup = 'id',
        from_ = alt.LookupData(mass_shootings_states, 'FIPS', list(mass_shootings_states.columns))
    ).mark_geoshape(strokeWidth = 0).encode(
        color = alt.value('white'),
        opacity = alt.condition(Q3_state_selection, alt.value(0), alt.value(1)),
        tooltip = ['State:N']
    ).project(type = 'albersUsa').properties(
        title = alt.TitleParams(
                text = 'Distribution of shootings per year, by state and county',
                fontSize = 18,
                fontWeight = 'bold',
                color = 'black')
    ).add_params(Q3_state_selection)
    

    selected_county_overlay = alt.Chart(USA_counties).transform_lookup(
        lookup = 'id',
        from_ = alt.LookupData(county_population, 'County FIPS', list(county_population.columns))
    ).mark_geoshape(fill = 'transparent').encode(tooltip = ['County Name:N']).project(type = 'albersUsa')
    

    Q3_left = Q3_average_shootings 
    Q3_right = alt.layer(state_shape_base, Q3_county_population_map, Q3_county_shootings, selected_state_overlay, selected_county_overlay
        ).properties(width = 650, height = 500)
    Q3_choropleths_final = alt.hconcat(Q3_left, Q3_right).resolve_scale(color = 'independent')
    
    return Q3_choropleths_final


def main():
    mass_shootings = pd.read_csv('MassShootings.csv')
    county_population = pd.read_csv('CountyPopulation.csv')

    mass_shootings_regions, mass_shootings_states = general_data_preparation(mass_shootings)

    st.markdown('## Analysis of the evolution of Mass Shootings in the US')
    st.markdown('**Authors:** Raquel Jolis Carné and Martina Massana Massip')

    Q1_linechart_final = first_question(mass_shootings_regions, mass_shootings_states)
    st.altair_chart(Q1_linechart_final)
    
    #Q1_linechart_final = prova(mass_shootings_regions, mass_shootings_states)
    #st.altair_chart(Q1_linechart_final)

    Q2_slopecharts_final = second_question_slopechart(mass_shootings_regions)
    st.altair_chart(Q2_slopecharts_final, use_container_width=True)
    
    Q3_selection_year = st.slider('Select a year:', min_value=2014, max_value=2023, step=1, value=2014)
    Q3_choropleths_final = third_question(mass_shootings_states, mass_shootings, county_population, Q3_selection_year)
    st.altair_chart(Q3_choropleths_final, use_container_width=True)


if __name__ == '__main__':
    main()
