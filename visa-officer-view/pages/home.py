import streamlit as st
from datetime import datetime


def show():
    st.title("Tacto Dashboard")
    # Dashboard stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Pending Applications",
            len(
                st.session_state.applications[
                    st.session_state.applications["status"] != "Completed"
                ]
            ),
        )
    with col2:
        st.metric(
            "Completed Today",
            len(
                st.session_state.applications[
                    st.session_state.applications["status"] == "Completed"
                ]
            ),
        )
    with col3:
        st.metric("New Assignments", len(st.session_state.notifications))

    # # New assignments
    # st.subheader("New Application Assigned")
    # new_apps = st.session_state.applications[
    #     st.session_state.applications["status"] == "Not Started"
    # ].head(2)
    # for _, app in new_apps.iterrows():
    #     with st.container():
    #         col1, col2 = st.columns([3, 1])
    #         with col1:
    #             st.write(f"**Application ID:** {app['application_id']}")
    #             st.write(f"**Name:** {app['name']}")
    #             st.write(f"**Visa Type:** {app['visa_type']}")
    #         with col2:
    #             st.button(
    #                 "Review",
    #                 key=f"review_{app['application_id']}",
    #                 on_click=view_application,
    #                 args=(app["application_id"],),
    #             )

    # Recent activity
    # st.subheader("Recent Activity")
    # st.dataframe(
    #     st.session_state.applications.iloc[:5][
    #         ["application_id", "name", "status", "submission_date"]
    #     ]
    # )


def view_application(app_id):
    st.session_state.current_application = app_id
    st.session_state.page = "evaluation"
