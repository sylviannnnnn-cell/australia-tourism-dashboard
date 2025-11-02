#!/usr/bin/env python
# coding: utf-8

# In[40]:


from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import pandas as pd
from pandas.api.types import CategoricalDtype


# ### Data processing

# In[41]:


app = Dash(__name__)
server = app.server


# In[42]:


# ========= rain and temp Data Loading =========
df=pd.read_csv('5010 rain and temp.csv', dtype={'City': str, 'Month': str})

# ========= Calculate Max and Min of Temp and Rainfall =========
temp_min, temp_max = df['temp'].min(), df['temp'].max()
rain_min, rain_max = df['rainfall'].min(), df['rainfall'].max()


# In[43]:


# ========= Trip Data Loading =========
df_trip = pd.read_csv('5010 trip.csv')
df_trip.columns = df_trip.columns.str.strip()
df_trip['State'] = df_trip['State'].astype(str).str.strip()

# ========= data processing =========
cols_to_clean = [
    "Daytrip Trips", "Daytrip Spend ($M)", "Overnight Trips", "Overnight Nights", "Overnight Spend ($M)",
    "Overnight Intrastate Trips", "Overnight Intrastate Nights", "Overnight Intrastate Spend ($M)"]

for c in cols_to_clean:
    df_trip[c] = (
        df_trip[c].astype(str)
        .str.replace(",", "", regex=False)
        .replace(["", "nan", "NaN"], pd.NA)
    )
    df_trip[c] = pd.to_numeric(df_trip[c], errors="coerce")

df_trip = df_trip.dropna(subset=cols_to_clean, how="any")

# ========= Map State Names =========
state_full = {
    'NSW': 'New South Wales', 'VIC': 'Victoria', 'QLD': 'Queensland', 'SA': 'South Australia',
    'WA': 'Western Australia', 'TAS': 'Tasmania', 'NT': 'Northern Territory', 'ACT': 'Australian Capital Territory'
}
state_map = {v: k for k, v in state_full.items()}
df_trip['State'] = df_trip['State'].replace(state_map)

# ========= Calculate Average Spend =========
df_trip["Avg Daytrip Spend ($)"] = (df_trip["Daytrip Spend ($M)"] * 1e6) / df_trip["Daytrip Trips"]
df_trip["Avg Overnight Spend ($)"] = (df_trip["Overnight Spend ($M)"] * 1e6) / df_trip["Overnight Nights"]
df_trip["Avg Overnight Intrastate Spend ($)"] = (df_trip["Overnight Intrastate Spend ($M)"] * 1e6) / df_trip["Overnight Intrastate Nights"]

# Define spending columns
spend_columns = ["Avg Daytrip Spend ($)", "Avg Overnight Spend ($)", "Avg Overnight Intrastate Spend ($)"]
# Calculate overall average spending per row (each state's average across all trip types)
df_trip['Overall Average Spend'] = df_trip[spend_columns].mean(axis=1)
# Find the state with the highest overall average spending
most_expensive_state = df_trip.groupby('State')['Overall Average Spend'].mean().idxmax()
# Get the average spending of that state (rounded to 2 decimal places)
most_expensive_value = round(df_trip.groupby('State')['Overall Average Spend'].mean().max(), 2)

# ========= Define spend columns =========
spend_cols = ["Avg Daytrip Spend ($)", "Avg Overnight Spend ($)", "Avg Overnight Intrastate Spend ($)"]

# ========= Color scheme =========
CB_SAFE = {
    "Avg Daytrip Spend ($)": "#0072B2",          # Blue
    "Avg Overnight Spend ($)": "#CC79A7",        # Pink
    "Avg Overnight Intrastate Spend ($)": "#E69F00"  # Orange
}



# In[44]:


# ========= Trip Amount Data Processing =========
# Define trip amount columns (only main types)
trip_cols = ["Daytrip Trips", "Overnight Trips"]

