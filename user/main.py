import shutil
import streamlit as st
import hashlib
import toml
import json
import os
from datetime import datetime
import pandas as pd

# Set page configuration
st.set_page_config(page_title="res[AI]de - Visa Immigration Fast Processing", page_icon="🌍", layout="centered")

# Paths for saving data
DATA_FOLDER = "data"
# File to store user credentials
CREDENTIALS_FILE = ".streamlit/secrets.toml"

# Function to generate a unique application ID
def generate_appid(user_email):
    unique_number = abs(hash(f"{user_email}{datetime.now()}")) % (10 ** 8)
    return f"APP{unique_number:08d}"

# Function to check for an existing app ID
def get_existing_appid(user_email):
    if os.path.exists(CREDENTIALS_FILE):
        credentials = toml.load(CREDENTIALS_FILE)
        return credentials.get("appid", {}).get(user_email, None)
    return None

# Function to save the app ID in the .toml file
def save_appid_to_toml(user_email, appid):
    credentials = {}
    if os.path.exists(CREDENTIALS_FILE):
        credentials = toml.load(CREDENTIALS_FILE)

    # Add appid for the user
    if "appid" not in credentials:
        credentials["appid"] = {}
    credentials["appid"][user_email] = appid

    with open(CREDENTIALS_FILE, "w") as file:
        toml.dump(credentials, file)

# Function to save JSON data locally
def save_data_to_json(appid, data):
    # Create the data folder if it doesn't exist
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)

    # Create the folder for the appid
    app_folder = os.path.join(DATA_FOLDER, appid)
    if not os.path.exists(app_folder):
        os.makedirs(app_folder)

    # Save the JSON file in the appid folder
    json_path = os.path.join(app_folder, "application_data.json")
    with open(json_path, "w") as json_file:
        json.dump(data, json_file, indent=4)


# Helper function to hash passwords
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

# Function to load credentials from the TOML file
def load_credentials():
    if not os.path.exists(CREDENTIALS_FILE):
        # Create the file if it doesn't exist
        os.makedirs(os.path.dirname(CREDENTIALS_FILE), exist_ok=True)
        with open(CREDENTIALS_FILE, "w") as file:
            toml.dump({}, file)
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
        st.write(f"Welcome, **{st.session_state.user_email}**!")

        # Check for an existing application ID
        existing_appid = get_existing_appid(st.session_state.user_email)
        if existing_appid:
            st.write(f"**Existing Application ID:** {existing_appid}")
            st.session_state.appid = existing_appid  # Store the App ID in session state

            # Load existing application data
            app_folder = os.path.join(DATA_FOLDER, existing_appid)
            json_path = os.path.join(app_folder, "application_data.json")
            if os.path.exists(json_path):
                with open(json_path, "r") as json_file:
                    existing_data = json.load(json_file)
                application_status = existing_data.get("application_submission", "in_process")
            else:
                application_status = "in_process"
        else:
            application_status = "in_process"

        # Session state for tracking views within the account page
        if "app_state" not in st.session_state:
            st.session_state.app_state = "main"  # Default state

        # Main account page actions
        if st.session_state.app_state == "main":
            col_stud, col_work = st.columns(2)

            with col_stud:
                if application_status == "in_process":
                    if st.button("Start Application"):
                        if existing_appid:
                            # If an existing application exists, show options to resume or start new
                            st.session_state.app_state = "existing_application"
                        else:
                            # No existing application; go to visa selection view
                            st.session_state.app_state = "visa_selection"
                        st.rerun()
                else:
                    st.write("Your application has been successfully submitted.")

            with col_work:
                if st.button("Track Application"):
                    # st.session_state.app_state = "track_application"
                    st.session_state.page = "track_application"
                    st.rerun()
                    # st.text_input("Enter Application ID:", key="track_id")
                    # if st.button("Track", key="track_button"):
                    #     st.success("Tracking your application...")  # Simulated response

        # Existing Application View (Resume or Start New)
        elif st.session_state.app_state == "existing_application":
            st.subheader("Existing Application Detected")
            st.write("Would you like to resume your existing application or start a new one?")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Resume Application"):
                    st.session_state.page = "application_process"  # Resume application process
                    st.rerun()

            with col2:
                if st.button("Start New Application"):
                    # Delete the old application folder if it exists
                    if existing_appid:
                        old_app_folder = os.path.join(DATA_FOLDER, existing_appid)
                        if os.path.exists(old_app_folder):
                            shutil.rmtree(old_app_folder)  # Delete the folder and all its contents
                            st.write(f"Deleted old application data for App ID: {existing_appid}")

                    # Generate a new App ID for the user
                    new_appid = generate_appid(st.session_state.user_email)
                    save_appid_to_toml(st.session_state.user_email, new_appid)
                    st.session_state.appid = new_appid

                    # Redirect to visa selection view
                    st.session_state.app_state = "visa_selection"
                    st.rerun()

        # Visa selection view for new application
        elif st.session_state.app_state == "visa_selection":
            st.subheader("Choose Visa Type")
            st.write("Please choose the type of visa you want to apply for:")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Study Visa"):
                    # Application process starts for Study Visa
                    st.session_state.page = "application_process"
                    st.session_state.visa_type = "study"
                    st.rerun()

            with col2:
                if st.button("Work Visa"):
                    # Application process starts for Work Visa
                    st.session_state.page = "application_process"
                    st.session_state.visa_type = "work"
                    st.rerun()

    else:
        st.warning("You must log in to access this page.")
        st.session_state["page"] = "login"  # Redirect to login/signup view
        st.rerun()

