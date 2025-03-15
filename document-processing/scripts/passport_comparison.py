import os
import sys
import json
import base64
from dotenv import load_dotenv
from mistralai import Mistral

# Load environment variables from .env file
load_dotenv()

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

def extract_passport_data(image_path, client, model, schema=None):
    """
    Run inference on a passport image to extract passport data as a JSON object.
    If a schema is provided, it is included in the prompt to enforce the JSON structure.
    """
    encoded_image = encode_image(image_path)
    if not encoded_image:
        return None

    prompt_text = (
        "You are a visa officer, fluent in multiple languages and familiar with passports from various countries. "
        "Extract the text from this passport image and output as a JSON object with a separate key for machine-readable text. "
        "Translate the text to English. This is a critical, high-security task; think carefully step by step before responding. "
        "If any values are unclear due to image quality, output 'unclear' for that value."
    )
    if schema is not None:
        prompt_text += f" Please ensure that the JSON follows exactly this schema: {schema}"

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt_text},
                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{encoded_image}"}
            ]
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
        print(f"Error during inference for image {image_path}: {e}")
        return None

def compare_passport_json(json1, json2):
    """
    Compare two passport JSON objects field by field.
    Returns a string summarizing and highlighting the differences.
    """
    if not json1 or not json2:
        return "One or both JSON outputs are missing."
    
    differences = {}
    all_keys = set(json1.keys()).union(set(json2.keys()))
    for key in all_keys:
        v1 = json1.get(key, "<missing>")
        v2 = json2.get(key, "<missing>")
        if v1 != v2:
            differences[key] = {"ground_truth": v1, "uploaded": v2}
    
    if not differences:
        return "The JSON outputs are identical."
    
    diff_str = "Differences found:\n"
    for key, diff in differences.items():
        diff_str += f"**{key}**:\n - Ground Truth: {diff['ground_truth']}\n - Uploaded: {diff['uploaded']}\n"
    return diff_str

def compare_images(image_path1, image_path2, client, model):
    """
    Use the LLM to compare two passport images.
    Returns the LLM's response as a string.
    """
    encoded_image1 = encode_image(image_path1)
    encoded_image2 = encode_image(image_path2)
    
    if not encoded_image1 or not encoded_image2:
        return "Error: Could not encode one or both images for comparison."
    
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": (
                    "You are a visa officer reviewing passport images. Compare the two provided passport images and highlight any "
                    "differences or inconsistencies between them."
                )},
                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{encoded_image1}"},
                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{encoded_image2}"}
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
        return f"Error during image comparison: {e}"

def analyze_comparisons(json_comparison, image_comparison, client, model):
    """
    Combine the JSON and image comparisons to provide a final analysis.
    Returns the LLM's analysis as a concise response (maximum two sentences)
    that also recommends asking the applicant for clarifications if needed.
    """
    prompt_text = (
        "Based on the following comparisons, provide a concise final analysis in no more than two sentences. "
        "If any details are unclear, recommend that the visa officer ask the applicant for further clarification.\n\n"
        "JSON Comparison:\n" + json_comparison + "\n\n"
        "Image Comparison:\n" + image_comparison
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
            response_format={"type": "text"}
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error during analysis: {e}"

def classify_application(json_comparison, image_comparison, client, model):
    """
    Classify the passport application into one of three classes: green, yellow, or red.
    
    Criteria:
      - Green: Both JSON and image comparisons indicate identical inputs (application can be approved).
      - Yellow: Minor discrepancies or unclear information are present (follow-up with the applicant is needed).
      - Red: Major discrepancies exist between the two JSON outputs and/or the uploaded image is extremely unclear 
             (follow-up is mandatory, and rejection may be warranted).
    
    Returns a JSON object with only one key "classification", for example:
      {"classification": "green"}
    """
    prompt_text = (
        "Based on the following comparisons, classify the passport application into one of three classes: green, yellow, or red.\n\n"
        "Criteria:\n"
        "- Green: Both JSON and image comparisons indicate identical inputs, so the application can be approved.\n"
        "- Yellow: Minor discrepancies or unclear information are present; a follow-up with the applicant is needed.\n"
        "- Red: Major discrepancies exist between the two JSON outputs and/or the uploaded image is extremely unclear; follow up is mandatory, and rejection may be warranted.\n\n"
        "Return your answer as a JSON object with only one key: 'classification'. For example: {\"classification\": \"green\"}\n\n"
        "JSON Comparison:\n" + json_comparison + "\n\n"
        "Image Comparison:\n" + image_comparison
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

def main():
    # Read passport image paths from environment variables
    uploaded_path = os.getenv("UPLOADED_PASSPORT_PATH")
    ground_truth_path = os.getenv("GROUND_TRUTH_PASSPORT_PATH")
    
    if not uploaded_path or not ground_truth_path:
        print("Error: UPLOADED_PASSPORT_PATH and/or GROUND_TRUTH_PASSPORT_PATH not set in .env file.")
        sys.exit(1)
    
    # Step 1: Extract passport data from the ground truth passport
    print("Extracting data from ground truth passport...")
    ground_truth_data = extract_passport_data(ground_truth_path, client, EXTRACT_MODEL)
    if not ground_truth_data:
        print("Error: Could not extract data from the ground truth passport image.")
        sys.exit(1)
    
    # Copy the JSON schema from the ground truth extraction
    schema = json.dumps(ground_truth_data, indent=2)
    
    # Step 2: Extract passport data from the uploaded passport using the ground truth schema
    print("Extracting data from uploaded passport using the ground truth schema...")
    uploaded_data = extract_passport_data(uploaded_path, client, EXTRACT_MODEL, schema=schema)
    if not uploaded_data:
        print("Error: Could not extract data from the uploaded passport image.")
        sys.exit(1)
    
    # Step 3: Compare the JSON outputs
    json_comparison = compare_passport_json(ground_truth_data, uploaded_data)
    print("JSON Comparison:")
    print(json_comparison)
    
    # Step 4: Compare the images via LLM using the 'pixtral-large-latest' model
    image_comparison = compare_images(ground_truth_path, uploaded_path, client, IMAGE_COMPARE_MODEL)
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

if __name__ == "__main__":
    main()
