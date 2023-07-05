from flask import Flask, request, jsonify
from flask_cors import CORS
from run import main
import pandas as pd 
import io  

app = Flask(__name__)
CORS(app)

@app.route('/predict', methods = ['GET', 'POST'])
def predict():

    try :
        data = request.json

        text                = data['text'] 
        max_coref_length    = int(data['maxCorefLength'])
        max_length          = int(data['maxLength'])
        seuil_duplication   = int(data['seuilDuplication'])
        strict_mode         = True if data['temps'] == "strict" else False
        window_duplication  = int(data["windowDuplication"])
        postag_repetition   = data['postTagRepetition']
        voc_cinema_df       = None if not str(data['vocCinema']) else pd.read_csv(io.StringIO(data['vocCinema']), sep="\t")
        voc_offensant_df    = None if not str(data['vocOffensant']) else pd.read_csv(io.StringIO(data['vocOffensant']), sep="\t")
        with_emotion        = True
    except: 
        print("ERROR")
    
    print("Text", text, type(text))
    print("max_length", max_length, type(max_length))
    print("seuil_duplication", seuil_duplication, type(seuil_duplication))
    print("strict_mode", strict_mode, type(strict_mode))
    print("window_duplication", window_duplication, type(window_duplication))
    print("postag_repetition", postag_repetition, type(postag_repetition))
    print("max_coref_length", max_coref_length, type(max_coref_length))
    print("with_emotion", with_emotion, type(with_emotion))
    print("voc_cinema_df", voc_cinema_df, type(voc_cinema_df))
    print("voc_offensant_df", voc_offensant_df, type(voc_offensant_df))

    output =  main(
                text                = text,
                max_length          = max_length,
                seuil_duplication   = seuil_duplication,
                window_duplication  = window_duplication,
                postag_repetition   = postag_repetition, 
                lemmatizing         = True, 
                strict_mode         = strict_mode,
                max_coref_length    = max_coref_length,
                with_emotion        = with_emotion,
                voc_cinema_df       = voc_cinema_df,
                voc_offensant_df    = voc_offensant_df
            )


    print(output)

    response = jsonify(output)
            
    return (response)



@app.route('/status', methods = ['GET', 'POST'])
def status():
    status_check = jsonify({
        'service' : "vdqual_outil",
        'status_check': "OK"
        })
    return (status_check)


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5008)
    

    
