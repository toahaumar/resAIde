import json
import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from datetime import datetime
from pages import home, applications, evaluation, resources
from utils.data import load_applications_data

# Configure the page
st.set_page_config(
    page_title="Visa Officer Portal", layout="wide", initial_sidebar_state="collapsed"
)

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "home"

# Load applications data from user/data directory
data_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'candidate', 'data'))
print(f"Data directory path: {data_directory}")

if "applications" not in st.session_state:
    st.session_state.applications = load_applications_data(st, data_directory)
    print(st.session_state.applications)

if "current_application" not in st.session_state:
    st.session_state.current_application = None

# Add notifications to session state if not already present
if "notifications" not in st.session_state:
    st.session_state.notifications = []

# Check for new notifications on every page load
if not st.session_state.applications.empty:
    new_apps = st.session_state.applications[
        st.session_state.applications["status"] == "Not Started"
    ]

    for _, app in new_apps.iterrows():
        # Extract name from PersonalInformation if available
        name = app.get('PersonalInformation', {}).get('FirstName', '') + ' ' + \
               app.get('PersonalInformation', {}).get('Surname', '')
        visa_type = app.get('PurposeAndDurationOfStay', {}).get('PurposeOfStay', 'Unknown')
        
        notification = f"You have a new application to review. {visa_type} Visa for {name.strip()}"
        if notification not in st.session_state.notifications:
            st.session_state.notifications.append(notification)
            st.toast(notification)

# Create a top navigation bar
col1, col2 = st.columns([6, 1])  # Adjust column widths as needed

with col1:
    st.button("Home", on_click=lambda: setattr(st.session_state, "page", "home"))
    st.button("Applications", on_click=lambda: setattr(st.session_state, "page", "applications"))

with col2:
    st.write("**Officer:** Jane Wilson", unsafe_allow_html=True)
    st.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}", unsafe_allow_html=True)

# Load environment variables from .env file
load_dotenv()

# Main content based on the selected page
if st.session_state.page == "home":
    home.show()
elif st.session_state.page == "applications":
    applications.show()
elif st.session_state.page == "evaluation":
    evaluation.show()
elif st.session_state.page == "resources":
    resources.show()

