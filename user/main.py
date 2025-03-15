import streamlit as st
import hashlib
import toml

# Set page configuration
st.set_page_config(page_title="res[AI]de - Visa Immigration Fast Processing", page_icon="🌍", layout="centered")


# File to store user credentials
CREDENTIALS_FILE = ".streamlit/secrets.toml"

# Helper function to hash passwords
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

# Function to load credentials from the TOML file
def load_credentials():
    with open(CREDENTIALS_FILE, "r") as file:
        return toml.load(file)

# Function to save credentials to the TOML file
def save_credentials(credentials):
    with open(CREDENTIALS_FILE, "w") as file:
        toml.dump(credentials, file)

# Helper function to hash passwords
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

# Homepage view
def homepage_view():
    st.title("Welcome to res[AI]de 🌍")
    st.subheader("Fast and Reliable Visa Immigration Processing at Your Fingertips")

    st.write("""
    At **res[AI]de**, we strive to make visa immigration processing seamless and stress-free. 
    With advanced technology and expert consultants, we ensure that your applications are processed quickly and efficiently.
    Whether you're a student, professional, or traveler, our team is here to guide you through every step of the process.
    """)

    # Single "Account" button
    if st.button("Account"):
        if st.session_state.get("logged_in"):  # Check login status
            st.session_state["page"] = "account"  # Navigate to Account page
        else:
            st.session_state["page"] = "login"  # Redirect to Login/Signup page
        st.rerun()  # Force rerun to navigate immediately

# Login and signup view
def login_signup_view():
    st.title("Login / Signup")

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user_email = ""

    # Tabs for Login and Signup
    tab1, tab2 = st.tabs(["Login", "Signup"])

    with tab1:
        st.subheader("Login")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login"):
            if email in st.secrets["users"]:
                hashed_password = hash_password(password)
                if st.secrets["users"][email] == hashed_password:
                    st.session_state.logged_in = True
                    st.session_state.user_email = email
                    st.success("Login successful!")
                    st.session_state["page"] = "account"  # Navigate to Account view
                    st.rerun()  # Force rerun to update login status
                else:
                    st.error("Invalid password. Please try again.")
            else:
                st.error("Email not found. Please sign up first.")

    with tab2:
        st.subheader("Signup")
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")

        if st.button("Signup"):
            if not new_email or not new_password:
                st.error("Please provide both email and password.")
                return

            credentials = load_credentials()
            users = credentials.get("users", {})

            if new_email in users:
                st.warning("Email already registered. Please login instead.")
            else:
                # Hash the new password and save the user
                hashed_password = hash_password(new_password)
                users[new_email] = hashed_password
                credentials["users"] = users
                save_credentials(credentials)
                st.success("Signup successful! You can now log in.")
                st.rerun()  # Force rerun to update login status
    

# # Account view
# def account_view():
#     title_text, logout_btn = st.columns([3, 1])
#     title_text.title("Your Account")
   
#     with logout_btn:
#         if st.button("Logout"):
#             st.session_state.logged_in = False
#             st.session_state.user_email = ""
#             st.session_state["page"] = "home"
#             st.success("You have logged out.")
#             st.rerun()

#     if st.session_state.get("logged_in"):
#         st.write(f"Welcome back, **{st.session_state.user_email}**!")
       
#         col1, col2 = st.columns(2)

#         with col1:
#             if st.button("Start Application"):
#                 st.text_input("Option 1 Input")

#         with col2:
#             if st.button("Track Application"):
#                 st.text_input("Option 2 Input")

#     else:
#         st.warning("You must log in to access this page.")
#         st.session_state["page"] = "login"  # Redirect to login/signup view
#         # st.rerun()

# def account_view():
#     title_text, logout_btn = st.columns([3, 1])
#     title_text.title("Your Account")

#     with logout_btn:
#         if st.button("Logout"):
#             st.session_state.logged_in = False
#             st.session_state.user_email = ""
#             st.session_state["page"] = "home"
#             st.success("You have logged out.")
#             st.rerun()

#     if st.session_state.get("logged_in"):
#         st.write(f"Welcome back, **{st.session_state.user_email}**!")

#         # Session state for tracking views within the account page
#         if "app_state" not in st.session_state:
#             st.session_state.app_state = "main"  # Default state

#         # Main account page actions
#         if st.session_state.app_state == "main":
#             col_stud, col_work = st.columns(2)

#             with col_stud:
#                 if st.button("Start Application"):
#                     st.session_state.app_state = "start_application"
#                     st.rerun()  # Refresh view immediately

#             with col_work:
#                 if st.button("Track Application"):
#                     st.text_input("Enter Application ID:", key="track_id")
#                     if st.button("Track", key="track_button"):
#                         st.success("Tracking your application...")  # Simulated response

