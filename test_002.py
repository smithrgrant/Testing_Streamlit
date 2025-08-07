import os
import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from urllib.parse import quote

AIRTABLE_TOKEN = st.secrets.get('airtable_token') or os.environ.get('AIRTABLE_TOKEN')
BASE_ID = st.secrets.get('base_id') or os.environ.get('BASE_ID')
TABLE_NAME = st.secrets.get('table_name') or os.environ.get('TABLE_NAME')

# URL-encode table name (handles spaces and special characters)
TABLE_NAME_ENCODED = quote(TABLE_NAME)

# Construct the API endpoint URL
url = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME_ENCODED}'

# Set the authorization header using personal access token
headers = {
    'Authorization': f'Bearer {AIRTABLE_TOKEN}'
}



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

# --- Load Data (from CSV) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, 'a6af56ca-97ab-4f46-a48a-89d49230980b.csv')
@st.cache_data
def load_data():
    records = []
    offset = None

    while True:
        # Include the view name in the query parameters
        params = {
            # 'view': VIEW_NAME,
            'pageSize': 100

        }
        if offset:
            params['offset'] = offset

        # Send the request
        response = requests.get(url, headers=headers, params=params)
        # print('REPONSE:')
        # print(response.status_code, response.text)
        response.raise_for_status()

        data = response.json()
        records.extend(data['records'])

        
        # Pagination handling
        offset = data.get('offset')
        if not offset:
            break

    # Convert the result to a pandas DataFrame
    df = pd.json_normalize([r['fields'] for r in records])    
    df['Cost Per Serving'] = df['Cost Per Serving'].astype(float)
    df['Description'] = df.get('Description', '').fillna('')
    return df

df = load_data()

# --- Prepare Data ---
from ast import literal_eval

item_cost = dict(zip(df['Item Name'], df['Cost Per Serving']))
default_servings = {item: 1 for item in df['Item Name']}
desc_map = dict(zip(df['Item Name'], df['Description']))

# Parse and flatten 'Name (from Primary Tag)' into tags list
primary_raw = df['Name (from Primary Tag)'].dropna()
primary_list = []
for cell in primary_raw:
    # Attempt to parse list-like strings
    if isinstance(cell, str) and cell.strip().startswith('['):
        try:
            items = literal_eval(cell)
        except Exception:
            items = [cell]
    elif isinstance(cell, list):
        items = cell
    else:
        items = [cell]
    for tag in items:
        primary_list.append(tag)
# Deduplicate preserving order
tags = []
seen = set()
for t in primary_list:
    if t not in seen:
        seen.add(t)
        tags.append(t)

# Map each item to its first Primary Tag string
category_map = {}
for item, cell in zip(df['Item Name'], df['Name (from Primary Tag)']):
    if isinstance(cell, str) and cell.strip().startswith('['):
        try:
            vals = literal_eval(cell)
        except Exception:
            vals = [cell]
    elif isinstance(cell, list):
        vals = cell
    else:
        vals = [cell]
    category_map[item] = vals[0]

# Define screens sequence
screens = ['info'] + tags + ['summary']

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

def send_email(to_email, subject, html_body):
    msg = MIMEMultipart('alternative')
    msg['From'] = FROM_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(html_body, 'html'))
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
    ], columns=['Item Name', 'Servings', 'Unit Price ($)', 'Line Total ($)'])

# --- Callbacks ---
def go_to(screen):
    st.session_state['screen'] = screen

def start_order():
    go_to(tags[0] if tags else 'summary')

def back_screen():
    idx = screens.index(st.session_state['screen'])
    go_to(screens[idx - 1])

def next_screen():
    idx = screens.index(st.session_state['screen'])
    go_to(screens[idx + 1])

