import os
import streamlit as st
import pandas as pd

# Determine base directory and CSV path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, 'catering_items_weight_shares.csv')

@st.cache_data
# Load dataset
def load_data():
    return pd.read_csv(CSV_PATH)

df = load_data()

# Prepare cost lookup and default servings
grouped_costs = (
    df.groupby(['Item Name', 'Servings'])['Cost per Component ($)']
      .sum()
      .reset_index()
      .rename(columns={'Cost per Component ($)': 'Cost per Serving ($)'})
)
item_cost = dict(zip(grouped_costs['Item Name'], grouped_costs['Cost per Serving ($)']))
default_servings = dict(zip(grouped_costs['Item Name'], grouped_costs['Servings']))

# Build a description map based on components
desc_map = {}
for item, sub in df.groupby('Item Name'):
    comps = sorted(sub['Component'].unique())
    desc_map[item] = f"Includes: {', '.join(comps)}."

# Category assignments
category_map = {
    'Mini Quiche': 'appetizers', 'Spring Rolls': 'appetizers', 'Caprese Skewers': 'appetizers',
    'Shrimp Cocktail': 'appetizers', 'Bruschetta': 'appetizers', 'Deviled Eggs': 'appetizers',
    'Meatball Skewers': 'appetizers', 'Sushi Rolls': 'appetizers', 'Chicken Satay': 'appetizers',
    'Hummus with Pita': 'appetizers',

    'Chicken Cheesesteak': 'entrees', 'Beef Sliders': 'entrees', 'Mini Tacos': 'entrees',
    'Turkey Club Wrap': 'entrees', 'Cheese Fondue': 'entrees',

    'Veggie Platter': 'sides', 'Fruit Platter': 'sides', 'Cheese and Crackers': 'sides',
    'Spinach Artichoke Dip': 'sides',

    'Chocolate Covered Strawberries': 'desserts'
}

# Screen flow
def init_session_state():
    if 'screen' not in st.session_state:
        st.session_state.screen = 'info'
    if 'selected' not in st.session_state:
        st.session_state.selected = {}
    # Initialize form fields
    for field in ['name', 'email', 'event_type', 'event_date']:
        if field not in st.session_state:
            st.session_state[field] = '' if field != 'event_date' else None

init_session_state()

st.set_page_config(page_title="Catering Dashboard", layout="wide")

# Helper to build summary DataFrame
def build_summary():
    if not st.session_state.selected:
        return None
    return pd.DataFrame([
        (item, serv, item_cost[item], serv * item_cost[item])
        for item, serv in st.session_state.selected.items()
    ], columns=["Item Name", "Servings", "Cost per Serving ($)", "Total Cost ($)"])

# Info screen: collect user and event details
def info_screen():
    st.title("Event Details")
    st.session_state.name = st.text_input("Your Name", value=st.session_state.name)
    st.session_state.email = st.text_input("Email Address", value=st.session_state.email)
    st.session_state.event_type = st.text_input("Type of Event (e.g., Wedding, Corporate, Birthday)", value=st.session_state.event_type)
    st.session_state.event_date = st.date_input("Event Date", value=st.session_state.event_date)
    if st.button("Start Order"):
        st.session_state.screen = 'appetizers'

# Generic selection screen
def selection_screen(category, title):
    st.title(f"Select {title}")
    items = [item for item, cat in category_map.items() if cat == category]
    for item in items:
        with st.expander(f"{item} — ${item_cost[item]:.2f} per serving"):
            c1, c2 = st.columns([3, 1])
            include = c1.checkbox(f"Include {item}", key=f"inc_{category}_{item}")
            c1.write(desc_map[item])
            if include:
                servings = c2.slider(
                    label="Servings",
                    min_value=0,
                    max_value=default_servings[item] * 2,
                    value=st.session_state.selected.get(item, default_servings[item]),
                    step=1,
                    key=f"serv_{category}_{item}"
                )
                st.session_state.selected[item] = servings
            else:
                st.session_state.selected.pop(item, None)
    # Display running total
    summary_df = build_summary()
    total = summary_df['Total Cost ($)'].sum() if summary_df is not None else 0
    st.metric("Current Total", f"${total:.2f}")
    # Navigation
    back, forward = st.columns(2)
    with back:
        if st.button("Back") and category != 'appetizers':
            st.session_state.screen = screens[screens.index(category) - 1]
    with forward:
        label = "Next" if category != 'desserts' else "Review Summary"
        if st.button(label):
            st.session_state.screen = screens[screens.index(category) + 1]

# Summary screen
def summary_screen():
    st.title("📄 Final Catering Quote")
    # Display event info
    st.subheader("Event Information")
    st.write(f"**Name:** {st.session_state.name}")
    st.write(f"**Email:** {st.session_state.email}")
    st.write(f"**Event Type:** {st.session_state.event_type}")
    st.write(f"**Event Date:** {st.session_state.event_date}")
    # Display final quote
    summary_df = build_summary()
    if summary_df is not None:
        total = summary_df["Total Cost ($)"].sum()
        cols = st.columns([1, 2, 1])
        with cols[1]:
            st.subheader("Final Summary")
            st.dataframe(summary_df)
            st.metric("Grand Total", f"${total:.2f}")
    else:
        st.write("No items selected.")
    if st.button("Back to Desserts"):
        st.session_state.screen = 'desserts'

# Screen dispatcher
screens = ['info', 'appetizers', 'entrees', 'sides', 'desserts', 'summary']
if st.session_state.screen == 'info':
    info_screen()
elif st.session_state.screen != 'summary':
    selection_screen(st.session_state.screen, st.session_state.screen.capitalize())
else:
    summary_screen()
