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
