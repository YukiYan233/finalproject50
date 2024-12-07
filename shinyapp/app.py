import geopandas as gpd
import pandas as pd
import folium
from folium import Choropleth
from shiny import App, render, ui
import os
import zipfile
import requests

file_path_new = r"C:\Users\mepr9\Downloads\basic-app\care_enrollment.csv"
data = pd.read_csv(file_path_new)

# Clean year column
data['Year'] = data['Enrollment Month'].str[0:4]

# Remove commas in the 'numbers' column
data['Count of Enrollees'] = data['Count of Enrollees'].str.replace(',', '')

data['Count of Enrollees'] = data['Count of Enrollees'].fillna(0).astype(int)

data['Count of Enrollees'] = data['Count of Enrollees'].astype(str).astype(int)



# Group by County and sum New and Renewed
grouped_data_1 = data.groupby(['County', 'Year'])[['Count of Enrollees'
]].sum()

# Reset the index (optional, to turn 'County' back into a column)
grouped_data_county = grouped_data_1.reset_index()


# Step 1: Download and extract the shapefile
url = "https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_us_county_20m.zip"
local_zip = "cb_2018_us_county_20m.zip"

response = requests.get(url)
with open(local_zip, "wb") as file:
    file.write(response.content)

with zipfile.ZipFile(local_zip, "r") as zip_ref:
    zip_ref.extractall("shapefiles")

# Verify extracted files
print("Extracted files:", os.listdir("shapefiles"))

# Step 2: Load the shapefile and filter California counties
california_map = gpd.read_file("shapefiles/cb_2018_us_county_20m.shp")
california_map = california_map[california_map['STATEFP'] == '06']  # Only California (state code '06')

# Step 4: Clean and merge the data
grouped_data_county['County'] = grouped_data_county['County'].str.lower()
california_map['NAME'] = california_map['NAME'].str.lower()

map_data = california_map.merge(grouped_data_county, left_on='NAME', right_on='County', how='left')
print(map_data)

## Convert Year Column to int
map_data['Year'] = map_data['Year'].astype(str).astype(int)


# Create the choropleth map using Folium
def create_interactive_map(selected_year):
    # Filter data by the selected year
    filtered_data = map_data[map_data['Year'] == selected_year]
    # Filter the data by the selected year
    # Create a folium map centered on California
    m = folium.Map(location=[36.7783, -119.4179], zoom_start=6)

    # Create a choropleth map
    Choropleth(
        geo_data=filtered_data,
        data=filtered_data,
        columns=['County', 'Count of Enrollees'],
        key_on='feature.properties.NAME',
        fill_color='YlOrRd',  # Color palette
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Total Enrollments'
    ).add_to(m)

    map_html = m._repr_html_()
    return map_html

# Define the UI for the Shiny app (with required arguments)
app_ui = ui.page_fluid(
    ui.input_select(
        id="year_selector",
        label="Select Year",
        choices=list(map(str, sorted(data['Year'].unique()))),  # Dynamic year choices
        selected=str(data['Year'].min())  # Default to the first year
    ),
    ui.output_ui("display_map")  # This is where the map will be displayed
)

# Define the server function for the Shiny app
def server(input, output, session):
    @output
    @render.ui
    def display_map():
        # Get the selected year from the dropdown
        selected_year = int(input.year_selector())
        # Create the interactive map and get the file path
        map_html_path = create_interactive_map(selected_year)
        # Embed the map using an iframe
        return ui.HTML(map_html_path)
        ##return ui.HTML(f'<iframe src="{map_html_path}" width="100%" height="500px"></iframe>')


# Create the Shiny app with the defined UI and server
app = App(app_ui, server)


