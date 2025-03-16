import streamlit as st
from utils.registry import PERSONAL_INFO_REGISTRY
from .evaluation import save_personal_info_feedback

def show():
    st.title("Applications")

    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox(
            "Filter by Status", ["All", "Not Started", "In Progress", "Completed"]
        )
    with col2:
        visa_type_filter = st.selectbox(
            "Filter by Visa Type",
            ["All", "Tourist", "Student", "Work", "Business", "Family"],
        )
    with col3:
        search_term = st.text_input("Search by Name or ID")

    # Apply filters
    filtered_apps = st.session_state.applications.copy()

    if status_filter != "All":
        filtered_apps = filtered_apps[filtered_apps["status"] == status_filter]

    if visa_type_filter != "All":
        filtered_apps = filtered_apps[filtered_apps["visa_type"] == visa_type_filter]

    if search_term:
        filtered_apps = filtered_apps[
            (filtered_apps["name"].str.contains(search_term, case=False))
            | (filtered_apps["application_id"].astype(str).str.contains(search_term))
        ]

    # Display applications
    st.write(f"Showing {len(filtered_apps)} applications")

    # Status filter tabs
    tab1, tab2, tab3 = st.tabs(["Not Started", "In Progress", "Completed"])

    with tab1:
        not_started = filtered_apps[filtered_apps["status"] == "Not Started"]
        if len(not_started) > 0:
            for _, app in not_started.iterrows():
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**Application ID:** {app['application_id']}")
                        st.write(f"**Name:** {app['name']} ({app['nationality']})")
                        st.write(f"**Visa Type:** {app['visa_type']}")
                    with col2:
                        st.button(
                            "Review",
                            key=f"ns_review_{app['application_id']}",
                            on_click=view_application,
                            args=(app["application_id"],),
                        )
        else:
            st.write("No applications with 'Not Started' status")

    with tab2:
        in_progress = filtered_apps[filtered_apps["status"] == "In Progress"]
        if len(in_progress) > 0:
            for _, app in in_progress.iterrows():
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**Application ID:** {app['application_id']}")
                        st.write(f"**Name:** {app['name']} ({app['nationality']})")
                        st.write(f"**Visa Type:** {app['visa_type']}")
                    with col2:
                        st.button(
                            "Continue",
                            key=f"ip_review_{app['application_id']}",
                            on_click=view_application,
                            args=(app["application_id"],),
                        )
        else:
            st.write("No applications with 'In Progress' status")

    with tab3:
        completed = filtered_apps[filtered_apps["status"] == "Completed"]
        if len(completed) > 0:
            for _, app in completed.iterrows():
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**Application ID:** {app['application_id']}")
                        st.write(f"**Name:** {app['name']} ({app['nationality']})")
                        st.write(f"**Visa Type:** {app['visa_type']}")
                    with col2:
                        st.button(
                            "View",
                            key=f"c_review_{app['application_id']}",
                            on_click=view_application,
                            args=(app["application_id"],),
                        )
        else:
            st.write("No applications with 'Completed' status")


def view_application(app_id):
    # Get application data
    app_data = st.session_state.applications[st.session_state.applications['application_id'] == app_id].iloc[0]
    
    # Only run automatic checks if this is a new review (status is "Not Started")
    if app_data['status'] == "Not Started":
        applicant_name = app_data['name']
        
        # Check if person exists in registry and generate appropriate message
        if applicant_name in PERSONAL_INFO_REGISTRY:
            registry_data = PERSONAL_INFO_REGISTRY[applicant_name]
            mismatches = []
            fields_to_check = {
                'nationality': 'CurrentNationality',
                'date_of_birth': 'DateOfBirth',
            }
            
            for field, display_name in fields_to_check.items():
                if app_data['PersonalInformation'][display_name] != registry_data[field]:
                    mismatches.append(f"{display_name}: Provided '{app_data['PersonalInformation'][display_name]}' does not match registry '{registry_data[field]}'")
            
            if len(mismatches) == 0:
                save_personal_info_feedback(app_id, 'approved', f"All automatic checks passed")
            else:
                feedback_message = "Discrepancies found: " + "; ".join(mismatches)
                save_personal_info_feedback(app_id, 'rejected', feedback_message)
        else:
            save_personal_info_feedback(app_id, 'rejected', "Invalid personal details!")
    
    st.session_state.current_application = app_id
    st.session_state.page = "evaluation"