def application_process(user_email):
    # Initialize state for navigation if not already set
    if "current_step" not in st.session_state:
        st.session_state["current_step"] = "personal_info"  # Default to Personal Info step

    # Call navigation logic
    application_navigation(user_email)


def application_navigation(user_email):
    # Navigation bar for steps
    nav_buttons = ["Personal Info", "Previous Stays", "Legal Info", "Livelihood Info"]
    nav_columns = st.columns(len(nav_buttons))

    for i, step in enumerate(nav_buttons):
        if nav_columns[i].button(step):
            st.session_state["current_step"] = step.lower().replace(" ", "_")
            st.rerun()

    # Load the current step's view
    # if st.session_state["current_step"] == "account":
    #     account_view()
    if st.session_state["current_step"] == "personal_info":
        personal_info_form(user_email)
    elif st.session_state["current_step"] == "entry_and_previous_stays":
        entry_and_previous_stays_form(user_email)
    elif st.session_state["current_step"] == "legal_info":
        legal_info_form(user_email)
    elif st.session_state["current_step"] == "livelihood_info":
        livelihood_info_form(user_email)

def personal_info_form(user_email):
    st.title("Step 1: Personal Information")
    st.write("Fill in your personal information, purpose of stay, and residence details.")

    # Load existing app ID and data, if available
    appid = st.session_state.get("appid", get_existing_appid(user_email))
    if appid:
        app_folder = os.path.join(DATA_FOLDER, appid)
        json_path = os.path.join(app_folder, "application_data.json")
        if os.path.exists(json_path):
            with open(json_path, "r") as json_file:
                existing_data = json.load(json_file)
            personal_info = existing_data.get("PersonalInformation", {})
            purpose_data = existing_data.get("PurposeAndDurationOfStay", {})
            residence_data = existing_data.get("ResidenceData", {})
        else:
            personal_info, purpose_data, residence_data = {}, {}, {}
    else:
        personal_info, purpose_data, residence_data = {}, {}, {}

    # Personal Information Section
    surname = st.text_input("Surname*", value=personal_info.get("Surname", ""), disabled=bool(personal_info.get("Surname")))
    first_name = st.text_input("First Name*", value=personal_info.get("FirstName", ""), disabled=bool(personal_info.get("FirstName")))
    former_names = st.text_input("Former Names (if any)", value=personal_info.get("FormerNames", ""), disabled=bool(personal_info.get("FormerNames")))
    sex = st.selectbox("Sex*", ["Male", "Female", "Other"], index=["Male", "Female", "Other"].index(personal_info.get("Sex", "Male")), disabled=bool(personal_info.get("Sex")))
    dob = st.date_input("Date of Birth*", value=pd.to_datetime(personal_info.get("DateOfBirth", "1985-01-01")), disabled=bool(personal_info.get("DateOfBirth")))
    place_of_birth = st.text_input("Place of Birth*", value=personal_info.get("PlaceOfBirth", ""), disabled=bool(personal_info.get("PlaceOfBirth")))
    country_of_birth = st.text_input("Country of Birth*", value=personal_info.get("CountryOfBirth", ""), disabled=bool(personal_info.get("CountryOfBirth")))
    nationality = st.text_input("Current Nationality*", value=personal_info.get("CurrentNationality", ""), disabled=bool(personal_info.get("CurrentNationality")))
    marital_status = st.selectbox("Marital Status*", ["Single", "Married", "Divorced", "Widowed"], 
                                  index=["Single", "Married", "Divorced", "Widowed"].index(personal_info.get("MaritalStatus", "Single")), disabled=bool(personal_info.get("MaritalStatus")))
    height = st.text_input("Height (cm)*", value=personal_info.get("Height", ""), disabled=bool(personal_info.get("Height")))
    eye_color = st.text_input("Eye Colour*", value=personal_info.get("EyeColour", ""), disabled=bool(personal_info.get("EyeColour")))

    # Purpose and Duration of Stay Section
    st.write("---")
    st.subheader("Purpose and Duration of Stay")
    purpose_of_stay = st.text_input("Purpose of Stay*", value=purpose_data.get("PurposeOfStay", ""), disabled=bool(purpose_data.get("PurposeOfStay")))
    employer_host = st.text_input("Employer or Host*", value=purpose_data.get("EmployerOrHost", ""), disabled=bool(purpose_data.get("EmployerOrHost")))
    duration_of_stay = st.text_input("Duration of Stay*", value=purpose_data.get("DurationOfStay", ""), disabled=bool(purpose_data.get("DurationOfStay")))

    # Residence Data Section
    st.write("---")
    st.subheader("Residence Data")
    address_residence = st.text_input("Address of Residence in Germany*", value=residence_data.get("AddressOfResidenceInMunich", ""), disabled=bool(residence_data.get("AddressOfResidenceInMunich")))
    moved_from_address = st.text_input("Moved From Address*", value=residence_data.get("MovedFromAddress", ""), disabled=bool(residence_data.get("MovedFromAddress")))
    date_of_move = st.date_input("Date of Move to Current Address*", value=pd.to_datetime(residence_data.get("DateOfMoveToMunich", "2020-01-01")), disabled=bool(residence_data.get("DateOfMoveToMunich")))
    further_residence = st.text_input("Further Residence in Germany*", value=residence_data.get("FurtherResidenceInGermany", ""), disabled=bool(residence_data.get("FurtherResidenceInGermany")))
    retain_residence_outside = st.text_input("Retain Permanent Residence Outside Germany*", 
                                             value=residence_data.get("RetainPermanentResidenceOutsideGermany", ""), disabled=bool(residence_data.get("RetainPermanentResidenceOutsideGermany")))
    last_residence_origin = st.text_input("Last Residence in Country of Origin*", 
                                          value=residence_data.get("LastResidenceInCountryOfOrigin", ""), disabled=bool(residence_data.get("LastResidenceInCountryOfOrigin")))

    # back to account page
    col_back, col_next = st.columns([1, 1])
    with col_back:
        if st.button("Back to Account", use_container_width=True):
            st.session_state["page"] = "account"
            st.rerun()
    with col_next:
    # Next button
        if st.button("Next", use_container_width=True):
            # Save data
            updated_data = {
                "PersonalInformation": {
                    "Surname": surname,
                    "FirstName": first_name,
                    "FormerNames": former_names,
                    "Sex": sex,
                    "DateOfBirth": str(dob),
                    "PlaceOfBirth": place_of_birth,
                    "CountryOfBirth": country_of_birth,
                    "CurrentNationality": nationality,
                    "MaritalStatus": marital_status,
                    "Height": height,
                    "EyeColour": eye_color
                },
                "PurposeAndDurationOfStay": {
                    "PurposeOfStay": purpose_of_stay,
                    "EmployerOrHost": employer_host,
                    "DurationOfStay": duration_of_stay
                },
                "ResidenceData": {
                    "AddressOfResidenceInMunich": address_residence,
                    "MovedFromAddress": moved_from_address,
                    "DateOfMoveToMunich": str(date_of_move),
                    "FurtherResidenceInGermany": further_residence,
                    "RetainPermanentResidenceOutsideGermany": retain_residence_outside,
                    "LastResidenceInCountryOfOrigin": last_residence_origin
                },
                "visa_type": st.session_state.get("visa_type", "study")

            }

            # Create app ID if it doesn't exist
            if not appid:
                appid = generate_appid(user_email)
                save_appid_to_toml(user_email, appid)

            # Ensure the folder for app ID exists
            app_folder = os.path.join(DATA_FOLDER, appid)
            if not os.path.exists(app_folder):
                os.makedirs(app_folder)

            # Save data to JSON
            save_data_to_json(appid, updated_data)

            # Move to the next step
            st.session_state.current_step = "entry_and_previous_stays"
            st.session_state.appid = appid
            st.rerun()

