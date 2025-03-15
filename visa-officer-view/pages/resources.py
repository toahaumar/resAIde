import streamlit as st


def show():
    st.title("Resources")

    with st.expander("Visa Processing Guidelines"):
        st.write("""
        ### Standard Processing Guidelines
        
        1. **Personal Information Review**
           - Verify identity matches across all documents
           - Check for completeness of provided information
           - Validate contact information  
        
        2. **Document Verification**
           - Confirm passport validity (minimum 6 months beyond stay)
           - Verify financial documents show adequate funds
           - Check supporting documents specific to visa type
        
        3. **Criminal History Assessment**
           - Apply security rules based on country of origin
           - Consult international databases when necessary
           - Document any concerns for supervisor review
        """)

    with st.expander("Visa Categories"):
        st.write("""
        ### Visa Types and Requirements
        
        **Tourist Visa**
        - Valid passport
        - Proof of financial means
        - Return ticket
        - Travel itinerary
        
        **Student Visa**
        - Valid passport
        - Acceptance letter from recognized institution
        - Proof of financial support
        - Academic records
        
        **Work Visa**
        - Valid passport
        - Job offer letter
        - Work contract
        - Qualifications verification
        - Background check
        
        **Business Visa**
        - Valid passport
        - Letter from employer
        - Invitation from host company
        - Business registration documents
        
        **Family Visa**
        - Valid passport
        - Relationship proof
        - Sponsor's financial documents
        - Accommodation details
        """)

    with st.expander("Common Issues and Solutions"):
        st.write("""
        ### Troubleshooting Guide
        
        **Missing Documents**
        - Send feedback requesting specific missing documents
        - Provide clear instructions on required formats
        - Set reasonable deadline for submission
        
        **Inconsistent Information**
        - Highlight specific inconsistencies
        - Request clarification or correction
        - Document all discrepancies
        
        **Financial Concerns**
        - Specify minimum financial requirements
        - Request additional proof if necessary
        - Consider sponsorship options if applicable
        
        **System Issues**
        - Contact IT support at support@visaoffice.gov
        - Document error codes and screenshots
        - Use backup evaluation forms if system is down
        """)

    with st.expander("Contact Information"):
        st.write("""
        ### Important Contacts
        
        **Technical Support**
        - Email: tech.support@visaoffice.gov
        - Phone: 555-123-4567
        
        **Supervisor Assistance**
        - Email: supervisors@visaoffice.gov
        - Phone: 555-765-4321
        
        **Document Verification Unit**
        - Email: verification@visaoffice.gov
        - Phone: 555-987-6543
        
        **Security Review Team**
        - Email: security@visaoffice.gov
        - Phone: 555-321-0987
        """)
