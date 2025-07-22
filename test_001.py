import streamlit as st
import pandas as pd

# Load data
# Ensure the CSV file 'catering_items_weight_shares.csv' is in the same directory
# C:\Users\grobe\OneDrive\Documents\GitHub\Catering\catering_items_weight_shares.csv
@st.cache_data
def load_data():
    df = pd.read_csv(r"C:\Users\grobe\OneDrive\Documents\GitHub\Catering\catering_items_weight_shares.csv")
    
    return df

df = load_data()

# Compute cost per serving by summing component costs
grouped = df.groupby(['Item #', 'Item Name', 'Servings'])['Cost per Component ($)'] \
    .sum() \
    .reset_index() 
grouped = grouped.rename(columns={'Cost per Component ($)': 'Cost per Serving ($)'})

# Build lookup maps
item_cost = dict(zip(grouped['Item Name'], grouped['Cost per Serving ($)']))
default_servings = dict(zip(grouped['Item Name'], grouped['Servings']))

# App layout
st.set_page_config(page_title="Catering Dashboard", layout="wide")
st.title("🍴 Catering Order Dashboard")

# Sidebar controls
st.sidebar.header("Select Items and Adjust Servings")
selected = {}
for item in grouped['Item Name']:
    inc = st.sidebar.checkbox(item, key=f"inc_{item}")
    if inc:
        serv = st.sidebar.slider(
            f"Servings for {item}",
            min_value=0,
            max_value=default_servings[item] * 2,
            value=default_servings[item],
            step=1,
            key=f"serv_{item}"
        )
        selected[item] = serv

# Calculate totals
if selected:
    summary = pd.DataFrame(
        [(item, selected[item], item_cost[item], selected[item] * item_cost[item])
         for item in selected],
        columns=["Item Name", "Servings", "Cost per Serving ($)", "Total Cost ($)"]
    )
    grand_total = summary["Total Cost ($)"].sum()

    st.subheader("Order Summary")
    st.dataframe(summary)
    st.metric("Grand Total Cost", f"${grand_total:.2f}")
else:
    st.write("Select items in the sidebar to build your order.")

# Instructions
st.markdown("---\n**Instructions:** Make sure your `catering_items_weight_shares.csv` is here. Run:`streamlit run catering_dashboard.py`")
