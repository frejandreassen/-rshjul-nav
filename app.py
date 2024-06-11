import streamlit as st
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
import json

# Create a connection object
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data_from_gsheets():
    # Make sure the worksheet name and columns match your Google Sheets layout
    df = conn.read(ttl="1m")
    activities = []
    unique_id_counter = 1  # Initialize a counter to help create unique IDs
    for row in df.itertuples(index=False):
        # Create a unique ID by combining activity name, month abbreviation, and a counter
        unique_id = f"{row.Aktivitet}_{row.Månad[:3]}_{unique_id_counter}"
        activity = {
            "id": unique_id,
            "label": row.Aktivitet,
            "parent": row.Månad[:3],  # Assuming 'Månad' contains full month names
            "value": 1,  # Assigning a default value
            "description": f"Description of {row.Aktivitet}",
            "category": row.Kategori
        }
        activities.append(activity)
        unique_id_counter += 1
    return activities

def load_template_data(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data['data']

def prepare_data(data):
    ids = [item['id'] for item in data]
    labels = [item['label'] for item in data]
    parents = [item['parent'] for item in data]
    values = [item['value'] for item in data]
    categories = [item.get('category', '') for item in data]
    return ids, labels, parents, values, categories

def incorporate_activities(data, activities, selected_categories):
    filtered_activities = [act for act in activities if act['category'] in selected_categories]
    for activity in filtered_activities:
        data.append(activity)
        parent_item = next((item for item in data if item['id'] == activity['parent']), None)
        if parent_item and parent_item['value'] > 0:
            parent_item['value'] -= activity['value']
        else:
            for item in data:
                if item['parent'].startswith('Q') and item['id'] != activity['parent']:
                    item['value'] += activity['value']

# Load initial template data
template_data = load_template_data('template.json')
activities_data = load_data_from_gsheets()

# Streamlit multiselect widget to select categories
categories = [activity['category'] for activity in activities_data]
selected_categories = st.multiselect('Select Categories:', options=list(set(categories)), default=list(set(categories)))

# Prepare data repeatedly with a fresh template load
data = load_template_data('template.json')
incorporate_activities(data, activities_data, selected_categories)

# Extract ids, labels, parents, values, and categories for the sunburst chart
ids, labels, parents, values, categories = prepare_data(data)

# Create the sunburst chart using Plotly
fig = px.sunburst(
    ids=ids,
    names=labels,
    parents=parents,
    values=values,
    title="Näringslivsavdelningen Årshjul"
)
fig.update_traces(rotation=90)

# Display the plot in Streamlit
st.plotly_chart(fig, use_container_width=True)
# Markdown to display the link and editing note
st.markdown(
    "You can view and edit the data in this Google Sheet: "
    "[Edit Google Sheet](https://docs.google.com/spreadsheets/d/1fYiKbV1Cl0DZAwVA50J8xjBeYnxhUFHiHhmP6qvVoV0/edit?usp=sharing)"
)
