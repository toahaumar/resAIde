import json
import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from datetime import datetime
from pages import home, applications, evaluation, resources

def load_applications_data(data_dir):
    """
    Load applications data from user/data directory.
    Each subdirectory is an application ID containing application.json and uploaded files.
    """
    applications_data = []
    
    # Check if data directory exists and print absolute path
    data_dir = os.path.abspath(data_dir)
    print(f"Looking for data in: {data_dir}")
    
    if not os.path.exists(data_dir):
        st.error(f"Data directory not found: {data_dir}")
        return pd.DataFrame()
    
    # Print list of directories found
    subdirs = os.listdir(data_dir)
    print(f"Found directories: {subdirs}")
    
    # Iterate through all subdirectories in the data directory
    for app_id in subdirs:
        app_dir = os.path.join(data_dir, app_id)
        
        # Skip if not a directory
        if not os.path.isdir(app_dir):
            print(f"Skipping {app_id} - not a directory")
            continue
            
        # Path to application.json
        json_path = os.path.join(app_dir, "application_data.json")
        print(f"Looking for application_data.json in: {json_path}")
        
        # Skip if application.json doesn't exist
        if not os.path.exists(json_path):
            print(f"Skipping {app_id} - application_data.json not found")
            continue
            
        try:
            # Load application data
            with open(json_path, 'r') as file:
                app_data = json.load(file)
            print(f"Successfully loaded data for application {app_id}")
            
            # Create a new dictionary with required fields
            processed_data = {
                'application_id': app_id,
                'status': 'Not Started',
                'document_status': 'Pending',
                'personal_info_status': 'Pending',
                'criminal_history_status': 'Pending',
                'officer_notes': '',
                'name': '',
                'nationality': ''
            }
            
            # Add the original application data
            processed_data.update(app_data)
            processed_data['name'] = processed_data['PersonalInformation']['FirstName'] + " " + processed_data['PersonalInformation']['Surname']
            processed_data['nationality'] = processed_data['PersonalInformation']['CurrentNationality']
            processed_data['submission_date'] = '2022-12-15'
            
            # Add the application data to our list
            applications_data.append(processed_data)
            print(f"Added application {app_id} to applications_data")
            
            # Save the updated data back to the JSON file
            with open(json_path, 'w') as file:
                json.dump(processed_data, file, indent=4)
            
        except json.JSONDecodeError as e:
            st.error(f"Error reading application data for {app_id}: {str(e)}")
            print(f"JSON decode error for {app_id}: {str(e)}")
        except Exception as e:
            st.error(f"Unexpected error processing application {app_id}: {str(e)}")
            print(f"Unexpected error for {app_id}: {str(e)}")

        print()
    
    # Print final data
    print(f"Total applications loaded: {len(applications_data)}")
    
    # Convert to DataFrame
    if applications_data:
        df = pd.DataFrame(applications_data)
        
        # Ensure all required columns exist with default values
        required_columns = {
            'application_id': '',
            'status': 'Not Started',
            'document_status': 'Pending',
            'personal_info_status': 'Pending',
            'criminal_history_status': 'Pending',
            'officer_notes': ''
        }
        
        for col, default_value in required_columns.items():
            if col not in df.columns:
                df[col] = default_value
        
        print(f"Created DataFrame with {len(df)} rows")
        return df
    else:
        print("No applications data found, returning empty DataFrame")
        # Return empty DataFrame with required columns
        return pd.DataFrame(columns=[
            'application_id', 'status', 'document_status',
            'personal_info_status', 'criminal_history_status',
            'officer_notes'
        ])

# Configure the page
st.set_page_config(
    page_title="Visa Officer Portal", layout="wide", initial_sidebar_state="expanded"
)

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "home"

# Load applications data from user/data directory
data_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'candidate', 'data'))
print(f"Data directory path: {data_directory}")

if "applications" not in st.session_state:
    st.session_state.applications = load_applications_data(data_directory)
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