def entry_and_previous_stays_form(user_email):
    st.title("Step 2: Entry and Previous Stays")
    st.write("Provide details of your entry to and stays in Germany.")

    # Load existing app ID and data, if available
    appid = st.session_state.get("appid", get_existing_appid(user_email))
    if appid:
        app_folder = os.path.join(DATA_FOLDER, appid)
        json_path = os.path.join(app_folder, "application_data.json")
        if os.path.exists(json_path):
            with open(json_path, "r") as json_file:
                existing_data = json.load(json_file)
            entry_stays_data = existing_data.get("EntryAndPreviousStays", {})
        else:
            entry_stays_data = {}
    else:
        entry_stays_data = {}

    # Ensure data integrity by checking if keys already exist in the JSON
    first_date_key = "FirstDateOfEntryIntoGermany"
    uninterrupted_key = "InGermanyWithoutInterruptionSince"
    stays_abroad_key = "StaysAbroadExceedingSixMonths"
    former_stays_key = "FormerStaysInGermany"

    first_entry = st.date_input(
        "First Date of Entry into Germany*",
        value=pd.to_datetime(entry_stays_data.get(first_date_key, "2015-01-01")),
        disabled=bool(entry_stays_data.get(first_date_key))
    )
    uninterrupted_since = st.date_input(
        "In Germany Without Interruption Since*",
        value=pd.to_datetime(entry_stays_data.get(uninterrupted_key, "2016-01-01")),
        disabled=bool(entry_stays_data.get(uninterrupted_key))
    )
    stays_abroad = st.text_area(
        "Stays Abroad Exceeding Six Months (provide details in the format: Country, Start Date, End Date per line)",
        value="\n".join(
            [
                f"{stay['Country']}, {stay['From']}, {stay['Until']}"
                for stay in entry_stays_data.get(stays_abroad_key, [])
            ]
        ) if stays_abroad_key in entry_stays_data else "",
        disabled=bool(entry_stays_data.get(stays_abroad_key)),
        placeholder="e.g., France, 2020-01-01, 2020-06-30"
    )
    former_stays = st.text_area(
        "Former Stays in Germany (provide details in the format: Country, Start Date, End Date per line)",
        value="\n".join(
            [
                f"{stay['Country']}, {stay['From']}, {stay['Until']}"
                for stay in entry_stays_data.get(former_stays_key, [])
            ]
        ) if former_stays_key in entry_stays_data else "",
        disabled=bool(entry_stays_data.get(former_stays_key)),
        placeholder="e.g., Germany, 2014-06-01, 2014-12-01"
    )

    # Navigation buttons
    col_back, col_next = st.columns([1, 1])
    with col_back:
        if st.button("Back to Personal Info", use_container_width=True):
            st.session_state.current_step = "personal_info"
            st.rerun()
    with col_next:
        if st.button("Next", use_container_width=True):
            # Parse stays_abroad text into structured data only if the field is editable
            stays_abroad_list = entry_stays_data.get(stays_abroad_key, [])
            if not entry_stays_data.get(stays_abroad_key) and stays_abroad.strip():
                for line in stays_abroad.strip().split("\n"):
                    try:
                        country, start_date, end_date = map(str.strip, line.split(","))
                        stays_abroad_list.append(
                            {"Country": country, "From": start_date, "Until": end_date}
                        )
                    except ValueError:
                        st.warning("Invalid format in Stays Abroad. Please follow the format: Country, Start Date, End Date.")
                        return

            # Parse former_stays text into structured data only if the field is editable
            former_stays_list = entry_stays_data.get(former_stays_key, [])
            if not entry_stays_data.get(former_stays_key) and former_stays.strip():
                for line in former_stays.strip().split("\n"):
                    try:
                        country, start_date, end_date = map(str.strip, line.split(","))
                        former_stays_list.append(
                            {"Country": country, "From": start_date, "Until": end_date}
                        )
                    except ValueError:
                        st.warning("Invalid format in Former Stays. Please follow the format: Country, Start Date, End Date.")
                        return

            # Load existing data to ensure no overwrite of other sections
            if os.path.exists(json_path):
                with open(json_path, "r") as json_file:
                    data = json.load(json_file)
            else:
                data = {}

            # Update Entry and Previous Stays data
            updated_entry_stays_data = {
                first_date_key: str(first_entry),
                uninterrupted_key: str(uninterrupted_since),
                stays_abroad_key: stays_abroad_list,
                former_stays_key: former_stays_list,
            }
            data["EntryAndPreviousStays"] = updated_entry_stays_data

            # Save updated data to JSON
            save_data_to_json(appid, data)

            # Move to the next step
            st.session_state.current_step = "legal_info"
            st.rerun()

