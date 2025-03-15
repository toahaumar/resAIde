import streamlit as st
import pandas as pd
from datetime import datetime
from pages import home, applications, evaluation, resources
from utils.data import initialize_data

# Configure the page
st.set_page_config(
    page_title="Visa Officer Portal", layout="wide", initial_sidebar_state="expanded"
)

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "home"

# Initialize applications data if not already present
if "applications" not in st.session_state:
    st.session_state.applications = initialize_data()

if "current_application" not in st.session_state:
    st.session_state.current_application = None

# Add notifications to session state if not already present
if "notifications" not in st.session_state:
    st.session_state.notifications = []

# Check for new notifications on every page load
new_apps = st.session_state.applications[
    st.session_state.applications["status"] == "Not Started"
]

for _, app in new_apps.iterrows():
    notification = f"You have a new application to review. {app['visa_type']} Visa for {app['name']}"
    if notification not in st.session_state.notifications:
        st.session_state.notifications.append(notification)
        st.toast(notification)

# Sidebar navigation
st.sidebar.title("Quick Links")
st.sidebar.button("Home", on_click=lambda: setattr(st.session_state, "page", "home"))
st.sidebar.button(
    "Applications",
    on_click=lambda: setattr(st.session_state, "page", "applications"),
)
# st.sidebar.button(
#     "Evaluation", on_click=lambda: setattr(st.session_state, "page", "resources")
# )
st.sidebar.info("Officer: Jane Wilson")
st.sidebar.info(f"Date: {datetime.now().strftime('%Y-%m-%d')}")

def main():
    # Display the appropriate page
    if st.session_state.page == "home":
        home.show()
    elif st.session_state.page == "applications":
        applications.show()
    elif st.session_state.page == "evaluation":
        evaluation.show()
    elif st.session_state.page == "resources":
        resources.show()

if __name__ == "__main__":
    main()

