import streamlit as st

# Add this at the top of the file with other imports
PERSONAL_INFO_REGISTRY = {
    "John Doe": {
        "date_of_birth": "1990-05-15",
        "nationality": "USA",
        "passport_number": "AB123456",
    },
    "Maria Garcia": {
        "date_of_birth": "1988-03-21",
        "nationality": "Spain",
        "passport_number": "XY789012",
    },
    # Add more entries as needed
}

def show():
    if st.session_state.current_application:
        app_id = st.session_state.current_application
        app_data = st.session_state.applications[st.session_state.applications['application_id'] == app_id].iloc[0]
        
        # Back button
        st.button("← Back to Applications", on_click=lambda: setattr(st.session_state, 'page', 'applications'))
        
        # Application header
        st.title(f"Application Evaluation - {app_id}")
        st.write(f"**Applicant:** {app_data['name']} | **Nationality:** {app_data['nationality']} | **Visa Type:** {app_data['visa_type']}")
        st.write(f"**Submission Date:** {app_data['submission_date']}")
        
        # Overall status
        st.write("### Overall Status")
        status_col1, status_col2, status_col3 = st.columns(3)
        with status_col1:
            st.write("Not Started" if app_data['status'] == 'Not Started' else "")
        with status_col2:
            st.write("In Progress" if app_data['status'] == 'In Progress' else "")
        with status_col3:
            st.write("Completed" if app_data['status'] == 'Completed' else "")
        
        # Personal Info Evaluation
        with st.expander("PERSONAL INFO EVALUATION", expanded=True):
            st.write("Review the applicant's personal information against the central registry.")
            
            # Check if person exists in registry
            applicant_name = app_data['name']
            if applicant_name in PERSONAL_INFO_REGISTRY:
                registry_data = PERSONAL_INFO_REGISTRY[applicant_name]
                
                # Compare all crucial information
                mismatches = []
                fields_to_check = {
                    'nationality': 'Nationality',
                    'date_of_birth': 'Date of Birth',
                    'passport_number': 'Passport Number'
                }
                
                for field, display_name in fields_to_check.items():
                    if app_data[field] != registry_data[field]:
                        mismatches.append({
                            'field': display_name,
                            'provided': app_data[field],
                            'registry': registry_data[field]
                        })
                
                if len(mismatches) == 0:
                    st.success("✅ No discrepancies found. All personal information matches the central registry.")
                else:
                    st.error("⚠️ Discrepancies found in the following fields:")
                    for mismatch in mismatches:
                        st.write(f"**{mismatch['field']}:**")
                        st.write(f"- Provided: {mismatch['provided']}")
                        st.write(f"- Registry: {mismatch['registry']}")
            else:
                st.error("⚠️ Person not found in central registry")
            
            # Decision buttons
            st.write("### Decision")
            personal_col1, personal_col2, personal_col3 = st.columns(3)
            with personal_col1:
                st.button("APPROVE", key="personal_approve", 
                          on_click=update_evaluation_status, 
                          args=(app_id, 'personal_info_status', 'Approved'))
            with personal_col2:
                if st.button("FEEDBACK", key="personal_feedback"):
                    st.session_state.feedback_section = 'personal_info_status'
            with personal_col3:
                st.button("REJECT", key="personal_reject", 
                          on_click=update_evaluation_status, 
                          args=(app_id, 'personal_info_status', 'Rejected'))
            
            # Current status
            st.write(f"**Current Status:** {app_data['personal_info_status']}")
            
            # Feedback section
            if hasattr(st.session_state, 'feedback_section') and st.session_state.feedback_section == 'personal_info_status':
                feedback = st.text_area("Enter feedback for Personal Info", value=app_data['officer_notes'])
                if st.button("Save Feedback"):
                    save_feedback(app_id, 'personal_info_status', feedback)
                    st.session_state.pop('feedback_section')
                    st.experimental_rerun()
        
        # Document Evaluation
        with st.expander("DOCUMENT EVALUATION (LLM)", expanded=True):
            st.write("Review the applicant's documents using LLM-assisted verification.")
            
            # Document checks
            st.subheader("Passport Check")
            st.write("**Passport Number:** AB123456")
            st.write("**Issue Date:** 2020-06-01")
            st.write("**Expiry Date:** 2030-06-01")
            st.write("**Issuing Authority:** Department of State")
            st.write("**LLM Verification:** Passport appears valid")
            
            st.subheader("Financial Document Check")
            st.write("**Bank Statement:** Account shows sufficient funds")
            st.write("**Income Verification:** Monthly income: $5,000")
            st.write("**LLM Analysis:** Financial status meets requirements")
            
            st.subheader("Visa-specific Document Check")
            st.write(f"**Document Type:** {app_data['visa_type']} visa supporting documents")
            if app_data['visa_type'] == 'Work':
                st.write("**Work Contract:** Verified with employer")
                st.write("**Position:** Software Engineer")
            elif app_data['visa_type'] == 'Student':
                st.write("**University Acceptance:** Verified with institution")
                st.write("**Program:** Computer Science")
            
            # Decision buttons
            st.write("### Decision")
            doc_col1, doc_col2, doc_col3 = st.columns(3)
            with doc_col1:
                st.button("APPROVE", key="doc_approve", 
                          on_click=update_evaluation_status, 
                          args=(app_id, 'document_status', 'Approved'))
            with doc_col2:
                if st.button("FEEDBACK", key="doc_feedback"):
                    st.session_state.feedback_section = 'document_status'
            with doc_col3:
                st.button("REJECT", key="doc_reject", 
                          on_click=update_evaluation_status, 
                          args=(app_id, 'document_status', 'Rejected'))
            
            # Current status
            st.write(f"**Current Status:** {app_data['document_status']}")
            
            # Feedback section
            if hasattr(st.session_state, 'feedback_section') and st.session_state.feedback_section == 'document_status':
                feedback = st.text_area("Enter feedback for Document Evaluation", value=app_data['officer_notes'])
                if st.button("Save Document Feedback"):
                    save_feedback(app_id, 'document_status', feedback)
                    st.session_state.pop('feedback_section')
                    st.experimental_rerun()
        
        # Criminal History Evaluation
        with st.expander("CRIMINAL HISTORY EVALUATION (RULE-BASED)", expanded=True):
            st.write("Review the applicant's criminal history using rule-based checks.")
            
            # Criminal history checks
            st.write("**Background Check Results:**")
            st.write("- Local Criminal Database: No records found")
            st.write("- International Alerts: None")
            st.write("- Prior Visa Violations: None")
            
            # Risk assessment
            risk_score = 0.2  # Mock score
            st.write(f"**Risk Assessment Score:** {risk_score:.2f} (Low)")
            st.progress(risk_score)
            
            # Rule-based evaluation results
            st.write("**Automated Rule Check Results:**")
            st.write("- Rule 1: PASS - No criminal convictions")
            st.write("- Rule 2: PASS - No immigration violations")
            st.write("- Rule 3: PASS - No security concerns")
            
            # Decision buttons
            st.write("### Decision")
            crim_col1, crim_col2, crim_col3 = st.columns(3)
            with crim_col1:
                st.button("APPROVE", key="crim_approve", 
                          on_click=update_evaluation_status, 
                          args=(app_id, 'criminal_history_status', 'Approved'))
            with crim_col2:
                if st.button("FEEDBACK", key="crim_feedback"):
                    st.session_state.feedback_section = 'criminal_history_status'
            with crim_col3:
                st.button("REJECT", key="crim_reject", 
                          on_click=update_evaluation_status, 
                          args=(app_id, 'criminal_history_status', 'Rejected'))
            
            # Current status
            st.write(f"**Current Status:** {app_data['criminal_history_status']}")
            
            # Feedback section
            if hasattr(st.session_state, 'feedback_section') and st.session_state.feedback_section == 'criminal_history_status':
                feedback = st.text_area("Enter feedback for Criminal History", value=app_data['officer_notes'])
                if st.button("Save Criminal History Feedback"):
                    save_feedback(app_id, 'criminal_history_status', feedback)
                    st.session_state.pop('feedback_section')
                    st.experimental_rerun()
        
        # Logic summary
        st.write("### Decision Logic")
        st.write("AND -> APPROVED: All sections must be approved for final approval")
        st.write("OR -> FEEDBACK, REJECT: Any section with feedback or rejection will affect the final decision")
        
        # Final decision
        if app_data['status'] == 'Completed':
            st.write("### Final Decision")
            if app_data['personal_info_status'] == 'Approved' and app_data['document_status'] == 'Approved' and app_data['criminal_history_status'] == 'Approved':
                st.success("VISA APPROVED")
            else:
                st.error("VISA REJECTED")
                st.write(f"**Reason:** {app_data['officer_notes']}")
    else:
        st.error("No application selected")
        st.button("Back to Applications", on_click=lambda: setattr(st.session_state, 'page', 'applications'))

# Helper functions for the evaluation page
def update_evaluation_status(app_id, field, status):
    index = st.session_state.applications[st.session_state.applications['application_id'] == app_id].index[0]
    st.session_state.applications.at[index, field] = status
    
    # Update overall status
    personal = st.session_state.applications.at[index, 'personal_info_status']
    document = st.session_state.applications.at[index, 'document_status']
    criminal = st.session_state.applications.at[index, 'criminal_history_status']
    
    if personal == 'Approved' and document == 'Approved' and criminal == 'Approved':
        st.session_state.applications.at[index, 'status'] = 'Completed'
    elif personal == 'Rejected' or document == 'Rejected' or criminal == 'Rejected':
        st.session_state.applications.at[index, 'status'] = 'Completed'
    else:
        st.session_state.applications.at[index, 'status'] = 'In Progress'
    
    st.experimental_rerun()

def save_feedback(app_id, field, feedback):
    index = st.session_state.applications[st.session_state.applications['application_id'] == app_id].index[0]
    st.session_state.applications.at[index, 'officer_notes'] = feedback
    update_evaluation_status(app_id, field, 'Feedback')