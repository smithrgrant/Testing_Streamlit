import os
import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- Configuration ---
st.set_page_config(page_title="Catering Dashboard", layout="wide")

# --- Custom CSS for Aesthetic UI ---
st.markdown("""
<style>
/* Full-screen gradient background */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #4ca1af, #2c3e50);
    color: #ecf0f1;
    font-family: 'Roboto', sans-serif;
    padding: 2rem;
}
/* Sidebar styling */
[data-testid="stSidebar"] {
    background: #1f2833;
    color: #ecf0f1;
    padding-top: 2rem;
}
/* Headers */
h1, h2, h3, .stTitle {
    color: #ff6f61;
    font-weight: 700;
}
/* Buttons styling */
.stButton>button {
    background-color: #ff6f61;
    color: #ffffff;
    border: none;
    border-radius: 12px;
    padding: 0.75rem 1.5rem;
    font-size: 1.1rem;
    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    transition: transform 0.1s ease;
}
.stButton>button:hover {
    background-color: #ff4f41;
    transform: translateY(-2px);
}
/* Expander card style */
.css-1rs6os.edgvbvh3 {
    background: rgba(0,0,0,0.4);
    color: #ecf0f1;
    border-radius: 12px;
    margin-bottom: 1rem;
    box-shadow: 0 2px 6px rgba(0,0,0,0.5);
}
/* Slider accent color */
.css-1kyxreq .css-1lcbmhc {
    color: #ff6f61;
}
/* Table styling */
.stDataFrame td, .stDataFrame th {
    background-color: rgba(0,0,0,0.6);
    color: #ecf0f1;
}
.stDataFrame tr:nth-child(even) td {
    background-color: rgba(255,255,255,0.05);
}
</style>
""", unsafe_allow_html=True)

# --- Load Data ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, 'catering_items_weight_shares.csv')
@st.cache_data
def load_data():
    return pd.read_csv(CSV_PATH)

df = load_data()

# --- Prepare Data ---
grouped = (
    df.groupby(['Item Name', 'Servings'])['Cost per Component ($)']
      .sum().reset_index()
      .rename(columns={'Cost per Component ($)': 'Cost per Serving ($)'})
)
item_cost = dict(zip(grouped['Item Name'], grouped['Cost per Serving ($)']))
default_servings = dict(zip(grouped['Item Name'], grouped['Servings']))
desc_map = {item: 'Includes: ' + ', '.join(sorted(sub['Component'].unique())) + '.'
            for item, sub in df.groupby('Item Name')}
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
screens = ['info', 'appetizers', 'entrees', 'sides', 'desserts', 'summary']

# --- Session State Initialization ---
st.session_state.setdefault('screen', 'info')
st.session_state.setdefault('selected', {})
st.session_state.setdefault('name', '')
st.session_state.setdefault('email', '')
st.session_state.setdefault('event_type', '')
st.session_state.setdefault('event_date', None)

# --- Email Helper ---
SMTP_SERVER = st.secrets.get('smtp_server') or os.environ.get('SMTP_SERVER')
SMTP_PORT = int(st.secrets.get('smtp_port', 587) or os.environ.get('SMTP_PORT', 587))
SMTP_USER = st.secrets.get('smtp_user') or os.environ.get('SMTP_USER')
SMTP_PASS = st.secrets.get('smtp_pass') or os.environ.get('SMTP_PASS')
FROM_EMAIL = SMTP_USER

def send_email(to_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = FROM_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)

# --- Build Summary DataFrame ---
def build_summary():
    sel = st.session_state['selected']
    if not sel:
        return None
    return pd.DataFrame([
        (item, sel[item], item_cost[item], round(sel[item] * item_cost[item], 2))
        for item in sel
    ], columns=['Item Name', 'Servings', 'Cost per Serving ($)', 'Total Cost ($)'])

# --- Navigation Callbacks ---
def go_to(screen):
    st.session_state['screen'] = screen

def start_order():
    go_to('appetizers')

def back_screen():
    idx = screens.index(st.session_state['screen'])
    go_to(screens[idx - 1])

def next_screen():
    idx = screens.index(st.session_state['screen'])
    go_to(screens[idx + 1])

def send_quote():
    df_sum = build_summary()
    lines = [
        f"Name: {st.session_state['name']}",
        f"Email: {st.session_state['email']}",
        f"Event Type: {st.session_state['event_type']}",
        f"Event Date: {st.session_state['event_date']}",
        "\nQuote Summary:"
    ]
    for _, row in df_sum.iterrows():
        lines.append(
            f"- {row['Item Name']}: {row['Servings']} x ${row['Cost per Serving ($)']} = ${row['Total Cost ($)']}"
        )
    lines.append(f"\nGrand Total: ${df_sum['Total Cost ($)'].sum():.2f}")
    send_email(st.session_state['email'], f"Your Catering Quote - {st.session_state['event_type']}", '\n'.join(lines))
    st.success("Quote sent successfully!")

# --- Screens ---
def info_screen():
    st.header("✨ Event Details")
    with st.form('info_form'):
        name_input = st.text_input("Your Name", value=st.session_state['name'])
        email_input = st.text_input("Email Address", value=st.session_state['email'])
        event_input = st.text_input("Type of Event", value=st.session_state['event_type'])
        date_input = st.date_input("Event Date", value=st.session_state['event_date'])
        submitted = st.form_submit_button("Start Order")
        if submitted:
            st.session_state['name'] = name_input
            st.session_state['email'] = email_input
            st.session_state['event_type'] = event_input
            st.session_state['event_date'] = date_input
            start_order()


def selection_screen(category):
    st.header(f"🍽️ Select {category.title()}")
    for item in [i for i, c in category_map.items() if c == category]:
        with st.expander(f"{item} — ${item_cost[item]:.2f}/serv"):
            col1, col2 = st.columns([3, 1])
            include = col1.checkbox(f"Include {item}", key=f"inc_{item}")
            col1.write(desc_map[item])
            if include:
                qty = col2.slider(
                    "Servings",
                    0,
                    default_servings[item] * 2,
                    st.session_state['selected'].get(item, default_servings[item]),
                    1,
                    key=f"qty_{item}"
                )
                st.session_state['selected'][item] = qty
            else:
                st.session_state['selected'].pop(item, None)
    df_sum = build_summary()
    total = df_sum['Total Cost ($)'].sum() if df_sum is not None else 0
    st.metric("💰 Current Total", f"${total:.2f}")
    cols = st.columns([1,1])
    cols[0].button("⬅️ Back", on_click=back_screen, disabled=(category=='appetizers'))
    cols[1].button("➡️ Next", on_click=next_screen)


def summary_screen():
    st.header("🎉 Final Catering Quote")
    st.subheader("Event Information")
    st.write(f"**Name:** {st.session_state['name']}")
    st.write(f"**Email:** {st.session_state['email']}")
    st.write(f"**Event Type:** {st.session_state['event_type']}")
    st.write(f"**Event Date:** {st.session_state['event_date']}")
    df_sum = build_summary()
    st.dataframe(df_sum, use_container_width=True)
    total = df_sum['Total Cost ($)'].sum() if df_sum is not None else 0
    st.metric("🏆 Grand Total", f"${total:.2f}")
    cols = st.columns([1,1])
    cols[0].button("⬅️ Back to Desserts", on_click=back_screen)
    cols[1].button("✉️ Send Quote", on_click=send_quote)

# --- Dispatcher ---
if st.session_state['screen'] == 'info':
    info_screen()
elif st.session_state['screen'] != 'summary':
    selection_screen(st.session_state['screen'])
else:
    summary_screen()
