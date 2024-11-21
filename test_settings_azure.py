# test_settings_azure.py

import requests
from flask import request, jsonify
from azure.storage.blob import BlobServiceClient

# Hardcoded source document URL, source language, and target language
SOURCE_DOCUMENT_URL = "https://devaitranslationstorage.blob.core.windows.net/source/Body%20is%20the%20temple.docx?sp=r&st=2024-10-10T13:21:05Z&se=2026-02-25T21:21:05Z&spr=https&sv=2022-11-02&sr=b&sig=TUldqtSd0ljLMMOzrMnrot0FzBI7r0uwz%2BnDKkpntRc%3D"
TARGET_DOCUMENT_URL = "https://devaitranslationstorage.blob.core.windows.net/translated/translated_doc_es.docx"
SOURCE_LANGUAGE_CODE = "en"  # English as source language
TARGET_LANGUAGE_CODE = "es"  # Spanish as target language

def test_translation():
    # Get the inputs from form-data or query parameters
    key = request.form.get('key')  # Azure Translator API key
    text_translation_endpoint = request.form.get('endpoint')  # Translator service endpoint URL
    region = request.form.get('region')  # Azure region

    # Hardcoded values for translation
    source_language_code = "en"  # English as source language
    target_language_code = "es"  # Spanish as target language
    text_to_translate = "This is a test"  # Text to translate

    # Check if key, endpoint, and region are provided
    if not key or not text_translation_endpoint or not region:
        return jsonify({"error": "API key, endpoint, and region are required."}), 400

    # Construct the Azure Translator API URL
    path = 'translate'
    constructed_url = f"{text_translation_endpoint}/{path}"

    # Setup the query parameters and headers
    params = {
        'api-version': '3.0',
        'from': source_language_code,
        'to': target_language_code
    }

    headers = {
        'Ocp-Apim-Subscription-Key': key,
        'Ocp-Apim-Subscription-Region': region,
        'Content-Type': 'application/json'
    }

    # Body of the request with the hardcoded text to be translated
    body = [{'text': text_to_translate}]

    try:
        # Make the request to the Azure Translator API
        response = requests.post(constructed_url, params=params, headers=headers, json=body)
        response.raise_for_status()  # Raises an HTTPError for bad responses

        # Parse the response JSON
        response_json = response.json()

        # Return the JSON response from the API
        return jsonify(response_json), 200

    except requests.exceptions.HTTPError as http_err:
        # Catch HTTP errors from the API call
        return jsonify({"error": f"HTTP error occurred: {http_err}"}), 500
    except Exception as e:
        # Catch any other errors
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