def legal_info_form(user_email):
    st.title("Step 3: Legal Info")
    st.write("Provide legal information for your visa application.")

    # Load existing app ID and data, if available
    appid = st.session_state.get("appid", get_existing_appid(user_email))
    if appid:
        app_folder = os.path.join(DATA_FOLDER, appid)
        json_path = os.path.join(app_folder, "application_data.json")
        if os.path.exists(json_path):
            with open(json_path, "r") as json_file:
                existing_data = json.load(json_file)
            legal_info_data = existing_data.get("LegalViolations", {})
        else:
            legal_info_data = {}
    else:
        legal_info_data = {}

    # Prefill form fields with existing data or leave editable if no data
    expelled_deported = st.selectbox(
        "Have you been expelled, deported, or repelled?",
        ["No", "Yes"],
        index=["No", "Yes"].index(legal_info_data.get("ExpelledDeportedOrRepelled", "No")),
        disabled=bool(legal_info_data.get("ExpelledDeportedOrRepelled"))
    )
    if expelled_deported == "Yes":
        expulsion_date = st.date_input(
            "If Yes, Date of Expulsion/Deportation",
            value=pd.to_datetime(legal_info_data.get("IfYesDate", "2000-01-01")),
            disabled=bool(legal_info_data.get("IfYesDate"))
        )
        by_authority = st.text_input(
            "By which authority?",
            value=legal_info_data.get("ByAuthority", ""),
            disabled=bool(legal_info_data.get("ByAuthority"))
        )
    else:
        expulsion_date = None
        by_authority = None

    residence_permit_denied = st.selectbox(
        "Have you been denied a residence permit?",
        ["No", "Yes"],
        index=["No", "Yes"].index(legal_info_data.get("ResidencePermitDenied", "No")),
        disabled=bool(legal_info_data.get("ResidencePermitDenied"))
    )
    if residence_permit_denied == "Yes":
        permit_date = st.date_input(
            "If Yes, Date of Denial",
            value=pd.to_datetime(legal_info_data.get("IfYesDatePermit", "2000-01-01")),
            disabled=bool(legal_info_data.get("IfYesDatePermit"))
        )
        by_authority_permit = st.text_input(
            "By which authority?",
            value=legal_info_data.get("ByAuthorityPermit", ""),
            disabled=bool(legal_info_data.get("ByAuthorityPermit"))
        )
    else:
        permit_date = None
        by_authority_permit = None

    entry_visa_denied = st.selectbox(
        "Have you been denied an entry visa?",
        ["No", "Yes"],
        index=["No", "Yes"].index(legal_info_data.get("EntryVisaDenied", "No")),
        disabled=bool(legal_info_data.get("EntryVisaDenied"))
    )
    if entry_visa_denied == "Yes":
        visa_date = st.date_input(
            "If Yes, Date of Denial",
            value=pd.to_datetime(legal_info_data.get("IfYesDateVisa", "2000-01-01")),
            disabled=bool(legal_info_data.get("IfYesDateVisa"))
        )
        by_authority_visa = st.text_input(
            "By which authority?",
            value=legal_info_data.get("ByAuthorityVisa", ""),
            disabled=bool(legal_info_data.get("ByAuthorityVisa"))
        )
    else:
        visa_date = None
        by_authority_visa = None

    long_term_permit = st.selectbox(
        "Do you own a long-term residence permit in the EU?",
        ["No", "Yes"],
        index=["No", "Yes"].index(legal_info_data.get("OwnLongTermResidencePermitEU", "No")),
        disabled=bool(legal_info_data.get("OwnLongTermResidencePermitEU"))
    )

    eu_blue_card = st.selectbox(
        "Do you own an EU Blue Card?",
        ["No", "Yes"],
        index=["No", "Yes"].index(legal_info_data.get("OwnEUBlueCard", "No")),
        disabled=bool(legal_info_data.get("OwnEUBlueCard"))
    )

    # Navigation buttons
    col_back, col_next = st.columns([1, 1])
    with col_back:
        if st.button("Back to Entry and Previous Stays", use_container_width=True):
            st.session_state.current_step = "entry_and_previous_stays"
            st.rerun()
    with col_next:
        if st.button("Next", use_container_width=True):
            # Load existing data
            app_folder = os.path.join(DATA_FOLDER, appid)
            json_path = os.path.join(app_folder, "application_data.json")
            with open(json_path, "r") as json_file:
                data = json.load(json_file)

            # Update Legal Violations data
            updated_legal_info_data = {
                "ExpelledDeportedOrRepelled": expelled_deported,
                "IfYesDate": str(expulsion_date) if expulsion_date else "",
                "ByAuthority": by_authority if by_authority else "",
                "ResidencePermitDenied": residence_permit_denied,
                "IfYesDatePermit": str(permit_date) if permit_date else "",
                "ByAuthorityPermit": by_authority_permit if by_authority_permit else "",
                "EntryVisaDenied": entry_visa_denied,
                "IfYesDateVisa": str(visa_date) if visa_date else "",
                "ByAuthorityVisa": by_authority_visa if by_authority_visa else "",
                "OwnLongTermResidencePermitEU": long_term_permit,
                "OwnEUBlueCard": eu_blue_card
            }
            data["LegalViolations"] = updated_legal_info_data

            # Save updated data to JSON
            save_data_to_json(appid, data)

            # Move to the next step
            st.session_state.current_step = "livelihood_info"
            st.rerun()

