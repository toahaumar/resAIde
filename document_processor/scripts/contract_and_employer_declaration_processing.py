#!/usr/bin/env python3
import os
import sys
import json
import base64
import re
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel
from dotenv import load_dotenv
from mistralai import Mistral, TextChunk, ImageURLChunk, DocumentURLChunk
from mistralai.models import OCRResponse

# Load environment variables from .env file
load_dotenv()

class StructuredOCRResponse(BaseModel):
    employee_name: str
    employee_address: str
    employee_salary_per_month_brutto: str
    employee_nationality: str
    employee_academic_degree: str
    employee_academic_degree_in_germany: bool
    employee_profession:str
    employment_start_date: str
    employment_duration: str
    employer_name: str
    employer_address: str
    employer_signature_present: bool
    
class StructuredOCRResponseforContract(BaseModel):
    employee_name: str
    employee_address: str
    employee_salary_per_month_brutto: str
    employee_profession:str
    employment_start_date: str
    employment_duration: str
    employer_name: str
    employer_address: str
    employer_signature_present: bool


def docstring_from_file(doc_file_path):
    """
    Decorator that reads a docstring from an external file and assigns it
    to the decorated function at runtime.
    """
    def decorator(func):
        try:
            with open(doc_file_path, 'r', encoding='utf-8') as f:
                func.__doc__ = f.read()
        except FileNotFoundError:
            func.__doc__ = "Error: Could not find the docstring file."
        return func
    return decorator


@docstring_from_file("read_txt_file_docstring.txt")
def read_txt_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        return f"Error: The file at {file_path} was not found."
    except IOError as e:
        return f"Error: An IOError occurred while reading the file at {file_path}. Details: {e}"