def send_quote():
    df_sum = build_summary()
    subtotal = df_sum['Line Total ($)'].sum()
    tax = round(subtotal * 0.08, 2)
    total = round(subtotal + tax, 2)
    rows = ''.join(
        f"<tr><td>{row['Item Name']}</td><td>{row['Servings']}</td><td>${row['Unit Price ($)']:.2f}</td><td>${row['Line Total ($)']:.2f}</td></tr>"
        for _, row in df_sum.iterrows()
    )
    html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; color: #333; background-color: #f4f4f4; margin: 0; padding: 0; }}
            .container {{ max-width: 600px; margin: 20px auto; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            .header {{ background: #2a9d8f; color: #fff; padding: 20px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 24px; }}
            .content {{ padding: 20px; }}
            .content h2 {{ color: #264653; margin-top: 0; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            th, td {{ text-align: left; padding: 10px; border-bottom: 1px solid #ddd; }}
            th {{ background: #e9ecef; }}
            .total-row th, .total-row td {{ font-weight: bold; }}
            .footer {{ background: #e9ecef; padding: 15px; text-align: center; font-size: 12px; color: #666; }}
            .button {{ display: inline-block; margin-top: 20px; padding: 12px 20px; background: #e76f51; color: #fff; text-decoration: none; border-radius: 4px; }}
        </style>
        </head>
        <body>
        <div class="container">
            <div class="header">
            <h1>Bowtie Catering</h1>
            </div>
            <div class="content">
            <p>Hi {st.session_state['name']},</p>
            <p>Thank you for considering Bowtie Catering for your event on <strong>{st.session_state['event_date']}</strong>. Below is your customized quote:</p>
            <h2>Event Details</h2>
            <p>
                <strong>Event:</strong> {st.session_state['event_type']}<br>
                <strong>Email:</strong> {st.session_state['email']}
            </p>
            <h2>Your Quote</h2>
            <table>
                <tr><th>Menu Item</th><th>Qty</th><th>Unit Price</th><th>Line Total</th></tr>
                {rows}
                <tr class="total-row"><td colspan="3">Subtotal</td><td>${subtotal:.2f}</td></tr>
                <tr><td colspan="3">Tax (8%)</td><td>${tax:.2f}</td></tr>
                <tr class="total-row"><td colspan="3">Total</td><td>${total:.2f}</td></tr>
            </table>
            <p style="text-align:center;">
                <a href="https://example.com/confirm-order" class="button">Confirm Your Quote</a>
            </p>
            <p>Warm regards,<br>
            <strong>Phil Bolinger</strong><br>
            Owner, Bowtie Catering.<br>
            (555) 123-4567 • phil@bowtiecatering.com</p>
            </div>
            <div class="footer">
            Bowtie Catering. • 123 Main St • Pottstown, PA<br>
            <a href="https://example.com/unsubscribe">Unsubscribe</a>
            </div>
        </div>
        </body>
        </html>
        """
    send_email(st.session_state['email'], f"Your Catering Quote - {st.session_state['event_type']}", html)
    st.success("Quote sent successfully!")

# --- Screens ---
def info_screen():
    st.header("✨ Event Details")
    with st.form('info_form'):
        name_input = st.text_input("Your Name", value=st.session_state['name'])
        email_input = st.text_input("Email Address", value=st.session_state['email'])
        event_input = st.text_input("Type of Event", value=st.session_state['event_type'])
        date_input = st.date_input("Event Date", value=st.session_state['event_date'])
        if st.form_submit_button("Start Order"):
            st.session_state['name'] = name_input
            st.session_state['email'] = email_input
            st.session_state['event_type'] = event_input
            st.session_state['event_date'] = date_input
            start_order()

def selection_screen(category):
    st.header(f"🍽️ Select {category.title()}")
    for item in [i for i, tag in category_map.items() if tag == category]:
        with st.expander(f"{item}"):
            include = st.checkbox(f"Include {item}", key=f"inc_{item}")
            st.write(desc_map[item])
            if include:
                st.session_state['selected'][item] = default_servings[item]
            else:
                st.session_state['selected'].pop(item, None)
    df_sum = build_summary()
    total = df_sum['Line Total ($)'].sum() if df_sum is not None else 0
    st.metric("💰 Current Total", f"${total:.2f}")
    cols = st.columns([1,1])
    cols[0].button(f"⬅️ Back to {screens[screens.index(st.session_state['screen'])-1].title()}", on_click=back_screen, disabled=(st.session_state['screen']==tags[0]))
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
    total = df_sum['Line Total ($)'].sum() if df_sum is not None else 0
    st.metric("🏆 Grand Total", f"${total:.2f}")
    cols = st.columns([1,1])
    cols[0].button(f"⬅️ Back to {tags[-1].title()}", on_click=back_screen)
    cols[1].button("✉️ Send Quote", on_click=send_quote)

# --- Dispatcher ---
if st.session_state['screen'] == 'info':
    info_screen()
elif st.session_state['screen'] != 'summary':
    selection_screen(st.session_state['screen'])
else:
    summary_screen()