# def livelihood_info_form(user_email):
#     st.title("Step 4: Livelihood Information")
#     st.write("Provide your livelihood details.")

#     # Load existing app ID and data, if available
#     appid = st.session_state.get("appid", get_existing_appid(user_email))
#     if appid:
#         app_folder = os.path.join(DATA_FOLDER, appid)
#         json_path = os.path.join(app_folder, "application_data.json")
#         if os.path.exists(json_path):
#             with open(json_path, "r") as json_file:
#                 existing_data = json.load(json_file)
#             livelihood_info_data = existing_data.get("LivelihoodInformation", {})
#         else:
#             livelihood_info_data = {}
#     else:
#         livelihood_info_data = {}

#     # Prefill form fields with existing data or leave editable if no data
#     subsistence_means = st.text_input(
#         "Means of Subsistence (e.g., Employment, Savings, etc.)",
#         value=livelihood_info_data.get("MeansOfSubsistence", ""),
#         disabled=bool(livelihood_info_data.get("MeansOfSubsistence"))
#     )

#     # Upload supporting documents
#     uploaded_docs = st.file_uploader(
#         "Upload Proof of Income or Livelihood Documents (optional)",
#         type=["pdf", "docx", "jpg", "png"],
#         key="livelihood_docs"
#     )

#     # Save the uploaded document locally
#     uploaded_doc_path = ""
#     if uploaded_docs is not None:
#         # Ensure the app folder exists
#         if not os.path.exists(app_folder):
#             os.makedirs(app_folder)

