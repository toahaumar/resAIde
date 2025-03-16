"""
Utility functions for data handling
"""

import pandas as pd
import os
import json

def initialize_data():
    """Initialize sample application data"""
    return pd.DataFrame(
        {
            "application_id": list(range(1001, 1011)),
            "name": [
                "John Doe",
                "Jane Smith",
                "Robert Johnson",
                "Maria Garcia",
                "Wei Chen",
                "Fatima Ahmed",
                "Carlos Rodriguez",
                "Aisha Patel",
                "Viktor Petrov",
                "Olivia Kim",
            ],
            "date_of_birth": [
                "1990-05-16",
                "1992-08-23",
                "1985-11-30",
                "1988-03-21",
                "1995-02-14",
                "1987-07-09",
                "1993-12-05",
                "1991-04-18",
                "1989-09-27",
                "1994-01-12",
            ],
            "passport_number": [
                "AB123459",
                "CD789012",
                "EF345678",
                "GH901234",
                "IJ567890",
                "KL123456",
                "MN789012",
                "OP345678",
                "QR901234",
                "ST567890",
            ],
            "nationality": [
                "USA",
                "UK",
                "Canada",
                "Mexico",
                "China",
                "Egypt",
                "Brazil",
                "India",
                "Russia",
                "South Korea",
            ],
            "visa_type": [
                "Tourist",
                "Student",
                "Work",
                "Family",
                "Tourist",
                "Business",
                "Student",
                "Work",
                "Tourist",
                "Business",
            ],
            "status": [
                "Not Started",
                "In Progress",
                "Completed",
                "Not Started",
                "In Progress",
                "Not Started",
                "In Progress",
                "Completed",
                "Not Started",
                "In Progress",
            ],
            "submission_date": pd.date_range(start="2025-01-01", periods=10)
            .strftime("%Y-%m-%d")
            .tolist(),
            "personal_info_status": [
                "Pending",
                "Approved",
                "Approved",
                "Pending",
                "Feedback",
                "Pending",
                "Rejected",
                "Approved",
                "Pending",
                "Feedback",
            ],
            "document_status": [
                "Pending",
                "Pending",
                "Approved",
                "Pending",
                "Approved",
                "Pending",
                "Rejected",
                "Approved",
                "Pending",
                "Feedback",
            ],
            "criminal_history_status": [
                "Pending",
                "Pending",
                "Approved",
                "Pending",
                "Pending",
                "Pending",
                "Rejected",
                "Approved",
                "Pending",
                "Pending",
            ],
            "officer_notes": [
                "",
                "Needs additional financial proof",
                "All documents verified",
                "",
                "Passport expiry date concern",
                "",
                "Criminal record found",
                "Approved after verification",
                "",
                "Financial documents need clarification",
            ],
        }
    )

def load_applications_data(st, data_dir):
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
