from flask import request, jsonify
import psycopg2
import os

def get_db_connection():
    """Establish a database connection using environment variables."""
    host = os.getenv('DB_HOST')
    database = os.getenv('DB_NAME')
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    port_str = os.getenv('DB_PORT')

    # Convert port to integer
    try:
        port = int(port_str)
    except (ValueError, TypeError) as e:
        raise Exception("Invalid port number.") from e

    # Connect to PostgreSQL
    return psycopg2.connect(
        host=host,
        database=database,
        user=user,
        password=password,
        port=port
    )

def get_settings_deepl():
    # Check if 'admin_id' is provided in the query parameters
    admin_id = request.args.get('admin_id')
    if not admin_id:
        return jsonify({"error": "Missing admin_id"}), 400

    # Connect to the database
    conn = get_db_connection()
    if not conn:  
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor()

        # SQL query to retrieve the api_key for the provided admin_id
        query = """
        SELECT api_key FROM deepl_settings WHERE admin_id = %s;
        """

        cursor.execute(query, (admin_id,))
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if result:
            # Return the api_key if found
            return jsonify({"admin_id": admin_id, "api_key": result[0]}), 200
        else:
            # Return a message if no settings were found for the given admin_id
            return jsonify({"error": f"No settings found for admin_id {admin_id}"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500