# ========= Calculate Number of Trips =========
def prepare_trip_data(trip_type):
    data = df_trip.copy()
    
    if trip_type != 'Both':
# Single trip type - calculate average by state
        grouped = data.groupby('State', as_index=False)[trip_type].mean().sort_values(trip_type, ascending=False)
        grouped['State Full'] = grouped['State'].map(state_full)
        return grouped, trip_type, [TRIP_COLORS[trip_type]]
    else:
# Both trip types - calculate total
        data['Total Trips'] = data['Daytrip Trips'] + data['Overnight Trips']
        grouped = data.groupby('State', as_index=False)['Total Trips'].mean().sort_values('Total Trips', ascending=False)
        grouped['State Full'] = grouped['State'].map(state_full)
        return grouped, 'Total Trips', [TRIP_COLORS["Total Trips"]]

# ========= Color scheme =========
TRIP_COLORS = {
    "Daytrip Trips": "#1f77b4",          # Blue
    "Overnight Trips": "#ff7f0e",        # Orange
    "Total Trips": "#9467bd"             # Purple 
}


# In[45]:


# ========= Trip Length Data Processing =========
# Calculate average length per trip (Overnight only)
df_trip["Avg Overnight Trip Length (Nights)"] = df_trip["Overnight Nights"] / df_trip["Overnight Trips"]
df_trip["Avg Overnight Intrastate Trip Length (Nights)"] = df_trip["Overnight Intrastate Nights"] / df_trip["Overnight Intrastate Trips"]

# Color scheme for trip length
LENGTH_COLORS = {
    "Avg Overnight Trip Length (Nights)": "#17becf",          # Teal
    "Avg Overnight Intrastate Trip Length (Nights)": "#bcbd22" # Yellow-green
}

# calculate trip length data
def prepare_trip_length_data(length_type):
    data = df_trip.copy()
    
    # Calculate average length by state
    grouped = data.groupby('State', as_index=False)[length_type].mean().sort_values(length_type, ascending=False)
    grouped['State Full'] = grouped['State'].map(state_full)
    return grouped, length_type, [LENGTH_COLORS[length_type]]# ========= Trip Length Data Processing =========
# Calculate average length per trip (Overnight only)
df_trip["Avg Overnight Trip Length (Nights)"] = df_trip["Overnight Nights"] / df_trip["Overnight Trips"]
df_trip["Avg Overnight Intrastate Trip Length (Nights)"] = df_trip["Overnight Intrastate Nights"] / df_trip["Overnight Intrastate Trips"]

# Color scheme for trip length
LENGTH_COLORS = {
    "Avg Overnight Trip Length (Nights)": "#17becf",          # Teal
    "Avg Overnight Intrastate Trip Length (Nights)": "#bcbd22" # Yellow-green
}

# calculate trip length data
def prepare_trip_length_data(length_type):
    data = df_trip.copy()
    
    # Calculate average length by state
    grouped = data.groupby('State', as_index=False)[length_type].mean().sort_values(length_type, ascending=False)
    grouped['State Full'] = grouped['State'].map(state_full)
    return grouped, length_type, [LENGTH_COLORS[length_type]]


# In[46]:


# ========= Geographic Data Processing =========
# Australian state coordinates (approximate center points)
state_coordinates = {
    'NSW': {'lat': -32.0, 'lon': 147.0},
    'VIC': {'lat': -36.5, 'lon': 144.5},
    'QLD': {'lat': -22.5, 'lon': 145.5},
    'SA': {'lat': -31.0, 'lon': 135.0},
    'WA': {'lat': -26.0, 'lon': 121.0},
    'TAS': {'lat': -42.0, 'lon': 147.0},
    'NT': {'lat': -19.0, 'lon': 133.0},
    'ACT': {'lat': -35.5, 'lon': 149.0}
}

# Color scheme for geographic maps
GEO_COLORS = {
    "Avg Overnight Trip Length (Nights)": "viridis",
    "Avg Overnight Intrastate Trip Length (Nights)": "plasma"
}

