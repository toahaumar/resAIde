import streamlit as st
from datetime import datetime
from pages import home, applications, evaluation, resources
from utils.data import initialize_data


# Configure the page
st.set_page_config(
    page_title="Visa Officer Dashboard", layout="wide", initial_sidebar_state="expanded"
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

# Create a top navigation bar
col1, col2 = st.columns([6, 1])  # Adjust column widths as needed

with col1:
    st.button("Home", on_click=lambda: setattr(st.session_state, "page", "home"))
    st.button("Applications", on_click=lambda: setattr(st.session_state, "page", "applications"))

with col2:
    st.write("**Officer:** Jane Wilson", unsafe_allow_html=True)  # Officer's name on the top right
    st.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}", unsafe_allow_html=True)  # Current date on the top right


def main():
    # Main content based on the selected page
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