#         uploaded_doc_path = os.path.join(app_folder, uploaded_docs.name)
#         with open(uploaded_doc_path, "wb") as file:
#             file.write(uploaded_docs.read())

#     # Navigation buttons
#     col_back, col_next = st.columns([1, 1])
#     with col_back:
#         if st.button("Back to Legal Info", use_container_width=True):
#             st.session_state.current_step = "legal_info"
#             st.rerun()
#     with col_next:
#         if st.button("Finish", use_container_width=True):
#             # Load existing data
#             if os.path.exists(json_path):
#                 with open(json_path, "r") as json_file:
#                     data = json.load(json_file)
#             else:
#                 data = {}

#             # Save Livelihood Info data
#             updated_livelihood_info_data = {
#                 "MeansOfSubsistence": subsistence_means,
#                 "UploadedDocuments": uploaded_doc_path if uploaded_docs else livelihood_info_data.get("UploadedDocuments", "")
#             }
#             data["LivelihoodInformation"] = updated_livelihood_info_data

#             # Save updated data to JSON
#             save_data_to_json(appid, data)

#             # Redirect to success page
#             st.session_state["page"] = "success_page"
#             st.rerun()

# def livelihood_info_form(user_email):
#     st.title("Step 4: Livelihood Information")
#     st.write("Provide your livelihood details.")

#     # Load existing app ID and data, if available
#     appid = st.session_state.get("appid", get_existing_appid(user_email))
#     if appid:
#         app_folder = os.path.join(DATA_FOLDER, appid)
#         json_path = os.path.join(app_folder, "application_data.json")
#         if os.path.exists(json_path):
#             with open(json_path, "r") as json_file:
#                 existing_data = json.load(json_file)
#             livelihood_info_data = existing_data.get("LivelihoodInformation", {})
#         else:
#             livelihood_info_data = {}
#     else:
#         livelihood_info_data = {}

#     # Prefill form fields with existing data or leave editable if no data
#     subsistence_means = st.text_input(
#         "Means of Subsistence (e.g., Employment, Savings, etc.)",
#         value=livelihood_info_data.get("MeansOfSubsistence", ""),
#         disabled=bool(livelihood_info_data.get("MeansOfSubsistence"))
#     )

#     # Upload supporting documents
#     uploaded_docs = st.file_uploader(
#         "Upload Proof of Income or Livelihood Documents (optional)",
#         type=["pdf", "docx", "jpg", "png"],
#         key="livelihood_docs"
#     )

#     # Save the uploaded document locally
#     uploaded_doc_path = ""
#     if uploaded_docs is not None:
#         # Ensure the app folder exists
#         if not os.path.exists(app_folder):
#             os.makedirs(app_folder)

#         uploaded_doc_path = os.path.join(app_folder, uploaded_docs.name)
#         with open(uploaded_doc_path, "wb") as file:
#             file.write(uploaded_docs.read())

#     # Navigation buttons
#     col_back, col_next = st.columns([1, 1])
#     with col_back:
#         if st.button("Back to Legal Info", use_container_width=True):
#             st.session_state.current_step = "legal_info"
#             st.rerun()
#     with col_next:
#         if st.button("Finish", use_container_width=True):
#             # Load existing data
#             if os.path.exists(json_path):
#                 with open(json_path, "r") as json_file:
#                     data = json.load(json_file)
#             else:
#                 data = {}

#             # Save Livelihood Info data
#             updated_livelihood_info_data = {
#                 "MeansOfSubsistence": subsistence_means,
#                 "UploadedDocuments": uploaded_doc_path if uploaded_docs else livelihood_info_data.get("UploadedDocuments", "")
#             }
#             data["LivelihoodInformation"] = updated_livelihood_info_data

#             # Set application status to success
#             data["status"] = "success"

#             # Save updated data to JSON
#             save_data_to_json(appid, data)

#             # Redirect to success page
#             st.session_state["page"] = "success_page"
#             st.rerun()

# def livelihood_info_form(user_email):
#     st.title("Step 4: Livelihood Information")
#     st.write("Provide your livelihood details.")

#     # Load existing app ID and data, if available
#     appid = st.session_state.get("appid", get_existing_appid(user_email))
#     if appid:
#         app_folder = os.path.join(DATA_FOLDER, appid)
#         json_path = os.path.join(app_folder, "application_data.json")
#         if os.path.exists(json_path):
#             with open(json_path, "r") as json_file:
#                 existing_data = json.load(json_file)
#             livelihood_info_data = existing_data.get("LivelihoodInformation", {})
#         else:
#             livelihood_info_data = {}
#     else:
#         livelihood_info_data = {}

