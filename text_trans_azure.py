from flask import Flask, request, jsonify
import logging
import requests
import json
from urllib.parse import urlencode
import uuid
import psycopg2
import os

app = Flask(__name__)

# Database connection details
host = os.getenv('DB_HOST')
database = os.getenv('DB_NAME')
user = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
port = os.getenv('DB_PORT')

# Function to get supported languages from Azure Translator API
def get_supported_languages(endpoint, api_key):
    try:
        url = f"{endpoint.rstrip('/')}/languages?api-version=3.0"
        headers = {
            'Ocp-Apim-Subscription-Key': api_key,
            'Content-Type': 'application/json'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to retrieve supported languages: {str(e)}")
        raise e

# Function to convert language name to language code
def get_language_code(language_name, supported_languages):
    if supported_languages['translation'] is not None:
        for key, value in supported_languages['translation'].items():
            if value['name'].lower() == language_name.lower() or value['nativeName'].lower() == language_name.lower():
                return key
    return None  # Return None if the language is not supported

def fetch_settings(admin_id):
    try:
        # Establish connection to PostgreSQL
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port,
            sslmode='require'  # Ensure secure connection with Cosmos DB for PostgreSQL
        )

        # Create a cursor object to interact with the database
        cursor = conn.cursor()

        # SQL query to fetch settings for the given admin_id
        query = """
        SELECT key, text_translation_endpoint, region 
        FROM settings
        WHERE admin_id = %s;
        """
        cursor.execute(query, (admin_id,))
        result = cursor.fetchone()

        # Close the cursor and connection
        cursor.close()
        conn.close()

        return result  # Return the result directly

    except Exception as e:
        logging.error(f"Database error occurred: {e}", exc_info=True)
        return None  # Return None in case of an exception

@app.route('/text_trans_azure', methods=['POST'])
def text_trans_azure():
    logging.info('Processing translation request.')

    # Hardcoded Admin ID
    admin_id = '1'

    # Fetch settings from the database
    result = fetch_settings(admin_id)

    if result is None or len(result) < 3:
        logging.error("Failed to retrieve all required settings (key, text_translation_endpoint, region).")
        return jsonify({"error": "Failed to retrieve all required settings (key, text_translation_endpoint, region)."}), 500

    # Unpack the settings
    key, text_translation_endpoint, region = result

    # Extract target language, source language, and text from the request
    data = request.get_json()
    target_language_name = data.get('target_language')
    source_language_name = data.get('source_language')  # Optional source language
    text_to_translate = data.get('text')

    # Ensure target_language is provided
    if target_language_name and text_to_translate:
        # Get supported languages
        supported_languages = get_supported_languages(text_translation_endpoint, key)

        # Convert target language name to language code
        target_language_code = get_language_code(target_language_name, supported_languages)
        if not target_language_code:
            return jsonify({"error": f"Target language '{target_language_name}' is not supported."}), 400

        # Convert source language name to language code, if provided
        source_language_code = None
        if source_language_name:
            source_language_code = get_language_code(source_language_name, supported_languages)
            if not source_language_code:
                return jsonify({"error": f"Source language '{source_language_name}' is not supported."}), 400

        # Azure Translator API configuration
        path = '/translate'
        constructed_url = f"{text_translation_endpoint.rstrip('/')}{path}"

        params = {
            'api-version': '3.0',
            'to': [target_language_code]  # Use the converted language code
        }

        # If source_language_code is provided, add it to the params
        if source_language_code:
            params['from'] = source_language_code

        headers = {
            'Ocp-Apim-Subscription-Key': key,
            'Ocp-Apim-Subscription-Region': region,  # Correct region
            'Content-type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4())
        }

        body = [{'text': text_to_translate}]

        try:
            # Make the request to the Azure Translator API
            response = requests.post(constructed_url, params=params, headers=headers, json=body)
            response.raise_for_status()  # Raise an error for HTTP error responses
            response_json = response.json()

            # Return the response in JSON format
            return jsonify(response_json), 200

        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error occurred: {http_err}", exc_info=True)
            return jsonify({"error": f"HTTP error occurred: {http_err}"}), 500
        except requests.exceptions.RequestException as req_err:
            logging.error(f"Request error occurred: {req_err}", exc_info=True)
            return jsonify({"error": f"Request error occurred: {req_err}"}), 500
    else:
        return jsonify({"error": "Please pass target_language and text in the request."}), 400

if __name__ == '__main__':
    app.run(debug=True)
