from wrapper import SpanModel
from flask import Flask, Response, request, jsonify
from flask_cors import CORS
from configparser import ConfigParser
import os
import argparse

app = Flask(__name__)
CORS(app)

config = ConfigParser()
config.read(os.getenv('EMOTION_CONFIG'))


@app.route('/predict', methods = ['POST'])
def predict():
    print(request.json)

    data = request.json
    lines = data['lines']
    lang = str(data['lang']).upper()
    model_path = config['model'][lang]
    model = SpanModel(save_dir=model_path, random_seed=0)
    output_emotion = model.predict(lines)

    print(output_emotion)
    response = jsonify(output_emotion)

    return response


@app.route('/status', methods = ['GET', 'POST'])
def status():
    status_check = jsonify({
        'service' : "vdqual_emotions",
        'status_check': "OK"
        })
    return (status_check)


if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=5007)
    

    