#     # Prefill form fields with existing data or leave editable if no data
#     subsistence_means = st.text_input(
#         "Means of Subsistence (e.g., Employment, Savings, etc.)",
#         value=livelihood_info_data.get("MeansOfSubsistence", ""),
#         disabled=bool(livelihood_info_data.get("MeansOfSubsistence"))
#     )

#     # Upload supporting documents
#     uploaded_docs = st.file_uploader(
#         "Upload Proof of Income or Livelihood Documents (optional)",
#         type=["pdf", "docx", "jpg", "png"],
#         accept_multiple_files=True,
#         key="livelihood_docs"
#     )

#     # Save the uploaded documents locally
#     uploaded_doc_paths = []
#     if uploaded_docs:
#         # Ensure the app folder exists
#         if not os.path.exists(app_folder):
#             os.makedirs(app_folder)

#         for doc in uploaded_docs:
#             doc_path = os.path.join(app_folder, doc.name)
#             with open(doc_path, "wb") as file:
#                 file.write(doc.read())
#             uploaded_doc_paths.append(doc_path)

#     # Navigation buttons
#     col_back, col_next = st.columns([1, 1])
#     with col_back:
#         if st.button("Back to Legal Info", use_container_width=True):
#             st.session_state.current_step = "legal_info"
#             st.rerun()
#     with col_next:
#         if st.button("Finish", use_container_width=True):
#             # Load existing data
#             if os.path.exists(json_path):
#                 with open(json_path, "r") as json_file:
#                     data = json.load(json_file)
#             else:
#                 data = {}

#             # Save Livelihood Info data
#             updated_livelihood_info_data = {
#                 "MeansOfSubsistence": subsistence_means,
#                 "UploadedDocuments": uploaded_doc_paths if uploaded_docs else livelihood_info_data.get("UploadedDocuments", [])
#             }
#             data["LivelihoodInformation"] = updated_livelihood_info_data

#             # Set application status to success
#             data["status"] = "success"

#             # Save updated data to JSON
#             save_data_to_json(appid, data)

#             # Redirect to success page
#             st.session_state["page"] = "success_page"
#             st.rerun()

def livelihood_info_form(user_email):
    st.title("Step 4: Livelihood Information")
    st.write("Provide your livelihood details.")

    # Load existing app ID and data, if available
    appid = st.session_state.get("appid", get_existing_appid(user_email))
    if appid:
        app_folder = os.path.join(DATA_FOLDER, appid)
        json_path = os.path.join(app_folder, "application_data.json")
        if os.path.exists(json_path):
            with open(json_path, "r") as json_file:
                existing_data = json.load(json_file)
            livelihood_info_data = existing_data.get("LivelihoodInformation", {})
        else:
            livelihood_info_data = {}
    else:
        livelihood_info_data = {}

    # Prefill form fields with existing data or leave editable if no data
    subsistence_means = st.text_input(
        "Means of Subsistence (e.g., Employment, Savings, etc.)",
        value=livelihood_info_data.get("MeansOfSubsistence", ""),
        disabled=bool(livelihood_info_data.get("MeansOfSubsistence"))
    )

    # Upload supporting documents
    passport_doc = st.file_uploader(
        "Upload Passport (required)",
        type=["pdf", "docx", "jpg", "png"],
        key="passport_doc"
    )
    work_contract_doc = st.file_uploader(
        "Upload Work Contract (required)",
        type=["pdf", "docx", "jpg", "png"],
        key="work_contract_doc"
    )
    employer_declaration_doc = st.file_uploader(
        "Upload Employer Declaration (required)",
        type=["pdf", "docx", "jpg", "png"],
        key="employer_declaration_doc"
    )

    # Save the uploaded documents locally
    uploaded_doc_paths = {}
    if passport_doc:
        passport_path = os.path.join(app_folder, passport_doc.name)
        with open(passport_path, "wb") as file:
            file.write(passport_doc.read())
        uploaded_doc_paths["Passport"] = passport_path

    if work_contract_doc:
        work_contract_path = os.path.join(app_folder, work_contract_doc.name)
        with open(work_contract_path, "wb") as file:
            file.write(work_contract_doc.read())
        uploaded_doc_paths["WorkContract"] = work_contract_path

    if employer_declaration_doc:
        employer_declaration_path = os.path.join(app_folder, employer_declaration_doc.name)
        with open(employer_declaration_path, "wb") as file:
            file.write(employer_declaration_doc.read())
        uploaded_doc_paths["EmployerDeclaration"] = employer_declaration_path

    # Navigation buttons
    col_back, col_next = st.columns([1, 1])
    with col_back:
        if st.button("Back to Legal Info", use_container_width=True):
            st.session_state.current_step = "legal_info"
            st.rerun()
    with col_next:
        if st.button("Finish", use_container_width=True):
            # Load existing data
            if os.path.exists(json_path):
                with open(json_path, "r") as json_file:
                    data = json.load(json_file)
            else:
                data = {}

            # Save Livelihood Info data
            updated_livelihood_info_data = {
                "MeansOfSubsistence": subsistence_means,
                "UploadedDocuments": uploaded_doc_paths if uploaded_doc_paths else livelihood_info_data.get("UploadedDocuments", {})
            }
            data["LivelihoodInformation"] = updated_livelihood_info_data

            # Set application status to success
            data["application_submission"] = "success"

            # Save updated data to JSON
            save_data_to_json(appid, data)

            # Redirect to success page
            st.session_state["page"] = "success_page"
            st.rerun()

