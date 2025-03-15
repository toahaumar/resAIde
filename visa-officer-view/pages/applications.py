import streamlit as st


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
    st.session_state.current_application = app_id
    st.session_state.page = "evaluation"
