import datetime
import logging
from azure.storage.blob import BlobServiceClient
from flask import jsonify
import os
# Retrieve the connection string (replace with your actual environment variable if necessary)
connection_string = os.getenv('STORAGE_CONNECTION_STRING')
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Check if the connection string is set
if not connection_string:
    logging.error("STORAGE_CONNECTION_STRING environment variable is not set.")
    raise ValueError("Please set the STORAGE_CONNECTION_STRING environment variable.")

def get_container_timestamp(container_name):
    # Extract timestamp from container name, assuming format 'source-YYYYMMDDHHMMSS'
    try:
        timestamp_str = container_name.split('-')[-1]
        return datetime.datetime.strptime(timestamp_str, '%Y%m%d%H%M%S')
    except ValueError:
        return None

def delete_old_containers():
    logging.info("Flask App to delete containers created over an hour ago")

    # Create BlobServiceClient using the connection string
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    
    # Get current time
    current_time = datetime.datetime.utcnow()
    logging.info(f"Current UTC Time: {current_time}")

    # List all containers in the storage account
    containers = blob_service_client.list_containers()

    deleted_containers = []

    for container in containers:
        container_name = container['name']

        # Get the timestamp from the container name
        container_timestamp = get_container_timestamp(container_name)

        if container_timestamp:
            # Check if the container is older than one hour
            time_difference = current_time - container_timestamp
            if time_difference.total_seconds() > 900:  # Older than 15 minutes
                try:
                    # Delete the container
                    blob_service_client.delete_container(container_name)
                    deleted_containers.append(container_name)
                    logging.info(f"Deleted container: {container_name}")
                except Exception as e:
                    logging.error(f"Failed to delete container {container_name}: {e}")
            else:
                logging.info(f"Container {container_name} is less than 1 hour old, skipping...")
        else:
            logging.info(f"Container {container_name} does not match the expected naming pattern.")

    return jsonify({"deleted_containers": deleted_containers}), 200