# Prepare geographic data for mapping
def prepare_geographic_data(length_type):
    data = df_trip.copy()
    
    # Calculate average length by state
    grouped = data.groupby('State', as_index=False)[length_type].mean()
    grouped['State Full'] = grouped['State'].map(state_full)
    
    # Add coordinates
    grouped['lat'] = grouped['State'].map(lambda x: state_coordinates[x]['lat'])
    grouped['lon'] = grouped['State'].map(lambda x: state_coordinates[x]['lon'])
    
    return grouped


# In[47]:


# ========= Axis styling =========
def style_axes(fig):
    fig.update_layout(
        title_x=0.0,
        xaxis=dict(showgrid=False, tickangle=0, tickfont=dict(size=12)),
        yaxis=dict(showgrid=True, gridcolor='rgba(230,230,230,0.4)', zeroline=False, title_font=dict(size=14)),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    return fig


# ### Layout

# In[48]:


# ========= Section 0:  Metric Cards =========
app.layout = html.Div(
    style={
        "backgroundImage": "url('/assets/bg.jpg')",
        "backgroundSize": "cover",
        "backgroundRepeat": "no-repeat",
        "backgroundPosition": "center",
        "minHeight": "100vh",
        "padding": "20px",
        "margin": "0"
    },
    children=[
        html.H1(
            "Find the Best Australian Destination for HOLIDAY!",
            style={
                "backgroundColor": "rgb(127, 166, 201,0.6)",
                "padding": "15px 20px",
                "textAlign": "center",
                "boxShadow": "0 4px 8px rgba(0,0,0,0.2)",
                'color':'white'
            }
        ),
        html.Div(
                style={
                    "display": "flex",
                    "justifyContent": "space-around",
                    "flexWrap": "wrap",
                    "gap": "20px",
                    "marginBottom": "30px"
                },
                children=[
                    html.Div(
                        [
                            html.H3("Most Popular State"),
                            html.P("NSW")
                        ],
                        style={
                            "backgroundColor": "rgba(255, 255, 255, 0.6)",
                            "borderRadius": "10px",
                            "padding": "20px",
                            "width": "220px",
                            "textAlign": "center",
                            "boxShadow": "0 4px 10px rgba(0,0,0,0.1)"
                        }
                    ),
                    html.Div(
                        [
                            html.H3("Most Expensive State"),
                            html.P("ACT")
                        ],
                        style={
                            "backgroundColor": "rgba(255, 255, 255, 0.6)",
                            "borderRadius": "10px",
                            "padding": "20px",
                            "width": "220px",
                            "textAlign": "center",
                            "boxShadow": "0 4px 10px rgba(0,0,0,0.1)"
                        }
                    ),
                    html.Div(
                        [
                            html.H3("Most Comfortable City"),
                            html.P("Hobart")
                        ],
                        style={
                            "backgroundColor": "rgba(255, 255, 255, 0.6)",
                            "borderRadius": "10px",
                            "padding": "20px",
                            "width": "220px",
                            "textAlign": "center",
                            "boxShadow": "0 4px 10px rgba(0,0,0,0.1)"
                        }
                    )
                ]
            ),
# ========= Section 1:  Temp & Rain Layout =========
        html.Div([
            html.H2("1) 🌅 Choose your favorite WEATHER for destination!"),
            html.Div([
                html.H4("Filter by Month:"),
                dcc.Dropdown(
                    id='month-filter',
                    options=(
                        [{'label': 'All Months', 'value': 'ALL'}] +
                        [{'label': m, 'value': m} for m in df['Month'].dropna().unique()]),
                    placeholder="Select month...",
                    multi=True,
                    value=['ALL']
                ),
            ], style={'width': '45%', 'display': 'inline-block', 'padding': '0 20px'}),
                html.Div([
                html.H4("Filter by City:"),
                dcc.Dropdown(
                    id='city-filter',
                    options=(
                        [{'label': 'All Cities', 'value': 'ALL'}] +
                        [{'label': c, 'value': c} for c in sorted(df['City'].dropna().unique())]),
                    multi=True,
                    placeholder="Select one or more cities...",
                    value=['ALL']
                ),
            ], style={'width': '45%', 'display': 'inline-block', 'padding': '0 20px'}),
        ], style={'justifyContent': 'center'}),
        html.Div([
            html.H4("Filter by Temperature Range (°C):"),
            dcc.RangeSlider(
                id='temp-slider',
                min=df['temp'].min(),
                max=df['temp'].max(),
                step=0.5,
                value=[df['temp'].min(), df['temp'].max()],
                marks={int(t): str(int(t)) for t in range(int(df['temp'].min()), int(df['temp'].max())+1, 5)},
                tooltip={"placement": "bottom", "always_visible": True}
            ),
        ], style={'width': '90%', 'margin': '0 auto', 'padding': '20px 0'}),
        html.Div([
            html.H4("Filter by Rainfall Range (mm):"),
            dcc.RangeSlider(
                id='rain-slider',
                min=df['rainfall'].min(),
                max=df['rainfall'].max(),
                step=0.5,
                value=[df['rainfall'].min(), df['rainfall'].max()],
                marks={int(r): str(int(r)) for r in range(int(df['rainfall'].min()), int(df['rainfall'].max())+1, 50)},
                tooltip={"placement": "bottom", "always_visible": True}
            ),
        ], style={'width': '90%', 'margin': '0 auto', 'padding': '20px 0'}),
        html.Br(),
        html.Div(id='metric-cards', style={'display': 'flex', 'justifyContent': 'center', 'gap': '40px'}),
        html.Br(),
        dcc.Graph(id='temp-chart'),

# ========= Section 2:  Spend Layout =========
        html.H2("2) 💰 Average Spend per Day",
                style={'textAlign': 'left', 'marginLeft': '40px', 'marginBottom': '0', 'fontWeight': 'bold','color':'white'}),
        html.Div([
            html.Label("Trip Type:", style={'fontWeight': 'bold', 'marginRight': '10px', 'fontSize': '16px','color':'white'}),
            dcc.Dropdown(
                id='spend-type-dd',
                options=[
                    {'label': 'Daytrip Spend', 'value': 'Avg Daytrip Spend ($)'},
                    {'label': 'Overnight Spend', 'value': 'Avg Overnight Spend ($)'},
                    {'label': 'Overnight Intrastate Spend', 'value': 'Avg Overnight Intrastate Spend ($)'},
                    {'label': 'All Types', 'value': 'All'}
                ],
                value='Avg Daytrip Spend ($)',
                clearable=False,
                style={'width': '300px','color':'white'}
            )
        ], style={ 'display': 'flex','justifyContent': 'flex-end','marginRight': '40px'}),
        html.Div([
            dcc.Graph(id='spend-chart', style={"backgroundColor": "rgba(255, 255, 255, 0.6)",'width': '95%', 'margin': 'auto'})
        ]),


# ========= Section 3: Trip Amount Layout =========
        html.H2("3) 👥 Number of Trips by State",
                style={'textAlign': 'left', 'marginLeft': '40px', 'marginBottom': '0', 'fontWeight': 'bold','color':'white'}),
        html.Div([
            html.Label("Trip Type:", style={'fontWeight': 'bold', 'marginRight': '10px', 'fontSize': '16px'}),
            dcc.Dropdown(
                id='trip-amount-type-dd',
                options=[
                    {'label': 'Daytrip Trips', 'value': 'Daytrip Trips'},
                    {'label': 'Overnight Trips', 'value': 'Overnight Trips'},
                    {'label': 'Both Trip Types', 'value': 'Both'}
                ],
                value='Daytrip Trips',
                clearable=False,
                style={'width': '300px'}
            )
        ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'flex-end', 'marginRight': '40px', 'marginLeft': 'auto','color':'white'}),
        html.Div([
            dcc.Graph(id='trip-amount-chart', style={"backgroundColor": "rgba(255, 255, 255, 0.6)",'width': '95%', 'margin': 'auto'})
        ]),



# ========= Section 4: Trip Length Layout =========
        html.H2("4) 🌃Average Overnight Trip Length ",
                style={'textAlign': 'left', 'marginLeft': '40px', 'marginBottom': '0', 'fontWeight': 'bold','color':'white'}),
        html.Div([
            html.Label("Trip Type:", style={'fontWeight': 'bold', 'marginRight': '10px', 'fontSize': '16px'}),
            dcc.Dropdown(
                id='geo-length-type-dd',
                options=[
                    {'label': 'Overnight Trip Length', 'value': 'Avg Overnight Trip Length (Nights)'},
                    {'label': 'Overnight Intrastate Trip Length', 'value': 'Avg Overnight Intrastate Trip Length (Nights)'}
                ],
                value='Avg Overnight Trip Length (Nights)',
                clearable=False,
                style={'width': '300px'}
            )
        ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'flex-end', 'marginRight': '40px', 'marginLeft': 'auto','color':'white'}),
        html.Div([
            dcc.Graph(id='geo-length-chart', style={'width': '95%', 'height': '600px', 'margin': 'auto'})
        ]),
#Data Note:
        html.Div([
            html.Hr(),
            html.Div("Data note: Tourism, weather and expenditure data are aggregated from Tourism Research Australia and Bureau of Meteorology.",
                     style={'fontSize': '12px', 'color': '#555', 'textAlign': 'center',
                            'backgroundColor': 'rgba(255, 255, 255, 0.6)', 'padding': '10px', 'borderRadius': '8px'})
        ], style={'marginTop': '30px'}),
    ]
)


# ### Callback

# In[49]:


# ========= Section 1:  Temp & Rain Callback =========
@app.callback(
    [Output('temp-chart', 'figure'),
     Output('metric-cards', 'children')],
    [Input('city-filter', 'value'),
     Input('month-filter', 'value'),
     Input('temp-slider', 'value'),
     Input('rain-slider', 'value')]
)
def update_dashboard(selected_cities, selected_month, temp_range, rain_range):
    filtered_df = df.copy()
    if not selected_month or 'ALL' in selected_month:
        pass
    else:
        filtered_df = filtered_df[filtered_df['Month'].isin(selected_month)]
    if not selected_cities or 'ALL' in selected_cities:
        pass
    else:
        filtered_df = filtered_df[filtered_df['City'].isin(selected_cities)]
    min_temp, max_temp = temp_range
    filtered_df = filtered_df[(filtered_df['temp'] >= min_temp) & (filtered_df['temp'] <= max_temp)]
    min_rain, max_rain = rain_range
    filtered_df = filtered_df[(filtered_df['rainfall'] >= min_rain) & (filtered_df['rainfall'] <= max_rain)]
    if filtered_df.empty:
        fig = px.scatter(title="No data available for this selection.")
        return fig, [html.Div("No data found.", style={'color': 'gray', 'textAlign': 'center'})]
    avg_temp = filtered_df['temp'].mean()
    avg_rain = filtered_df['rainfall'].mean()
    cards = [
        html.Div([
            html.H3(f"{avg_temp:.1f}°C", style={'textAlign': 'center', 'color': '#0074D9'}),
            html.P("Average Temperature", style={'textAlign': 'center'})
        ]),
        html.Div([
            html.H3(f"{avg_rain:.1f} mm", style={'textAlign': 'center', 'color': '#FF4136'}),
            html.P("Average Rainfall", style={'textAlign': 'center'})
        ])
    ]
    fig = px.scatter(
        filtered_df,
        x='temp',
        y='rainfall',
        color='City',
        hover_data=['Month'],
        title=f"Temperature vs Rainfall in {selected_month} (Filtered Temp {min_temp:.1f}°C–{max_temp:.1f}°C, Rain {min_rain:.1f}–{max_rain:.1f} mm)"
    )
    fig.update_traces(marker=dict(size=15))
    fig.update_layout(xaxis_title="Temperature (°C)",
                      yaxis_title="Rainfall (mm)",
                      plot_bgcolor='rgba(255, 255, 255, 0.6)',
                      paper_bgcolor='rgba(255, 255, 255, 0.6)')
    return fig, cards



# ========= Section 2:  Spend Callback =========
@app.callback(
    Output('spend-chart', 'figure'),
    Input('spend-type-dd', 'value')
)
def update_spend_chart(spend_label):
    try:
        data = df_trip.copy()
        if data.empty:
            return px.bar(title="No data loaded")

        # -------- Single Trip Type --------
        if spend_label != 'All':
            col = spend_label
            grouped = data.groupby('State', as_index=False)[col].mean().sort_values(col, ascending=False)
            grouped['State Full'] = grouped['State'].map(state_full)

            color_seq = [CB_SAFE[col]]
            fig = px.bar(
                grouped, x='State', y=col, text=grouped[col].round(0),
                color_discrete_sequence=color_seq, custom_data=['State Full'])

            fig.update_traces(
                texttemplate='%{text:,.0f}', textposition='outside',
                hovertemplate='State=%{customdata[0]}<br>Avg Spend=%{y:,.0f} $<extra></extra>',
                marker=dict(line=dict(width=0, color='rgba(0,0,0,0)'), opacity=1.0),
                cliponaxis=False)

            fig.update_layout(
                title=f"{spend_label} by State", yaxis_title="Average Spend per Day ($)",
                xaxis_title="State", showlegend=False,
                plot_bgcolor='rgba(255, 255, 255, 0.3)',
                paper_bgcolor='rgba(255, 255, 255, 0.3)')

            return style_axes(fig)

        # -------- All Trip Types --------
        melted = data.melt(id_vars=['State'], value_vars=spend_cols, var_name='Spend Type',
                           value_name='Avg Spend ($)').dropna(subset=['Avg Spend ($)'])

        melted = (melted.groupby(['State', 'Spend Type'], as_index=False)['Avg Spend ($)'].mean())

        melted['State Full'] = melted['State'].map(state_full)

        # Fixed order Orange → Pink → Blue
        type_order = ["Avg Overnight Intrastate Spend ($)", "Avg Overnight Spend ($)", "Avg Daytrip Spend ($)"]
        melted['Spend Type'] = pd.Categorical(melted['Spend Type'], categories=type_order, ordered=True)

        # Sort by orange column
        orange_col = "Avg Overnight Intrastate Spend ($)"
        orange_order = (data.groupby('State')[orange_col].mean().sort_values(ascending=False).index.tolist())

        melted['State'] = pd.Categorical(melted['State'], categories=orange_order, ordered=True)
        melted = melted.sort_values(['State', 'Spend Type'], ascending=[True, True])

        fig = px.bar(
            melted, x='State', y='Avg Spend ($)', color='Spend Type',
            color_discrete_map=CB_SAFE, barmode='group',
            category_orders={'Spend Type': type_order, 'State': orange_order},
            custom_data=['Spend Type', 'State Full']
        )

        fig.update_traces(
            marker=dict(line=dict(width=0, color='rgba(0,0,0,0)'), opacity=1.0),
            hovertemplate='State=%{customdata[1]}<br>Type=%{customdata[0]}<br>Avg Spend=%{y:,.0f} $<extra></extra>',
            cliponaxis=False
        )

        fig.update_layout(
            title="Average Daily Spend Comparison across Trip Types",
            yaxis_title="Average Spend per Day ($)", xaxis_title="State", legend_title="Trip Type",
            plot_bgcolor='rgba(255, 255, 255, 0.6)',
            paper_bgcolor='rgba(255, 255, 255, 0.6)')

        return style_axes(fig)

    except Exception as e:
        return px.bar(title=f"❌ Error: {e}")


# In[50]:


# ========= Section 3: Trip Amount Callback =========
@app.callback(
    Output('trip-amount-chart', 'figure'),
    Input('trip-amount-type-dd', 'value')
)
def update_trip_amount_chart(trip_type):
    try:
        if df_trip.empty:
            return px.bar(title="No data loaded")

        # Get pre-calculated data from data processing
        grouped, column, color_seq = prepare_trip_data(trip_type)
        
        # Create figure based on pre-calculated data
        fig = px.bar(
            grouped, x='State', y=column, text=grouped[column].round(0),
            color_discrete_sequence=color_seq, custom_data=['State Full'])

        fig.update_traces(
            texttemplate='%{text:,.0f}', textposition='outside',
            hovertemplate='State=%{customdata[0]}<br>Number of Trips=%{y:,.0f}<extra></extra>',
            marker=dict(line=dict(width=0, color='rgba(0,0,0,0)'), opacity=1.0),
            cliponaxis=False)

        # Set titles based on trip type
        if trip_type != 'Both':
            title = f"Number of {trip_type} by State"
            y_title = "Number of Trips"
        else:
            title = "Total Number of Trips (Daytrip + Overnight) by State"
            y_title = "Total Number of Trips"

        fig.update_layout(
            title=title, 
            yaxis_title=y_title,
            xaxis_title="State", 
            showlegend=False,
            plot_bgcolor='rgba(255, 255, 255, 0.3)',
            paper_bgcolor='rgba(255, 255, 255, 0.3)')

        return style_axes(fig)

    except Exception as e:
        return px.bar(title=f"❌ Error: {e}")


# In[51]:


# ========= Section 4: Trip Length Callback =========
@app.callback(
    Output('geo-length-chart', 'figure'),
    Input('geo-length-type-dd', 'value')
)
def update_geographic_chart(length_type):
    try:
        if df_trip.empty:
            return px.scatter_geo(title="No data loaded")

        # Get pre-calculated geographic data
        geo_data = prepare_geographic_data(length_type)
        
        # Create bubble map
        fig = px.scatter_geo(
            geo_data,
            lat='lat',
            lon='lon',
            size=length_type,
            color=length_type,
            hover_name='State Full',
            hover_data={length_type: ':.1f', 'lat': False, 'lon': False},
            size_max=30,
            projection='natural earth',
            title=f"Average Overnight Trip Length - Geographic Distribution",
            color_continuous_scale=GEO_COLORS[length_type]
        )
        
        # Customize Australia-focused view
        fig.update_geos(
            visible=False,
            resolution=50,
            showcountries=True,
            countrycolor="Black",
            showsubunits=True,
            subunitcolor="Blue",
            scope='world',
            center=dict(lat=-25, lon=135),  # Center on Australia
            projection_scale=3  # Zoom on Australia
        )
        
        fig.update_layout(
            title_x=0.5,
            geo=dict(
                bgcolor='rgba(0,0,0,0)',
                lakecolor='#0e9aa7',
                landcolor='lightgray'
            ),plot_bgcolor='rgba(255, 255, 255, 0.6)',
            paper_bgcolor='rgba(255, 255, 255, 0.6)'
        )
        
        # Customize bubble appearance
        fig.update_traces(
            marker=dict(
                sizemode='area',
                sizeref=2.*max(geo_data[length_type])/(30.**2),
                sizemin=4,
                line=dict(width=2, color='darkgray')
            ),
            selector=dict(mode='markers')
        )
        
        return fig

    except Exception as e:
        return px.scatter_geo(title=f"❌ Error: {e}")


# In[52]:


# ========= Run Server =========
if __name__ == '__main__':
    app.run(debug=True)