def translate_document():
    # Get key, endpoint, and region from request
    key = request.form.get('key')
    text_translation_endpoint = request.form.get('endpoint')
    region = request.form.get('region')

    # Validate key, endpoint, and region
    if not key or not text_translation_endpoint or not region:
        return jsonify({"error": "API key, endpoint, and region are required."}), 400

    # Construct the Azure Document Translation API URL
    constructed_url = f"{text_translation_endpoint}/translator/text/batch/v1.0/batches"

    # Setup the request body and headers with hardcoded URLs and languages
    body = {
        "inputs": [
            {
                "source": {
                    "sourceUrl": SOURCE_DOCUMENT_URL,
                    "language": SOURCE_LANGUAGE_CODE
                },
                "targets": [
                    {
                        "targetUrl": TARGET_DOCUMENT_URL,
                        "language": TARGET_LANGUAGE_CODE
                    }
                ]
            }
        ]
    }

    headers = {
        'Ocp-Apim-Subscription-Key': key,
        'Ocp-Apim-Subscription-Region': region,
        'Content-Type': 'application/json'
    }

    try:
        # Make the request to the Azure Document Translation API
        response = requests.post(constructed_url, headers=headers, json=body)

        # Log the status code and response text
        print("Status Code:", response.status_code)
        print("Response Text:", response.text)

        # Raise an error for bad responses
        response.raise_for_status()

        # If the request is successful, return success message
        return jsonify({"success": True, "message": "Document translation started successfully."}), 200

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return jsonify({"error": f"HTTP error occurred: {http_err}"}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

def validate_connection_string(connection_string):
    try:
        # Attempt to create BlobServiceClient with the provided connection string
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        # Try to list containers to validate the connection
        containers = blob_service_client.list_containers()
        for container in containers:
            pass  # Just to iterate and check if we can access containers
        return True
    except Exception as e:
        print(f"Connection string validation failed: {str(e)}")
        return False

def validate_connection_string_route():
    # Extract connection string from request
    connection_string = request.form.get('connection_string')

    # Ensure connection string is provided
    if not connection_string:
        return jsonify({"error": "Connection string is required."}), 400

    # Validate the connection string using the function
    if validate_connection_string(connection_string):
        return jsonify({"success": True, "message": "Valid Azure Blob Storage connection string."}), 200
    else:
        return jsonify({"error": "Invalid Azure Blob Storage connection string."}), 400

def run_all_operations():
    # Get the inputs from form-data
    key = request.form.get('key')  # Azure Translator API key
    text_translation_endpoint = request.form.get('text_translation_endpoint')  # Text translation service endpoint URL
    document_translation_endpoint = request.form.get('document_translation_endpoint')  # Document translation endpoint URL
    region = request.form.get('region')  # Azure region

    # Validate key, endpoints, and region
    if not key or not text_translation_endpoint or not document_translation_endpoint or not region:
        return jsonify({
            "error": "API key, text translation endpoint, document translation endpoint, and region are required."
        }), 400

    # Initialize results
    results = {}
    all_successful = True  # Flag to check if all operations are successful

    # Step 1: Test Text Translation
    try:
        source_language_code = "en"  # English as source language
        target_language_code = "es"  # Spanish as target language
        text_to_translate = "This is a test"

        # Construct the Azure Text Translator API URL
        constructed_url = f"{text_translation_endpoint}/translate"
        params = {'api-version': '3.0', 'from': source_language_code, 'to': target_language_code}
        headers = {
            'Ocp-Apim-Subscription-Key': key,
            'Ocp-Apim-Subscription-Region': region,
            'Content-Type': 'application/json'
        }
        body = [{'text': text_to_translate}]
        
        # Make the request to the Text Translation API
        translation_response = requests.post(constructed_url, params=params, headers=headers, json=body)
        translation_response.raise_for_status()  # Raise exception for bad status codes

        # Add text translation result to the results dictionary
        results['text_translation'] = translation_response.json()
    except Exception as e:
        results['text_translation'] = {"error": str(e)}
        all_successful = False  # Set flag to False if there was an error

    # Step 2: Test Document Translation
    try:
        # Construct the Azure Document Translation API URL
        document_translation_url = f"{document_translation_endpoint}/translator/text/batch/v1.0/batches"
        body = {
            "inputs": [
                {
                    "source": {"sourceUrl": SOURCE_DOCUMENT_URL, "language": SOURCE_LANGUAGE_CODE},
                    "targets": [{"targetUrl": TARGET_DOCUMENT_URL, "language": TARGET_LANGUAGE_CODE}]
                }
            ]
        }
        headers = {
            'Ocp-Apim-Subscription-Key': key,
            'Ocp-Apim-Subscription-Region': region,
            'Content-Type': 'application/json'
        }
        
        # Make the request to the Document Translation API
        document_response = requests.post(document_translation_url, headers=headers, json=body)
        document_response.raise_for_status()  # Raise exception for bad status codes

        # Add document translation result to the results dictionary
        results['document_translation'] = {"message": "Document translation started successfully."}
    except Exception as e:
        results['document_translation'] = {"error": str(e)}
        all_successful = False  # Set flag to False if there was an error

    # Determine the status code based on the success of operations
    if all_successful:
        return jsonify(results), 200
    else:
        return jsonify(results), 500  # Return 500 if any operation failed
