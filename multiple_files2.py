from flask import Flask, request, jsonify
import requests
import time
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
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

# Supported languages for formality
formality_supported_languages = {"DE", "FR", "IT", "ES", "NL", "PL", "PT-BR", "PT-PT", "JA", "RU"}

# DEEPL_API_URL = 'https://api.deepl.com/v2/document'
# DEEPL_API_KEY = '82a64fae-73d4-4739-9935-bbf3cfc15010'  # Replace with your actual DeepL API key
# STORAGE_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=devaitranslationstorage;AccountKey=GtiG/Hm1kzpGy8aElsdqgBiApPvUgEg+8DbylzCUYV+f4ZCfsNFRCLLIsfrvPemzXqm5hnIw6VGA+AStpe8FWQ==;EndpointSuffix=core.windows.net"

DEEPL_API_URL = os.getenv('DEEPL_API_URL')
DEEPL_API_KEY = os.getenv('DEEPL_API_KEY')  # Replace with your actual DeepL API key
STORAGE_CONNECTION_STRING = os.getenv('STORAGE_CONNECTION_STRING')



# Initialize Azure Blob Service Client
blob_service_client = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)

@app.route('/multiple_files2', methods=['POST'])
def multiple_files2():
    try:
        # Retrieve form data
        files = request.files.getlist('file')
        source_lang = request.form.get('source_lang', 'auto')
        target_lang = request.form['target_lang']
        formality = request.form['formality']
        glossary_file = request.files.get('glossary_file')

        source_lang_code = language_mapping.get(source_lang, 'auto')
        target_lang_code = language_mapping.get(target_lang)

        if glossary_file:
            from create_glossary_deepl2 import upload_glossary
            response = upload_glossary(source_lang,target_lang,glossary_file)
            print('Response from Upload Glossary:',response)
            gl_data = response  # Parse the JSON string
            glossary_id = gl_data["glossary_id"]
        
        if not target_lang_code:
            return jsonify({"error": "Invalid target language"}), 400

        if target_lang_code not in formality_supported_languages and formality in ['more', 'less']:
            return jsonify({
                "error": f"Formality '{formality}' is not supported for the target language '{target_lang}'."
            }), 400

        # List to hold SAS URLs for all translated files
        sas_urls = []

        for file in files:
            # Prepare file and payload for the DeepL API request
            file_payload = {
                'file': (file.filename, file.stream, file.content_type),
                'target_lang': (None, target_lang_code),
                'source_lang': (None, source_lang_code if source_lang_code != 'auto' else None),
                'formality': (None, formality)
            }

            if glossary_file:
                file_payload['glossary_id'] = (None, glossary_id)

            headers = {
                'Authorization': f'DeepL-Auth-Key {DEEPL_API_KEY}'
            }

            # 1. Upload document for translation
            response = requests.post(DEEPL_API_URL, files=file_payload, headers=headers)

            if response.status_code != 200:
                return jsonify({"error": f"File upload failed for {file.filename}"}), response.status_code

            response_data = response.json()
            document_id = response_data['document_id']
            document_key = response_data['document_key']

            # 2. Check translation status (polling)
            check_status_url = f"{DEEPL_API_URL}/{document_id}"
            status_payload = {"document_key": document_key}

            max_retries = 20
            retry_count = 0
            status = 'translating'

            retry_count = 0
            retry_interval = 10  # Start with 10 seconds
    
            while status in ['translating', 'queued'] and retry_count < max_retries:
                time.sleep(retry_interval)
                status_response = requests.post(check_status_url, json=status_payload, headers=headers)
                status_data = status_response.json()
                status = status_data['status']
    
                if status == 'done':
                    break
                elif status == 'failed':
                    error_message = status_data.get('error', 'Unknown error occurred')
                    return jsonify({
                        "error": f"Translation failed for {file.filename}",
                        "status_details": status_data,
                        "error_message": error_message
                    }), 500
    
                # Exponential backoff: double the wait time after each retry
                retry_interval = min(retry_interval * 2, 300)  # Cap the wait time at 5 minutes
                retry_count += 1

            if status != 'done':
                return jsonify({
                    "error": f"Translation still in progress for {file.filename} after maximum retries.",
                    "status_details": status_data
                }), 500

            # 3. Download the translated document
            download_response = requests.post(f"{DEEPL_API_URL}/{document_id}/result", 
                                            json={"document_key": document_key}, 
                                            headers=headers)

            if download_response.status_code != 200:
                return jsonify({"error": f"Failed to download translated file for {file.filename}"}), download_response.status_code





            



    

            translated_blob_name = f"{file.filename.rsplit('.', 1)[0]}-{target_lang_code}.{file.filename.rsplit('.', 1)[-1]}"

            # Upload the translated document to Azure Blob Storage
            container_name = f"destination-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            blob_service_client.create_container(container_name)

            blob_client = blob_service_client.get_blob_client(container=container_name, blob=translated_blob_name)

            # Upload the translated content
            blob_client.upload_blob(download_response.content, overwrite=True)

            # Generate a SAS URL for the uploaded blob
            sas_token = generate_blob_sas(
                account_name=os.getenv('STORAGE_SERVICE_ACCOUNT_NAME'),  # Your storage account name
                account_key=os.getenv('STORAGE_SERVICE_KEY'),  # Your account key
                container_name=container_name,
                blob_name=translated_blob_name,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(hours=1)
            )

            sas_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_name}/{translated_blob_name}?{sas_token}"
            sas_urls.append({"file_name": translated_blob_name, "sas_url": sas_url})

        # Return the list of SAS URLs for all uploaded files
        return jsonify({"sas_urls": sas_urls})

    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True)
    