def encode_image(image_path):
    """Encode an image file to a base64 string."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        print(f"Error: The file {image_path} was not found.")
        return None
    except Exception as e:
        print(f"Error encoding image: {e}")
        return None


def replace_images_in_markdown(markdown_str: str, images_dict: dict) -> str:
    """
    Replace image placeholders in markdown with base64-encoded images.
    """
    for img_name, base64_str in images_dict.items():
        markdown_str = markdown_str.replace(
            f"![{img_name}]({img_name})",
            f"![{img_name}](data:image/jpeg;base64,{base64_str})"
        )
    return markdown_str


def get_combined_markdown(ocr_response: OCRResponse) -> str:
    """
    Combine OCR text and images into a single markdown document.
    """
    markdowns = []
    for page in ocr_response.pages:
        image_data = {}
        for img in page.images:
            image_data[img.id] = img.image_base64
        markdowns.append(replace_images_in_markdown(page.markdown, image_data))
    return "\n\n".join(markdowns)


def extract_employee_signature(markdown_str: str, signature_alt: str = "img-1.jpeg") -> str:
    """
    Extract the base64 image data corresponding to the employee signature from the markdown.
    
    Args:
        markdown_str: The complete markdown text.
        signature_alt: The expected alt text for the signature image.
    
    Returns:
        The base64 string of the employee signature image, or None if not found.
    """
    pattern = r"!\[(.*?)\]\((data:image\/jpeg;base64,.*?)\)"
    matches = re.findall(pattern, markdown_str)
    for alt_text, data_url in matches:
        if signature_alt in alt_text:
            return data_url.split("base64,")[-1]
    return None


def compare_signatures(signature_base64_markdown: str, signature_base64_ground: str, client, model):
    """
    Use the LLM to compare two candidate signature images.
    The prompt instructs the visa officer to check if the signature extracted
    from the markdown matches the ground-truth signature provided separately.
    
    Args:
        signature_base64_markdown: Base64 string of the signature extracted from the markdown.
        signature_base64_ground: Base64 string of the candidate's ground-truth signature.
        client: The Mistral client.
        model: The model to use for comparison (e.g., "pixtral-large-latest").
    
    Returns:
        A string response from the LLM detailing whether the signatures match.
    """
    if not signature_base64_markdown or not signature_base64_ground:
        return "Error: One or both signature images are missing."
    
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": (
                    "You are a visa officer reviewing candidate signatures. Compare the candidate signature extracted "
                    "from the contract markdown with the ground-truth signature provided separately. Determine whether "
                    "the two signatures match or if there are any discrepancies. Provide a concise summary of your findings."
                )},
                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{signature_base64_markdown}"},
                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{signature_base64_ground}"}
            ]
        }
    ]
    
    try:
        response = client.chat.complete(
            model=model,
            messages=messages,
            temperature=0.0,
            response_format={"type": "text"}
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error during signature comparison: {e}"


def check_employee_info(extracted_json: dict, ground_truth_name: str, ground_truth_address: str) -> str:
    """
    Compare the employee name and address extracted in the OCR JSON with the ground-truth values.
    
    Args:
        extracted_json: The OCR-extracted JSON which should include keys "employee_name" and "employee_address".
        ground_truth_name: The expected employee name.
        ground_truth_address: The expected employee address.
    
    Returns:
        A JSON string with two keys:
          - "employee_info_match": a boolean (true if both name and address match)
          - "explanation": a short explanation.
    """
    extracted_name = extracted_json.get("employee_name", "").strip()
    extracted_address = extracted_json.get("employee_address", "").strip()
    
    match_name = (extracted_name.lower() == ground_truth_name.lower())
    match_address = (extracted_address.lower() == ground_truth_address.lower())
    overall_match = match_name and match_address
    
    if overall_match:
        explanation = "Both employee name and address match the ground truth."
    else:
        explanation = ""
        if not match_name:
            explanation += f"Employee name mismatch: extracted '{extracted_name}', expected '{ground_truth_name}'. "
        if not match_address:
            explanation += f"Employee address mismatch: extracted '{extracted_address}', expected '{ground_truth_address}'."
    
    result = {
        "employee_info_match": overall_match,
        "explanation": explanation.strip()
    }
    return json.dumps(result)


def check_employment_start_date(employment_start_date_str: str, passport_expiry_date_str: str, submission_date_str: str) -> str:
    """
    Check whether the employment start date is after the application submission date 
    but before the passport expiry date.
    
    Dates should be in the format "dd.mm.yyyy".
    
    Returns:
        A JSON string with two keys:
          - "employment_start_date_valid": a boolean
          - "explanation": a short explanation.
    """
    try:
        employment_start = datetime.strptime(employment_start_date_str, "%d.%m.%Y")
        passport_expiry = datetime.strptime(passport_expiry_date_str, "%d.%m.%Y")
        submission_date = datetime.strptime(submission_date_str, "%d.%m.%Y")
    except Exception as e:
        return json.dumps({
            "employment_start_date_valid": False,
            "explanation": f"Error parsing dates: {e}"
        })
    
    if submission_date < employment_start < passport_expiry:
        result = {
            "employment_start_date_valid": True,
            "explanation": (
                f"Employment start date {employment_start_date_str} is after submission date "
                f"{submission_date_str} and before passport expiry date {passport_expiry_date_str}."
            )
        }
    else:
        result = {
            "employment_start_date_valid": False,
            "explanation": (
                f"Employment start date {employment_start_date_str} does not fall between the "
                f"submission date {submission_date_str} and passport expiry date {passport_expiry_date_str}."
            )
        }
    return json.dumps(result)


def classify_contract_status(employee_info_comparison, employment_date_comparison, signature_comparison, client, model):
    """
    Classify the contract status into one of three classes: green, yellow, or red.
    
    Criteria:
      - Green: All three comparisons yield positive matches (application can be approved).
      - Yellow: The signature comparison throws up negative results, while the other two comparisons are positive (follow-up with the applicant is needed).
      - Red: If either employee_info_comparison or employment_date_comparison is negative, it is a definite red.
             (Follow-up is mandatory, and rejection may be warranted.)
    
    Returns:
        A JSON object with two keys: "classification" and "summary".
    """
    prompt_text = (
        "Based on the following comparisons, classify the passport application into one of three classes: green, yellow, or red.\n\n"
        "Criteria:\n"
        "- Green: All three comparisons yield positive matches, so the contract status should be approved.\n"
        "- Yellow: The signature comparison throws up negative results, while the other two comparisons are positive; a follow-up with the applicant is needed.\n"
        "- Red: If either employee_info_comparison or employment_date_comparison is negative, it is a definite red; follow up is mandatory, and rejection may be warranted.\n\n"
        "Return your answer as a JSON object with only two keys: 'classification' and 'summary'. For example: {\"classification\": \"green\", \"summary\": \"All three analyses (employee information, employement_date and signatures) are positive.\"}\n\n"
        "employee_info_comparison:\n" + employee_info_comparison + "\n\n"
        "employment_date_comparison:\n" + employment_date_comparison + "\n\n"
        "signature_comparison:\n" + signature_comparison
    )
    
    messages = [
        {
            "role": "user",
            "content": [{"type": "text", "text": prompt_text}]
        }
    ]
    
    try:
        response = client.chat.complete(
            model=model,
            messages=messages,
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        json_output = response.choices[0].message.content
        return json.loads(json_output)
    except Exception as e:
        print(f"Error during classification: {e}")
        return None


def generate_markdown_from_ocr(client, file_under_processing, extract_model):
    """
    Uploads and processes the employment contract PDF using OCR and returns the combined markdown.
    
    Args:
        client: The Mistral client instance.
        employment_contract: A Path object representing the employment contract PDF.
        extract_model: The model to use for OCR extraction (e.g., "mistral-ocr-latest").
    
    Returns:
        str: The combined markdown generated from the OCR response.
    """
    try:
        uploaded_file = client.files.upload(
            file={
                "file_name": file_under_processing.stem,
                "content": file_under_processing.read_bytes(),
            },
            purpose="ocr",
        )
    except Exception as e:
        print(f"Error uploading file: {e}")
        sys.exit(1)

    signed_url = client.files.get_signed_url(file_id=uploaded_file.id, expiry=1)
    pdf_response = client.ocr.process(
        document=DocumentURLChunk(document_url=signed_url.url),
        model=extract_model,
        include_image_base64=True
    )
    # Process OCR response into combined markdown
    combined_markdown = get_combined_markdown(pdf_response)
    return combined_markdown

def analyze_declaration_accuracy(declaration_details, contract_details, client, model):
    """
    Combine the JSON and image comparisons to provide a final analysis.
    Returns the LLM's analysis as a concise response (maximum two sentences)
    that also recommends asking the applicant for clarifications if needed.
    """
    prompt_text = (
        "Based on the following details, highlight similarities and differences between employer contract details and declaration details for the fields present in the contract details. "
        "The final output must be a JSON, with similarities, differences, and classification as keys. The classification is green if all fields match perfectly, yellow if up to 20 percent of the fields don't match, and red otherwise. Please take care of any unicodes and abbreviations (such as Straße to Str.) in the descriptions and standardize the dates to DD.MM.YYYY format before comparing. Please do not include additional_fields_in_declaration for your analysis of classification category. Only output the JSON and Nothing else.\n\n"
        "Declaration Details:\n" + declaration_details + "\n\n"
        "Contract Details:\n" + contract_details
    )
    
    messages = [
        {
            "role": "user",
            "content": [{"type": "text", "text": prompt_text}]
        }
    ]
    
    try:
        response = client.chat.complete(
            model=model,
            messages=messages,
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        post_processed_response = json.loads(response.choices[0].message.content)

        return json.dumps(post_processed_response, indent=4)
    except Exception as e:
        return f"Error during analysis: {e}"

def analyze_blue_card_fit(declaration_details, blue_card_criteria, client, model):
    """
    Combine the JSON and image comparisons to provide a final analysis.
    Returns the LLM's analysis as a concise response (maximum two sentences)
    that also recommends asking the applicant for clarifications if needed.
    """
    prompt_text = (
        "Based on the employer declaration details and the blue card criteria, think step-by-step, and analyze the likelihood of the candidate successfully getting a blue card."
        "The final output must be a JSON, with explanation, and classification as keys. The classification is green if the candidate fits the criteria completely, yellow if some things need clarification, and red if a major condition is violated. Only output the JSON and Nothing else.\n\n"
        "Declaration Details:\n" + declaration_details + "\n\n"
        "Contract Details:\n" + blue_card_criteria
    )
    
    messages = [
        {
            "role": "user",
            "content": [{"type": "text", "text": prompt_text}]
        }
    ]
    
    try:
        response = client.chat.complete(
            model=model,
            messages=messages,
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        post_processed_response = json.loads(response.choices[0].message.content)

        return json.dumps(post_processed_response, indent=4)
    except Exception as e:
        return f"Error during analysis: {e}"

def main():
    # Candidate and document details
    candidate_name = 'Deepti Singhal'
    candidate_address = 'Theresienstr. 999, 80333 Munich, Bayern'
    passport_expiry_date = '12.06.2024'
    submission_date = '15.12.2022'
    blue_card_criteria_path = '/Users/q654642/Desktop/resAIde/resAIde/document-processing/prompts/blue_card_criteria.txt'
    blue_card_criteria = read_txt_file(blue_card_criteria_path)
    
    employment_contract_path = '/Users/q654642/Desktop/resAIde/resAIde/document-processing/deepti-singhal-documents/enhanced_employment_agreement.pdf'
    employment_contract = Path(employment_contract_path)
    candidate_signature_path = '/Users/q654642/Desktop/resAIde/resAIde/document-processing/deepti-singhal-documents/deepti-sign.png'
    
    # Initialize the Mistral client
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
    if not MISTRAL_API_KEY:
        print("Error: MISTRAL_API_KEY is not set in the .env file.")
        sys.exit(1)
    client = Mistral(api_key=MISTRAL_API_KEY)
    
    # Define models
    EXTRACT_MODEL = "mistral-ocr-latest"            # Used for JSON extraction
    FINAL_ANALYSIS_MODEL = "mistral-large-latest"     # Used for overall analysis and classification
    SIGNATURE_COMPARE_MODEL = "pixtral-large-latest"  # Used specifically for signature image comparison
    
    # Process the employment contract and get the combined markdown
    contract_markdown = generate_markdown_from_ocr(client, employment_contract, EXTRACT_MODEL)
    
    # Extract employee signature from the combined markdown
    extracted_signature_base64 = extract_employee_signature(contract_markdown, signature_alt="img-1.jpeg")
    if extracted_signature_base64:
        print("Employee signature extracted from markdown.")
    else:
        print("Employee signature image not found in the markdown.")
    
    # Read candidate's ground-truth signature from file
    candidate_signature_base64 = encode_image(candidate_signature_path)
    if candidate_signature_base64:
        print("Candidate's ground-truth signature loaded.")
    else:
        print("Failed to load candidate's ground-truth signature.")
    
    # Compare the extracted signature with the candidate's signature
    signature_comparison = compare_signatures(
        extracted_signature_base64,
        candidate_signature_base64,
        client,
        SIGNATURE_COMPARE_MODEL
    )
    print("Signature Comparison Result:")
    print(signature_comparison)
    
    # Extract structured JSON from OCR markdown using chat completion
    chat_response = client.chat.complete(
        model="pixtral-large-latest",
        messages=[
            {
                "role": "user",
                "content": [
                    TextChunk(
                        text=(
                            f"This is employment contract's OCR in markdown:\n\n{contract_markdown}\n.\n"
                            "Convert this into a sensible structured json response, with the keys 'employee_name', 'employee_address', 'employee_salary', 'employment_start_date', 'employee_signature_present' and 'employer_signature_present'. The date should be in the format DD.MM.YYYY "
                            "The output should be strictly be json with no extra commentary"
                        )
                    ),
                ],
            }
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )
    
    employer_declaration_structured_response = json.loads(chat_response.choices[0].message.content)
    print(json.dumps(employer_declaration_structured_response, indent=4))
    
    # Check employee info
    employee_info_comparison = check_employee_info(employer_declaration_structured_response, candidate_name, candidate_address)
    print("Employee Info Comparison Result:")
    print(employee_info_comparison)
    
    employment_start_date = employer_declaration_structured_response.get("employment_start_date", "").strip()
    
    # Check employment start date validity
    employment_date_comparison = check_employment_start_date(employment_start_date, passport_expiry_date, submission_date)
    print("Employment Start Date Comparison Result:")
    print(employment_date_comparison)
    
    # Classify contract status
    classification_result = classify_contract_status(
        employee_info_comparison,
        employment_date_comparison,
        signature_comparison,
        client,
        FINAL_ANALYSIS_MODEL
    )
    if classification_result:
        print("Classification Result:")
        print(classification_result.get("classification", "").strip())
        print("Summary:")
        print(classification_result.get("summary", "").strip())
    else:
        print("Classification failed.")

    # Read the Employer Declaration form
    employer_declaration_path = '/Users/q654642/Desktop/resAIde/resAIde/document-processing/deepti-singhal-documents/deepti-erklaerung-zum-beschaeftigungsverhaeltnis_ba047549-signed.pdf'
    employer_declaration = Path(employer_declaration_path)
    employer_declaration_markdown = generate_markdown_from_ocr(client, employer_declaration, EXTRACT_MODEL)

    # Extract detailed structured JSON from OCR markdown of the Employer Declaration form for Blue Card Fit
    chat_response = client.chat.parse(
        model="pixtral-large-latest",
        messages=[
            {
                "role": "user",
                "content": [
                    TextChunk(text=(
                        f"This is the employer declaration's OCR in markdown:\n{employer_declaration_markdown}\n.\n"
                        "Convert this into a structured JSON response "
                        "with the OCR contents in a sensible dictionnary."
                        )
                    )
                ]
            }
        ],
        response_format=StructuredOCRResponse,
        temperature=0
    )
    total_employer_declaration_structured_response = dict(chat_response.choices[0].message.parsed)

    #Extract partial structured JSON from OCR markdown of the Employer Declaration form for Contract comparison
    chat_response = client.chat.parse(
        model="pixtral-large-latest",
        messages=[
            {
                "role": "user",
                "content": [
                    TextChunk(text=(
                        f"This is the employer declaration's OCR in markdown:\n{employer_declaration_markdown}\n.\n"
                        "Convert this into a structured JSON response "
                        "with the OCR contents in a sensible dictionnary."
                        )
                    )
                ]
            }
        ],
        response_format=StructuredOCRResponseforContract,
        temperature=0
    )
    partial_employer_declaration_structured_response = dict(chat_response.choices[0].message.parsed)
    #print(employer_declaration_structured_response)

    # Extract structured JSON from OCR markdown of the Employment Contract
    chat_response = client.chat.parse(
        model="pixtral-large-latest",
        messages=[
            {
                "role": "user",
                "content": [
                    TextChunk(text=(
                        f"This is the employment contract's OCR in markdown:\n{contract_markdown}\n.\n"
                        "Convert this into a structured JSON response "
                        "with the OCR contents in a sensible dictionnary."
                        )
                    )
                ]
            }
        ],
        response_format=StructuredOCRResponseforContract,
        temperature=0
    )
    contract_structured_response = dict(chat_response.choices[0].message.parsed)
    #print(contract_structured_response)

    # Analyze the comparisons between the Employer Declaration and Employment Contract
    declaration_accuracy = analyze_declaration_accuracy(
        str(partial_employer_declaration_structured_response), str(contract_structured_response), client, FINAL_ANALYSIS_MODEL
    )
    print("Analysis Result:\n")
    print(declaration_accuracy)
    ## Analyze the comparisons between the Employer Declaration and Blue Card Criteria
    blue_card_fit = analyze_blue_card_fit(
        str(total_employer_declaration_structured_response), blue_card_criteria, client, FINAL_ANALYSIS_MODEL
    )
    print("Blue Card Fit Result:\n")
    print(blue_card_fit)

if __name__ == "__main__":
    main()