# Success Page
def success_page():
    st.title("Application Submitted Successfully!")
    st.write("Your application has been saved successfully.")
    st.write(f"**Tracking ID:** {st.session_state.get('appid')}")

    col_track, col_account = st.columns([1, 1])
    with col_track:
        if st.button("Track Application", use_container_width=True):
            st.session_state["page"] = "track_application"  # Change page to Track Application
            st.rerun()
    with col_account:
        if st.button("Go to Home", use_container_width=True):
            st.session_state["page"] = "home"  # Return to Account Page
            st.rerun()

def track_application_view():
    st.title("Track Application Status")
    st.write("Check the current status of your visa application.")

    # Load existing app ID and data, if available
    appid = st.session_state.get("appid", get_existing_appid(st.session_state.user_email))
    if appid:
        app_folder = os.path.join(DATA_FOLDER, appid)
        json_path = os.path.join(app_folder, "application_data.json")
        if os.path.exists(json_path):
            with open(json_path, "r") as json_file:
                existing_data = json.load(json_file)
            application_status = existing_data.get("application_status", "application_submitted")
        else:
            application_status = "application_submitted"
    else:
        st.error("No application found.")
        return

    # Define the stages and sub-statuses
    stages = [
        {"status": "application_submitted", "label": "Application Submitted", "color": "gray"},
        {"status": "visa_officer_assigned", "label": "Visa Officer Assigned", "color": "gray"},
        {"status": "automatic_checks_completed", "label": "Automatic Checks Completed", "color": "gray", "sub_statuses": [
            {"status": "clear", "label": "Clear", "color": "gray"},
            {"status": "feedback_required", "label": "Feedback Required", "color": "gray"},
            {"status": "denied", "label": "Denied", "color": "gray"}
        ]},
        {"status": "visa_officer_check_completed", "label": "Visa Officer Check Completed", "color": "gray", "sub_statuses": [
            {"status": "clear", "label": "Clear", "color": "gray"},
            {"status": "feedback_required", "label": "Feedback Required", "color": "gray"},
            {"status": "denied", "label": "Denied", "color": "gray"}
        ]},
        {"status": "visa_appointment_given", "label": "Visa Appointment Given", "color": "gray"}
    ]

    # Update the colors based on the current status
    for stage in stages:
        if stage["status"] == application_status:
            stage["color"] = "green"
            break
        stage["color"] = "green"
        if "sub_statuses" in stage:
            for sub_status in stage["sub_statuses"]:
                if sub_status["status"] == application_status:
                    sub_status["color"] = "green"
                    break
                sub_status["color"] = "green"

    # # Display the stages with colored circles
    # for stage in stages:
    #     st.markdown(f'<span style="color:{stage["color"]};">&#9679;</span> {stage["label"]}', unsafe_allow_html=True)
    #     if "sub_statuses" in stage:
    #         for sub_status in stage["sub_statuses"]:
    #             st.markdown(f'&nbsp;&nbsp;&nbsp;&nbsp;<span style="color:{sub_status["color"]};">&#9679;</span> {sub_status["label"]}', unsafe_allow_html=True)
    # Display the stages with colored circles
    for stage in stages:
        st.markdown(f'<span style="color:{stage["color"]};">&#9679;</span> {stage["label"]}', unsafe_allow_html=True)
        if stage["color"] == "green" and "sub_statuses" in stage:
            for sub_status in stage["sub_statuses"]:
                st.markdown(f'&nbsp;&nbsp;&nbsp;&nbsp;<span style="color:{sub_status["color"]};">&#9679;</span> {sub_status["label"]}', unsafe_allow_html=True)

    # Button to go back to the account page
    if st.button("Go to Home", use_container_width=True):
        st.session_state["page"] = "home"
        st.rerun()


# Routing logic
def router():
    if "page" not in st.session_state:
        st.session_state["page"] = "home"  # Default to homepage

    page = st.session_state["page"]

    if page == "account":
        account_view()
    elif page == "login":
        login_signup_view()
    # elif page == "application_process":
    #     user_email = st.session_state.user_email
    #     application_process(user_email)
    #     # application_process()
    elif st.session_state["page"] == "application_process":
        application_process(st.session_state.get("user_email", ""))
    elif st.session_state["page"] == "success_page":
        success_page()
    elif page == "track_application":
        track_application_view()  # Define your track application logic here
    else:
        homepage_view()

# Run the app
if __name__ == "__main__":
    router()