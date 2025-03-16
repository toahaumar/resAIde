import streamlit as st
from datetime import datetime

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
    "Deepti Singhal": {
        "date_of_birth": "1981-06-02",
        "nationality": "Indian",
        "passport_number": "L9492297",
    }
    # Add more entries as needed
}

OVERALL_FEEDBACK = {}  # Dictionary to store feedback for each application
EVALUATION_FEEDBACK = {}  # Dictionary to store individual evaluation feedback

def show():
    if "evaluation_updated" not in st.session_state:
        st.session_state.evaluation_updated = False

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
        # status_col1, status_col2, status_col3 = st.columns(3)
        # with status_col1:
        #     st.write("Not Started" if app_data['status'] == 'Not Started' else "")
        # with status_col2:
        #     st.write("In Progress" if app_data['status'] == 'In Progress' else "")
        # with status_col3:
        #     st.write("Completed" if app_data['status'] == 'Completed' else "")
        
        # Personal Info Evaluation
        with st.expander("PERSONAL INFO EVALUATION", expanded=True):
            if app_data['personal_info_status'] == 'Approved':
                st.success("✅ Personal Information Evaluation: APPROVED")
            elif app_data['personal_info_status'] == 'Rejected':
                st.error("❌ Personal Information Evaluation: REJECTED")
            else:
                st.write("Review the applicant's personal information against the central registry.")
                
                # Check if person exists in registry
                applicant_name = app_data['name']
                if applicant_name in PERSONAL_INFO_REGISTRY:
                    registry_data = PERSONAL_INFO_REGISTRY[applicant_name]
                    
                    # Compare all crucial information
                    mismatches = []
                    fields_to_check = {
                        'nationality': 'CurrentNationality',
                        'date_of_birth': 'DateOfBirth',
                        # 'passport_number': 'Passport Number'
                    }
                    
                    for field, display_name in fields_to_check.items():
                        if app_data['PersonalInformation'][display_name] != registry_data[field]:
                            mismatches.append({
                                'field': display_name,
                                'provided': app_data['PersonalInformation'][display_name],
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
            
            # Reset the update trigger after UI is refreshed
            if st.session_state.evaluation_updated:
                st.session_state.evaluation_updated = False
            
            # Feedback section
            if hasattr(st.session_state, 'feedback_section') and st.session_state.feedback_section == 'personal_info_status':
                feedback = st.text_area("Enter feedback for Personal Info", value=app_data['officer_notes'])
                if st.button("Save Personal Info Feedback"):
                    save_feedback(app_id, 'personal_info_status', feedback)
                    st.session_state.feedback_section = None  # Reset feedback section
                    st.rerun()  # Rerun to update the expander
            
            # Display saved feedback if it exists
            if app_id in EVALUATION_FEEDBACK and 'personal_info_status' in EVALUATION_FEEDBACK[app_id]:
                st.warning(f"💬 Feedback saved: {EVALUATION_FEEDBACK[app_id]['personal_info_status']}")
        
        # Document Evaluation
        with st.expander("DOCUMENT EVALUATION (LLM)", expanded=True):
            if app_data['document_status'] == 'Approved':
                st.success("✅ Document Evaluation: APPROVED")
            elif app_data['document_status'] == 'Rejected':
                st.error("❌ Document Evaluation: REJECTED")
            else:
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
                    st.session_state.feedback_section = None  # Reset feedback section
                    st.rerun()  # Rerun to update the expander
            
            # Display saved feedback if it exists
            if app_id in EVALUATION_FEEDBACK and 'document_status' in EVALUATION_FEEDBACK[app_id]:
                st.warning(f"💬 Feedback saved: {EVALUATION_FEEDBACK[app_id]['document_status']}")

        # Criminal History Evaluation
        with st.expander("CRIMINAL HISTORY EVALUATION (RULE-BASED)", expanded=True):
            if app_data['criminal_history_status'] == 'Approved':
                st.success("✅ Criminal History Evaluation: APPROVED")
            elif app_data['criminal_history_status'] == 'Rejected':
                st.error("❌ Criminal History Evaluation: REJECTED")
            else:
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
                    st.session_state.feedback_section = None  # Reset feedback section
                    st.rerun()  # Rerun to update the expander
            
            # Display saved feedback if it exists
            if app_id in EVALUATION_FEEDBACK and 'criminal_history_status' in EVALUATION_FEEDBACK[app_id]:
                st.warning(f"💬 Feedback saved: {EVALUATION_FEEDBACK[app_id]['criminal_history_status']}")

        # Reset the update trigger after UI is refreshed
        if st.session_state.evaluation_updated:
            st.session_state.evaluation_updated = False
        
        # Logic summary
        # st.write("### Decision Logic")
        # st.write("AND -> APPROVED: All sections must be approved for final approval")
        # st.write("OR -> FEEDBACK, REJECT: Any section with feedback or rejection will affect the final decision")
        
        # Final decision section
        st.write("---")
        st.write("## Final Decision")
        
        # Get statuses
        personal_status = app_data['personal_info_status']
        document_status = app_data['document_status']
        criminal_status = app_data['criminal_history_status']
        
        # Check if all evaluations are completed
        all_completed = all(status in ['Approved', 'Rejected', 'Feedback'] 
                           for status in [personal_status, document_status, criminal_status])
        
        if all_completed:
            all_approved = all(status == 'Approved' 
                              for status in [personal_status, document_status, criminal_status])
            any_rejected = any(status == 'Rejected' 
                              for status in [personal_status, document_status, criminal_status])
            
            if all_approved:
                st.success("✅ All evaluations have been approved")
                if st.button("Send Visa Approval Notification"):
                    approval_message = f"Congratulations! Your visa application ({app_id}) has been approved."
                    save_overall_feedback(app_id, 'Approved', approval_message)
                    st.success("Approval notification saved!")
            
            elif any_rejected:
                st.error("❌ One or more evaluations have been rejected")
                # Collect feedback from rejected evaluations
                rejection_feedback = []
                for field in ['personal_info_status', 'document_status', 'criminal_history_status']:
                    if app_data[field] == 'Rejected':
                        base_message = {
                            'personal_info_status': "Personal Information: Verification failed",
                            'document_status': "Document Verification: Required documents not satisfactory",
                            'criminal_history_status': "Criminal History: Background check requirements not met"
                        }[field]
                        
                        # Add specific feedback if it exists
                        if app_id in EVALUATION_FEEDBACK and field in EVALUATION_FEEDBACK[app_id]:
                            base_message += f" - {EVALUATION_FEEDBACK[app_id][field]}"
                        
                        rejection_feedback.append(base_message)
                
                rejection_message = (
                    f"Your visa application ({app_id}) has been denied for the following reasons:\n"
                    + "\n".join(f"- {feedback}" for feedback in rejection_feedback)
                )
                
                if st.button("Send Visa Denial Notification"):
                    save_overall_feedback(app_id, 'Rejected', rejection_message)
                    st.error("Denial notification saved!")
            
            else:
                # Case where there are feedbacks but no rejections
                st.warning("⚠️ Feedback provided for one or more evaluations")
                feedback_messages = []
                for field in ['personal_info_status', 'document_status', 'criminal_history_status']:
                    if app_id in EVALUATION_FEEDBACK and field in EVALUATION_FEEDBACK[app_id]:
                        section_name = {
                            'personal_info_status': "Personal Information",
                            'document_status': "Document Verification",
                            'criminal_history_status': "Criminal History"
                        }[field]
                        feedback_messages.append(f"{section_name}: {EVALUATION_FEEDBACK[app_id][field]}")
                
                if feedback_messages:
                    feedback_message = (
                        f"Your visa application ({app_id}) requires attention:\n"
                        + "\n".join(f"- {feedback}" for feedback in feedback_messages)
                    )
                    
                    if st.button("Send Feedback Notification"):
                        save_overall_feedback(app_id, 'Feedback', feedback_message)
                        st.warning("Feedback notification saved!")
        
        else:
            st.warning("⚠️ Please complete all evaluations before making a final decision")
        
        # Display saved feedback if it exists
        if app_id in OVERALL_FEEDBACK:
            st.write("### Saved Feedback")
            feedback_data = OVERALL_FEEDBACK[app_id]
            st.write(f"**Status:** {feedback_data['status']}")
            st.write(f"**Feedback:** {feedback_data['feedback']}")
            st.write(f"**Timestamp:** {feedback_data['timestamp']}")

        # Reset the update trigger after UI is refreshed
        if st.session_state.evaluation_updated:
            st.session_state.evaluation_updated = False
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
    
    # Add a trigger for UI update
    st.session_state.evaluation_updated = True

def save_feedback(app_id, field, feedback):
    index = st.session_state.applications[st.session_state.applications['application_id'] == app_id].index[0]
    st.session_state.applications.at[index, 'officer_notes'] = feedback
    
    # Save to evaluation feedback dictionary
    if app_id not in EVALUATION_FEEDBACK:
        EVALUATION_FEEDBACK[app_id] = {}
    EVALUATION_FEEDBACK[app_id][field] = feedback
    
    update_evaluation_status(app_id, field, 'Feedback')

def save_overall_feedback(app_id, status, feedback):
    print(feedback)
    OVERALL_FEEDBACK[app_id] = {
        'status': status,
        'feedback': feedback,
        'timestamp': str(datetime.now())
    }

    # Read and update the application_data.json file
    import os
    import json
    
    # Navigate two levels up from current file location
    json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'user', 'data', app_id, 'application_data.json')
    
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
            
        # Update feedback for the application
        data['final_feedback'] = {
            'status': status,
            'message': feedback,
            'timestamp': str(datetime.now())
        }
        
        # Write back to the file
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=4)
            
    except Exception as e:
        st.error(f"Error updating application data: {str(e)}")