#         # Start Application view
#         elif st.session_state.app_state == "start_application":
#             st.subheader("Start Application")
#             st.write("Please choose the type of visa you want to apply for:")
#             col1, col2 = st.columns(2)

#             with col1:
#                 if st.button("Study Visa"):
#                     st.session_state.app_state = "study_visa"
#                     st.rerun()

#             with col2:
#                 if st.button("Work Visa"):
#                     st.session_state.app_state = "work_visa"
#                     st.rerun()

#             # Back button for Start Application
#             if st.button("Back"):
#                 st.session_state.app_state = "main"
#                 st.rerun()

#         # Study Visa information view
#         elif st.session_state.app_state == "study_visa":
#             st.subheader("Study Visa Application")
#             st.write("Before proceeding, ensure you have the following ready:")
#             st.markdown("""
#             - **Proof of Enrollment**: A letter of admission from the institution.
#             - **Financial Documents**: Bank statements, scholarships, or sponsorship proof.
#             - **Passport**: A valid passport with at least 6 months' validity.
#             - **Photos**: Recent passport-size photographs.
#             """)
#             if st.button("Proceed to Application"):
#                 st.success("Proceeding to Study Visa Application...")  # Placeholder for the next step

#             # Back button for Study Visa
#             if st.button("Back"):
#                 st.session_state.app_state = "start_application"
#                 st.rerun()

#         # Work Visa information view
#         elif st.session_state.app_state == "work_visa":
#             st.subheader("Work Visa Application")
#             st.write("Before proceeding, ensure you have the following ready:")
#             st.markdown("""
#             - **Offer Letter**: A valid job offer letter from your employer.
#             - **Work Permit**: Employer-provided or self-applied work permit details.
#             - **Financial Documents**: Proof of financial stability.
#             - **Passport**: A valid passport with at least 6 months' validity.
#             - **Photos**: Recent passport-size photographs.
#             """)
#             if st.button("Proceed to Application"):
#                 st.success("Proceeding to Work Visa Application...")  # Placeholder for the next step

#             # Back button for Work Visa
#             if st.button("Back"):
#                 st.session_state.app_state = "start_application"
#                 st.rerun()

#     else:
#         st.warning("You must log in to access this page.")
#         st.session_state["page"] = "login"  # Redirect to login/signup view
#         st.rerun()

def account_view():
    title_text, logout_btn = st.columns([3, 1])
    title_text.title("Your Account")

    with logout_btn:
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.session_state["page"] = "home"
            st.success("You have logged out.")
            st.rerun()

    if st.session_state.get("logged_in"):
        st.write(f"Welcome back, **{st.session_state.user_email}**!")

        # Session state for tracking views within the account page
        if "app_state" not in st.session_state:
            st.session_state.app_state = "main"  # Default state

        # Main account page actions
        if st.session_state.app_state == "main":
            col_stud, col_work = st.columns(2)

            with col_stud:
                if st.button("Start Application"):
                    st.session_state.app_state = "start_application"
                    st.rerun()

            with col_work:
                if st.button("Track Application"):
                    st.text_input("Enter Application ID:", key="track_id")
                    if st.button("Track", key="track_button"):
                        st.success("Tracking your application...")  # Simulated response

        # Start Application view
        elif st.session_state.app_state == "start_application":
            st.subheader("Start Application")
            st.write("Please choose the type of visa you want to apply for:")
            col1, col2 = st.columns(2)

            with col1:
                if st.button("Study Visa"):
                    st.session_state.app_state = "study_visa"
                    st.rerun()

            with col2:
                if st.button("Work Visa"):
                    st.session_state.app_state = "work_visa"
                    st.rerun()

            # Back button for Start Application
            if st.button("Back"):
                st.session_state.app_state = "main"
                st.rerun()

        # Study Visa information view
        elif st.session_state.app_state == "study_visa":
            st.subheader("Study Visa Application")
            st.write("Before proceeding, ensure you have the following ready:")
            st.markdown("""
            - **Proof of Enrollment**: A letter of admission from the institution.
            - **Financial Documents**: Bank statements, scholarships, or sponsorship proof.
            - **Passport**: A valid passport with at least 6 months' validity.
            - **Photos**: Recent passport-size photographs.
            """)
            if st.button("Proceed to Application"):
                st.session_state["page"] = "application_process"  # Transition to new page
                st.session_state["current_step"] = "personal_info"  # Start the multi-step process
                st.rerun()

            # Back button for Study Visa
            if st.button("Back"):
                st.session_state.app_state = "start_application"
                st.rerun()

        # Work Visa information view
        elif st.session_state.app_state == "work_visa":
            st.subheader("Work Visa Application")
            st.write("Before proceeding, ensure you have the following ready:")
            st.markdown("""
            - **Offer Letter**: A valid job offer letter from your employer.
            - **Work Permit**: Employer-provided or self-applied work permit details.
            - **Financial Documents**: Proof of financial stability.
            - **Passport**: A valid passport with at least 6 months' validity.
            - **Photos**: Recent passport-size photographs.
            """)
            if st.button("Proceed to Application"):
                st.session_state["page"] = "application_process"  # Transition to new page
                st.session_state["current_step"] = "personal_info"  # Start the multi-step process
                st.rerun()

            # Back button for Work Visa
            if st.button("Back"):
                st.session_state.app_state = "start_application"
                st.rerun()

    else:
        st.warning("You must log in to access this page.")
        st.session_state["page"] = "login"  # Redirect to login/signup view
        st.rerun()


