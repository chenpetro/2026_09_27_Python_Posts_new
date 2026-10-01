from flask import Flask, jsonify
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@app.route('/status', methods=['GET']) 
def status():
    logging.info('Status route accessed')
    return jsonify({'status': 'running'}), 200

if __name__ == '__main__':
    app.run(debug=True)