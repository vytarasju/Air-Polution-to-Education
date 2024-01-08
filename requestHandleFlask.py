from flask import Flask, jsonify, request
from flask_cors import CORS
import happybase
import logging

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

connection_pool = happybase.ConnectionPool(size=10, host='localhost')

@app.route('/get_hbase_data')
def get_hbase_data():
    try:
        # Get the country code from the query parameter
        country_code = request.args.get('country', default=None)

        if country_code is None:
            return jsonify({'success': False, 'error': 'Country code is required'}), 400

        # Construct the row key using the country code
        row_key = country_code.upper()

        # Retrieve a connection from the pool
        with connection_pool.connection() as connection:
            table = connection.table('AQ')
            column_family = "data"
            qualifier = "value"

            # Retrieve the row from HBase
            row = table.row(row_key)

            print("Row for {}: {}".format(row_key, row))
            # Check if the specified column is present in the row
            column_check = f'{column_family}:{qualifier}'.encode('utf-8')
            if column_check in row:
                value = row[column_check].decode('utf-8')  # Decode byte string to regular string
                logger.debug("Value found: %s", value)
                return jsonify({'success': True, 'value': value})
            else:
                logger.debug(f"Column '{column_family}:{qualifier}' not found for row '{row_key}'.")
                return jsonify({'success': True, 'value': None})

    except Exception as e:
        logger.error("Error: %s", e)
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