def application_process():
    # Initialize state for navigation if not already set
    if "current_step" not in st.session_state:
        st.session_state["current_step"] = "personal_info"  # Default to Personal Info step

    # Call the navigation and step logic
    application_navigation()

def application_navigation():
    # Navigation bar for steps
    nav_buttons = ["Personal Info", "Previous Stays", "Legal Info", "Livelihood Info"]
    nav_columns = st.columns(len(nav_buttons))

    for i, step in enumerate(nav_buttons):
        if nav_columns[i].button(step):
            st.session_state["current_step"] = step.lower().replace(" ", "_")
            st.rerun()

    # Load the current step's view
    if st.session_state["current_step"] == "personal_info":
        personal_info_view()
    elif st.session_state["current_step"] == "previous_stays":
        previous_stays_view()
    elif st.session_state["current_step"] == "legal_info":
        legal_info_view()
    elif st.session_state["current_step"] == "livelihood_info":
        livelihood_info_view()


def personal_info_view():
    st.title("Step 1: Personal Info")
    st.write("Fill in your personal information below:")
    # Add your form fields for personal information
    st.text_input("Full Name", key="full_name")
    st.date_input("Date of Birth", key="dob")
    st.text_input("Contact Number", key="contact_number")
    st.text_input("Email Address", key="email_address")

    # Back button (disabled since it's the first step)
    col_back, col_next = st.columns([1, 1])
    with col_back:
        st.button("Back", disabled=True)
    with col_next:
        if st.button("Next"):
            st.session_state.current_step = "previous_stays"
            st.rerun()


def previous_stays_view():
    st.title("Step 2: Previous Stays")
    st.write("Provide details of your previous stays abroad:")
    # Add your form fields for previous stays
    st.text_area("Details of Previous Stays", key="prev_stays")
    st.file_uploader("Upload Supporting Documents (if any)", type=["pdf", "docx"], key="prev_stays_docs")

    # Navigation buttons
    col_back, col_next = st.columns([1, 1])
    with col_back:
        if st.button("Back"):
            st.session_state.current_step = "personal_info"
            st.rerun()
    with col_next:
        if st.button("Next"):
            st.session_state.current_step = "legal_info"
            st.rerun()


def legal_info_view():
    st.title("Step 3: Legal Info")
    st.write("Provide legal information for your visa application:")
    # Add your form fields for legal information
    st.text_area("Legal History (if any)", key="legal_history")
    st.file_uploader("Upload Legal Documents (if any)", type=["pdf", "docx"], key="legal_docs")

    # Navigation buttons
    col_back, col_next = st.columns([1, 1])
    with col_back:
        if st.button("Back"):
            st.session_state.current_step = "previous_stays"
            st.rerun()
    with col_next:
        if st.button("Next"):
            st.session_state.current_step = "livelihood_info"
            st.rerun()


def livelihood_info_view():
    st.title("Step 4: Livelihood Info")
    st.write("Provide your livelihood details:")
    # Add your form fields for livelihood information
    st.text_input("Current Employer or Occupation", key="livelihood_employer")
    st.text_input("Monthly Income (if applicable)", key="livelihood_income")
    st.file_uploader("Upload Proof of Income (if any)", type=["pdf", "docx"], key="income_docs")

    # Navigation buttons
    col_back, col_next = st.columns([1, 1])
    with col_back:
        if st.button("Back"):
            st.session_state.current_step = "legal_info"
            st.rerun()
    with col_next:
        st.button("Next", disabled=True)  # Disabled as it's the last step


# Routing logic
def router():
    if "page" not in st.session_state:
        st.session_state["page"] = "home"  # Default to homepage

    page = st.session_state["page"]

    if page == "account":
        account_view()
    elif page == "login":
        login_signup_view()
    elif page == "application_process":
        application_process()
    else:
        homepage_view()

# Run the app
if __name__ == "__main__":
    router()