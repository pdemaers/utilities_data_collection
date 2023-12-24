import streamlit as st
from streamlit_option_menu import option_menu
from pymongo import MongoClient
import pandas as pd
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
from pathlib import Path
import streamlit_authenticator as stauth

# Function to connect to MongoDB
def connect_to_mongodb():
    username = st.secrets["mongo_username"]
    password = st.secrets["mongo_password"]
    cluster_url = st.secrets["mongo_cluster_url"]
    client = MongoClient(f"mongodb+srv://{username}:{password}@{cluster_url}/")
    db = client[st.secrets["DATABASE_NAME"]]
    collection = db[st.secrets["COLLECTION_NAME"]]
    return collection

# Function to get the MongoDB data into a dataframe
def get_data():
    collection = connect_to_mongodb()
    df = pd.DataFrame(list(collection.find()))
    return df

# Data collection form
def data_collection():
    with st.form("Utilities", clear_on_submit=True):

        st.header("Utility meter values")

        # Collect data elements from the user
        selected_date = st.date_input("Select a date")
        date = selected_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        electricity_day = st.number_input("Enter Electricity Day:", min_value=0)
        electricity_night = st.number_input("Enter Electricity Night:", min_value=0)
        electricity_car = st.number_input("Enter Electricity Car:", min_value=0)
        gas = st.number_input("Enter Gas:", min_value=0)

        # Every form must have a submit button
        submitted = st.form_submit_button("Submit")

        if submitted:
            # Connect to MongoDB and insert the data
            collection = connect_to_mongodb()
            data = {
                "date": date,    
                "electricity_day": electricity_day,
                "electricity_night": electricity_night,
                "electricity_car": electricity_car,
                "gas": gas
            }
            collection.insert_one(data)

            # Show confirmation message
            st.success("Data submitted successfully!")

# Data table visualisation
def data_table():
    df = get_data()
    st.dataframe(df, use_container_width=True, hide_index=False)


# Data plots visualisation
def data_plots():
    df = get_data()

    # Show gas usage
    df['date'] = pd.to_datetime(df['date'])
    df_sorted = df.sort_values(by='date')
    df_filtered = df[df['gas'] != 0]                    # only take the gas values different from 0
    
    fig, ax = plt.subplots(figsize=(4,2))
    sns.lineplot(data=df_filtered, x='date', y='gas', marker='o', ax=ax)
    ax.set_xlabel('Date', fontsize=10)
    ax.set_ylabel('Gas', fontsize=10)
    ax.set_title('Gas Consumption Over Time', fontsize=12)
    ax.set_ylim(45000, 58000)
    ax.tick_params(axis='x', labelrotation=90, labelsize=4)  # Adjust font size and rotation for x-axis tick labels
    ax.tick_params(axis='y', labelsize=4)  # Adjust font size for y-axis tick labels
    st.pyplot(fig)

# Main Streamlit app
st.set_page_config(page_title="Utilities Data Management", page_icon=":lightbulb:", layout="wide", initial_sidebar_state="expanded")

# User authentication

file_path = Path(__file__).parent / "hashed_pw.pkl"
with file_path.open("rb") as file:
    hashed_passwords = pickle.load(file)

credentials = {
    "usernames":{
        "pdemaers":{
            "name": "Patrick Demaerschalk",
            "password": hashed_passwords[0]
        }
    }
}

if "authentication_status" not in st.session_state:
    st.session_state["authentication_status"] = None

authenticator = stauth.Authenticate(credentials, "utilities_data", "abcdef", cookie_expiry_days=0)

name, authentication_status, username = authenticator.login("Login", "main")

if st.session_state["authentication_status"] == False:
    st.error("Username/password is incorrect.")

if st.session_state["authentication_status"] == None:
    st.warning("Please enter your username and password.")

if st.session_state["authentication_status"]:

    st.title("Utilities Data Management")
    st.text("Enter new utilities usage data and get electricity and gas usage analysis.")

    with st.sidebar:

        authenticator.logout("Logout", "main")
        st.write(f"Logged in user: *{name}*")

        selected = option_menu(
            menu_title="Main menu",
            options=["Data entry usage", "Data table", "Data plots"],
            icons=["pencil-square", "table", "graph-up"],
            menu_icon="cast"
        )

    if selected == 'Data entry usage':
        data_collection()
    elif selected == 'Data table':
        data_table()
    elif selected == 'Data plots':
        data_plots()

# Data analysis visuals



 