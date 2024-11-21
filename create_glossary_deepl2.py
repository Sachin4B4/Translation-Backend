from flask import Flask, request, jsonify
import requests
import csv
import io
from io import BytesIO
import os


app = Flask(__name__)

# Language mapping as provided
language_mapping = {
    "Arabic": "AR",
    "Bulgarian": "BG",
    "Czech": "CS",
    "Danish": "DA",
    "German": "DE",
    "Greek": "EL",
    "English": "EN",
    "English (British)": "EN-GB",
    "English (American)": "EN-US",
    "Spanish": "ES",
    "Estonian": "ET",
    "Finnish": "FI",
    "French": "FR",
    "Hungarian": "HU",
    "Indonesian": "ID",
    "Italian": "IT",
    "Japanese": "JA",
    "Korean": "KO",
    "Lithuanian": "LT",
    "Latvian": "LV",
    "Norwegian Bokmål": "NB",
    "Dutch": "NL",
    "Polish": "PL",
    "Portuguese": "PT",
    "Portuguese (Brazilian)": "PT-BR",
    "Portuguese (European)": "PT-PT",
    "Romanian": "RO",
    "Russian": "RU",
    "Slovak": "SK",
    "Slovenian": "SL",
    "Swedish": "SV",
    "Turkish": "TR",
    "Ukrainian": "UK",
    "Chinese": "ZH",
    "Chinese (Simplified)": "ZH-HANS",
    "Chinese (Traditional)": "ZH-HANT"
}


def create_glossary(source_lang, target_lang, file):
    # Hardcoded DeepL auth key and glossary name
    auth_key = os.getenv('DEEPL_API_KEY')
    glossary_name = "glossary"
    
    # Set the URL for DeepL API glossary creation
    url = os.getenv('DEEPL_API_GLOSSARY_URL')

    # Set up headers
    headers = {
        "Authorization": f"DeepL-Auth-Key {auth_key}",
        "Content-Type": "application/json",
        "User-Agent": "YourApp/1.2.3"
    }

    # Read and format entries from the uploaded file
    entries = ""
    file_extension = file.filename.split('.')[-1]
    
    file_contents = file.read()  # Read as bytes
    file_io = BytesIO(file_contents)
    
    # Read the file based on its extension
    if file_extension == "csv":
        reader = csv.reader(io.TextIOWrapper(file_io, encoding="utf-8"))
    elif file_extension == "tsv":
        reader = csv.reader(io.TextIOWrapper(file_io, encoding="utf-8"), delimiter='\t')
    else:
        return {"error": "Unsupported file format. Use CSV or TSV files."}

    # Process each row and create the TSV formatted string for DeepL
    for row in reader:
        if len(row) >= 2:
            # Ensure each entry is formatted correctly with a tab separator
            entries += f"{row[0]}\t{row[1]}\n"

    entries = entries.strip()  # Trim the last newline

    # Debugging: Inspect the entries
    print(f"Formatted entries (TSV): {entries}")

    # Define the glossary payload
    payload = {
        "name": glossary_name,
        "source_lang": source_lang,
        "target_lang": target_lang,
        "entries": entries,
        "entries_format": "tsv"  # Make sure the format is set as "tsv"
    }

    # Make the POST request to DeepL API
    response = requests.post(url, headers=headers, json=payload)

    # Return success or error based on the response
    if response.status_code == 201:
        return response.json()  # return the JSON data directly
    else:
        # Log the full response for debugging purposes
        response_data = response.json()
        print(f"Error response: {response_data}")
        return {"error": response_data, "status_code": response.status_code}



# @app.route('/upload_glossary', methods=['POST'])
def upload_glossary(source_lang,target_lang,file):

    source_lang_code = language_mapping.get(source_lang, 'auto')
    target_lang_code = language_mapping.get(target_lang)

    # Validate form data
    if not all([source_lang_code, target_lang_code, file]):
        return jsonify({"error": "Missing required parameters"}), 400

    # Call the create_glossary function
    result = create_glossary(source_lang_code, target_lang_code, file)
    return result

if __name__ == '__main__':
    app.run(debug=True)
