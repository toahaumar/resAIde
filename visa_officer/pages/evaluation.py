import os, sys
import streamlit as st
from datetime import datetime
from utils.registry import PERSONAL_INFO_REGISTRY
from streamlit_image_zoom import image_zoom
import json
import base64
from mistralai import Mistral
from pathlib import Path

from PIL import Image

OVERALL_FEEDBACK = {}  # Dictionary to store feedback for each application
EVALUATION_FEEDBACK = {}  # Dictionary to store individual evaluation feedback

def show():
    # Navigate two levels up and then two levels down to document_processor/scripts
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../document_processor/scripts"))
    sys.path.insert(0, base_path)

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
        
        # Personal Info Evaluation
        with st.expander("PERSONAL INFO EVALUATION", expanded=True):
            st.subheader("Personal Information Check", divider="blue")
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
            st.markdown("### Decision")
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
                st.subheader("Passport Verification", divider="blue")
                user_data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'candidate', 'data', app_id)
                ground_data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'document_processor', 'ground_truth')
    
                passport_image_ground = Image.open(f"{ground_data_path}/indian_passport.png")
                if not os.path.exists(f"{user_data_path}/indian_passport.png"):
                    st.error("Uploaded passport image not found")
                else:
                    passport_image_upload = Image.open(f"{user_data_path}/indian_passport.png")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("Ground Truth Passport")
                        image_zoom(passport_image_ground)
                    with col2:  
                        st.write("Uploaded Passport")
                        image_zoom(passport_image_upload)

                # Now you can import from prop.py
                from passport_comparison import extract_passport_data, compare_passport_json, compare_images, analyze_comparisons, classify_application

                json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'candidate', 'data', app_id, 'application_data.json')

                with open(json_path, 'r') as f:
                    data = json.load(f)

                if "passport_analysis" in data:
                    status = data["passport_analysis"]["status"]
                    final_analysis = data["passport_analysis"]["feedback"]

                else:
                    # Initialize the Mistral client
                    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
                    if not MISTRAL_API_KEY:
                        print("Error: MISTRAL_API_KEY is not set in the .env file.")
                        sys.exit(1)
                    client = Mistral(api_key=MISTRAL_API_KEY)

                    # Define models:
                    EXTRACT_MODEL = "pixtral-12b-2409"            # Used for JSON extraction
                    IMAGE_COMPARE_MODEL = "pixtral-large-latest"   # Used for image comparison
                    FINAL_ANALYSIS_MODEL = "mistral-large-latest"    # Used for final analysis and classification

                    # Step 1: Extract passport data from the ground truth passport
                    print("Extracting data from ground truth passport...")
                    ground_truth_data = extract_passport_data(f"{ground_data_path}/indian_passport.png", client, EXTRACT_MODEL)
                    if not ground_truth_data:
                        print("Error: Could not extract data from the ground truth passport image.")
                        sys.exit(1)
                    
                    # Copy the JSON schema from the ground truth extraction
                    schema = json.dumps(ground_truth_data, indent=2)
                    
                    # Step 2: Extract passport data from the uploaded passport using the ground truth schema
                    print("Extracting data from uploaded passport using the ground truth schema...")
                    uploaded_data = extract_passport_data(f"{user_data_path}/indian_passport.png", client, EXTRACT_MODEL, schema=schema)
                    if not uploaded_data:
                        print("Error: Could not extract data from the uploaded passport image.")
                        sys.exit(1)
                    
                    # Step 3: Compare the JSON outputs
                    json_comparison = compare_passport_json(ground_truth_data, uploaded_data)
                    print("JSON Comparison:")
                    print(json_comparison)
                    
                    # Step 4: Compare the images via LLM using the 'pixtral-large-latest' model
                    image_comparison = compare_images(f"{ground_data_path}/indian_passport.png", f"{user_data_path}/indian_passport.png", client, IMAGE_COMPARE_MODEL)
                    print("Image Comparison:")
                    print(image_comparison)
                    
                    # Step 5: Provide final analysis (concise, max two sentences) using the 'mistral-large-latest' model
                    final_analysis = analyze_comparisons(json_comparison, image_comparison, client, FINAL_ANALYSIS_MODEL)
                    print("Final Analysis:")
                    print(final_analysis)
                    
                    # Step 6: Classify the application using the classifier function
                    classification = classify_application(json_comparison, image_comparison, client, FINAL_ANALYSIS_MODEL)
                    print("Application Classification:")
                    print(classification)

                    # save the llm analysis
                    data['passport_analysis'] = {
                        "status": classification["classification"],
                        "feedback": final_analysis
                    }

                    with open(json_path, 'w') as f:
                        json.dump(data, f, indent=4)

                    status = classification["classification"]

                st.write("Final Analysis:")
                if status == "green":
                    st.success(final_analysis)
                elif status == "yellow":
                    st.warning(final_analysis)
                else:
                    st.error(final_analysis)
            
                st.subheader("Employment Contract Verification", divider="blue")
                st.write("Please find the LLM analysis of this document below.")

                # Get paths for required files
                employment_contract_path = os.path.join(user_data_path, 'enhanced_employment_agreement.pdf')
                candidate_signature_path = os.path.join(ground_data_path, 'deepti-sign.png')

                # Initialize Mistral client if not already done
                if 'mistral_client' not in st.session_state:
                    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
                    if not MISTRAL_API_KEY:
                        st.error("Error: MISTRAL_API_KEY is not set in the .env file.")
                    else:
                        st.session_state.mistral_client = Mistral(api_key=MISTRAL_API_KEY)

                # Define models
                EXTRACT_MODEL = "mistral-ocr-latest"
                SIGNATURE_COMPARE_MODEL = "pixtral-large-latest"
                FINAL_ANALYSIS_MODEL = "mistral-large-latest"

                # Get application data
                json_path = os.path.join(user_data_path, 'application_data.json')
                with open(json_path, 'r') as f:
                    application_data = json.load(f)

                from contract_and_employer_declaration_processing import classify_contract

                if "contract_analysis" in application_data:
                    contract_classification_result = application_data["contract_analysis"]
                else:
                    # Run contract classification if not already done
                    contract_classification_result = classify_contract(
                        client=st.session_state.mistral_client,
                        employment_contract=Path(employment_contract_path),
                        candidate_signature_path=candidate_signature_path,
                        candidate_name=app_data['name'],
                        candidate_address=app_data['ResidenceData']['AddressOfResidenceInMunich'],
                        passport_expiry_date="12.06.2024",
                        submission_date="15.12.2022",
                        EXTRACT_MODEL=EXTRACT_MODEL,
                        SIGNATURE_COMPARE_MODEL=SIGNATURE_COMPARE_MODEL,
                        FINAL_ANALYSIS_MODEL=FINAL_ANALYSIS_MODEL
                    )

                    # Save the analysis result
                    application_data['contract_analysis'] = contract_classification_result
                    with open(json_path, 'w') as f:
                        json.dump(application_data, f, indent=4)

                # Display contract analysis results
                st.write("**Contract Analysis Results:**")
                classification = contract_classification_result.get('classification', '').lower()
                summary = contract_classification_result.get('summary', '')

                if classification == 'green':
                    st.success(f"✅ {summary}")
                elif classification == 'yellow':
                    st.warning(f"⚠️ {summary}")
                else:
                    st.error(f"❌ {summary}")

                st.write("**Employment Contract Document:**")
                if os.path.exists(employment_contract_path):
                    with open(employment_contract_path, "rb") as f:
                        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" style="width: 100%; height: 80vh;" type="application/pdf"></iframe>'
                    st.markdown(pdf_display, unsafe_allow_html=True)
                else:
                    st.error("Employer declaration not found")

                # Add Declaration of Employment Analysis
                st.write("**Declaration of Employment Analysis Results:**")
                
                # Get paths for required files
                employer_declaration_path = os.path.join(user_data_path, 'deepti-erklaerung-zum-beschaeftigungsverhaeltnis_ba047549-signed.pdf')
                blue_card_criteria_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'document_processor/prompts/blue_card_criteria.txt')

                from contract_and_employer_declaration_processing import analyze_employer_declaration_and_blue_card_fit, StructuredOCRResponse, StructuredOCRResponseforContract

                if "declaration_analysis" in application_data:
                    declaration_accuracy = application_data["declaration_analysis"]
                    blue_card_fit = application_data["blue_card_analysis"]
                else:
                    # Read blue card criteria
                    with open(blue_card_criteria_path, 'r') as f:
                        blue_card_criteria = f.read()

                    # Run declaration and blue card analysis if not already done
                    declaration_accuracy, blue_card_fit = analyze_employer_declaration_and_blue_card_fit(
                        client=st.session_state.mistral_client,
                        employer_declaration=Path(employer_declaration_path),
                        employment_contract=Path(employment_contract_path),
                        blue_card_criteria=blue_card_criteria,
                        EXTRACT_MODEL=EXTRACT_MODEL,
                        FINAL_ANALYSIS_MODEL=FINAL_ANALYSIS_MODEL,
                        StructuredOCRResponse=StructuredOCRResponse,
                        StructuredOCRResponseforContract=StructuredOCRResponseforContract
                    )

                    # Save the analysis results
                    application_data['declaration_analysis'] = json.loads(declaration_accuracy)
                    application_data['blue_card_analysis'] = json.loads(blue_card_fit)
                    with open(json_path, 'w') as f:
                        json.dump(application_data, f, indent=4)

                # Display declaration analysis results
                declaration_data = json.loads(declaration_accuracy) if isinstance(declaration_accuracy, str) else declaration_accuracy
                declaration_classification = declaration_data.get('classification', '').lower()

                if declaration_classification == 'green':
                    st.success("✅ Declaration matches contract perfectly")
                elif declaration_classification == 'yellow':
                    st.warning("⚠️ Minor discrepancies found in declaration")
                else:
                    st.error("❌ Significant discrepancies found in declaration")

                # # Display similarities and differences
                # if 'similarities' in declaration_data:
                #     st.write("**Matching Fields:**")
                #     for similarity in declaration_data['similarities']:
                #         st.write(f"✓ {similarity}")

                # if 'differences' in declaration_data:
                #     st.write("**Discrepancies Found:**")
                #     for difference in declaration_data['differences']:
                #         st.write(f"⚠️ {difference}")

                # Display the employer declaration document
                st.write("**Employer Declaration Document:**")
                if os.path.exists(employer_declaration_path):
                    with open(employer_declaration_path, "rb") as f:
                        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" style="width: 100%; height: 80vh;" type="application/pdf"></iframe>'
                    st.markdown(pdf_display, unsafe_allow_html=True)
                else:
                    st.error("Employer declaration not found")
                
                # Display Blue Card Fit Analysis
                blue_card_data = json.loads(blue_card_fit) if isinstance(blue_card_fit, str) else blue_card_fit
                blue_card_classification = blue_card_data.get('classification', '').lower()

                if 'explanation' in blue_card_data:
                    st.write("**Detailed Analysis:**")
                    for _, v in blue_card_data['explanation'].items():
                        st.write(v)

                st.write("**Blue Card Eligibility Analysis:**")
                if blue_card_classification == 'green':
                    st.success("✅ Candidate meets Blue Card criteria")
                elif blue_card_classification == 'yellow':
                    st.warning("⚠️ Some clarifications needed for Blue Card eligibility")
                else:
                    st.error("❌ Candidate does not meet Blue Card criteria")

                

                # Save contract analysis to evaluation feedback
                if app_id not in EVALUATION_FEEDBACK:
                    EVALUATION_FEEDBACK[app_id] = {}
                EVALUATION_FEEDBACK[app_id]['document_status'] = f"Contract Analysis: {classification.upper()}\n{summary}"
            
            # Decision buttons
            st.write("#### Decision")
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
                
                # Legal Violations Check
                st.write("**Legal Violations Check:**")
                legal_violations = app_data['LegalViolations']
                registry_violations = {
                    'deported': 'No',
                    'rp_denied': 'No',
                    'entry_visa_denied': 'No'
                }
                
                mismatches = []
                risk_factors = 0
                
                # Check each violation type
                violation_mapping = {
                    'ExpelledDeportedOrRepelled': ('deported', 'Deportation History'),
                    'ResidencePermitDenied': ('rp_denied', 'Residence Permit History'),
                    'EntryVisaDenied': ('entry_visa_denied', 'Entry Visa History')
                }
                
                for app_key, (reg_key, display_name) in violation_mapping.items():
                    if legal_violations[app_key] != registry_violations[reg_key]:
                        mismatches.append({
                            'field': display_name,
                            'provided': legal_violations[app_key],
                            'registry': registry_violations[reg_key]
                        })
                        risk_factors += 1
                    if legal_violations[app_key] == 'Yes':
                        risk_factors += 2  # Additional risk for any 'Yes' response
                
                # Display discrepancies
                if len(mismatches) == 0:
                    st.success("✅ No discrepancies found in Legal Violation history.")
                else:
                    st.error("⚠️ Discrepancies found in the following fields:")
                    for mismatch in mismatches:
                        st.write(f"**{mismatch['field']}:**")
                        st.write(f"- Declared: {mismatch['provided']}")
                        st.write(f"- Registry: {mismatch['registry']}")
                
                # Calculate risk score (0.0 to 1.0)
                max_risk_factors = 9  # Maximum possible risk factors (3 mismatches + 6 'Yes' responses)
                risk_score = min(risk_factors / max_risk_factors, 1.0)
                
                # Display risk assessment
                st.write("**Risk Assessment:**")
                risk_level = "Low" if risk_score < 0.3 else "Medium" if risk_score < 0.7 else "High"
                st.write(f"Risk Score: {risk_score:.2f} ({risk_level})")
                risk_color = "green" if risk_score < 0.3 else "orange" if risk_score < 0.7 else "red"
                st.markdown(f"<div style='width:100%; height:20px; background:{risk_color}; border-radius:10px'></div>", unsafe_allow_html=True)
                
                # Rule-based evaluation results
                st.write("**Automated Rule Check Results:**")
                rules_passed = []
                rules_failed = []
                
                # Rule 1: No deportation history
                if legal_violations['ExpelledDeportedOrRepelled'] == 'No':
                    rules_passed.append("No deportation history")
                else:
                    rules_failed.append("Has deportation history")
                
                # Rule 2: No residence permit denials
                if legal_violations['ResidencePermitDenied'] == 'No':
                    rules_passed.append("No residence permit denials")
                else:
                    rules_failed.append("Has residence permit denials")
                
                # Rule 3: No entry visa denials
                if legal_violations['EntryVisaDenied'] == 'No':
                    rules_passed.append("No entry visa denials")
                else:
                    rules_failed.append("Has entry visa denials")
                
                for rule in rules_passed:
                    st.write(f"✅ PASS - {rule}")
                for rule in rules_failed:
                    st.write(f"❌ FAIL - {rule}")
                
                # Save evaluation feedback
                feedback_message = f"Risk Assessment: {risk_level} (Score: {risk_score:.2f})\n"
                if mismatches:
                    feedback_message += "Discrepancies found:\n"
                    for mismatch in mismatches:
                        feedback_message += f"- {mismatch['field']}: Declared '{mismatch['provided']}' vs Registry '{mismatch['registry']}'\n"
                if rules_failed:
                    feedback_message += "Failed Rules:\n"
                    for rule in rules_failed:
                        feedback_message += f"- {rule}\n"
                
                if app_id not in EVALUATION_FEEDBACK:
                    EVALUATION_FEEDBACK[app_id] = {}
                EVALUATION_FEEDBACK[app_id]['criminal_history_status'] = feedback_message
            
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
    
    # If this is a personal info evaluation, save the automatic check results
    if field == 'personal_info_status':
        app_data = st.session_state.applications[st.session_state.applications['application_id'] == app_id].iloc[0]
        applicant_name = app_data['name']
        
        if status == 'Approved':
            save_personal_info_feedback(app_id, 'approved', "")
        elif status == 'Rejected':
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
                
                feedback_message = "Discrepancies found: " + "; ".join(mismatches)
            else:
                feedback_message = "Person not found in central registry"
            
            save_personal_info_feedback(app_id, 'rejected', feedback_message)
    
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
    
    # Navigate two levels up from current file location
    json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'candidate', 'data', app_id, 'application_data.json')
    
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

def save_personal_info_feedback(app_id, status, feedback_message):
    
    # Navigate two levels up from current file location
    json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'candidate', 'data', app_id, 'application_data.json')
    
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
            
        # Update automatic_checks directly
        if 'automatic_checks' not in data:
            data['automatic_checks'] = {}
            
        data['automatic_checks'] = {
            'status': status.lower(),  # Convert to lowercase to match required format
            'feedback': feedback_message
        }
        
        # Write back to the file
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=4)
            
    except Exception as e:
        st.error(f"Error updating application data: {str(e)}")