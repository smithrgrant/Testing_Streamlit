import os
import streamlit as st
import pandas as pd

# Determine base directory of this script and reference CSV in same folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILENAME = 'catering_items_weight_shares.csv'
CSV_PATH = os.path.join(BASE_DIR, CSV_FILENAME)

@st.cache_data
# Load data from the CSV located alongside this script
def load_data():
    return pd.read_csv(CSV_PATH)

# Initialize session state for screen management
if 'screen' not in st.session_state:
    st.session_state.screen = 'order'

# Load and prepare data
df = load_data()
grouped = (
    df.groupby(['Item #', 'Item Name', 'Servings'])['Cost per Component ($)']
      .sum()
      .reset_index()
      .rename(columns={'Cost per Component ($)': 'Cost per Serving ($)'})
)
item_cost = dict(zip(grouped['Item Name'], grouped['Cost per Serving ($)']))
default_servings = dict(zip(grouped['Item Name'], grouped['Servings']))

# Page configuration
st.set_page_config(page_title="Catering Dashboard", layout="wide")

# Order screen
def order_screen():
    st.title("🍴 Build Your Catering Quote")
    st.sidebar.header("Select Items and Adjust Servings")
    selected = {}
    for item in grouped['Item Name']:
        include_item = st.sidebar.checkbox(item, key=f"inc_{item}")
        if include_item:
            servings = st.sidebar.slider(
                label=f"Servings for {item}",
                min_value=0,
                max_value=default_servings[item] * 2,
                value=default_servings[item],
                step=1,
                key=f"serv_{item}"
            )
            selected[item] = servings

    if selected:
        summary = pd.DataFrame(
            [
                (item, servings, item_cost[item], servings * item_cost[item])
                for item, servings in selected.items()
            ],
            columns=["Item Name", "Servings", "Cost per Serving ($)", "Total Cost ($)"]
        )
        grand_total = summary["Total Cost ($)"].sum()

        st.subheader("Order Summary Draft")
        st.dataframe(summary)
        st.metric("Current Total", f"${grand_total:.2f}")
        if st.button("Finalize Quote"):
            # Save quote data to session and switch screen
            st.session_state.quote_summary = summary
            st.session_state.quote_total = grand_total
            st.session_state.screen = 'quote'
    else:
        st.write("Select items in the sidebar to build your order.")

# Quote review screen
def quote_screen():
    st.title("📄 Finalized Catering Quote")
    summary = st.session_state.get('quote_summary')
    total = st.session_state.get('quote_total')
    if summary is not None:
        st.dataframe(summary)
        st.metric("Grand Total", f"${total:.2f}")
        if st.button("Back to Order"):
            st.session_state.screen = 'order'
    else:
        st.error("No quote found. Please build your quote first.")

# Screen dispatcher
if st.session_state.screen == 'order':
    order_screen()
else:
    quote_screen()

# # Footer instructions
# st.markdown(
#     "---\n"
#     "**Instructions:** Ensure `catering_items_weight_shares.csv` is alongside this script. Run with `streamlit run catering_dashboard.py`."
# )
