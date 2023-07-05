"""
Script that calls all feature functions to perform a comprehensive quality
check on video descriptions
"""
import os
import time
from typing import Any, Dict
from stanza import Document, Pipeline
from modules import check_length, record_outputs, load_config
from duplication import duplication
from find_voc import find_voc
from tense_notpresent import tense_notpresent
from person import person
import pandas as pd

from coref.coref import flag_coref_chains
import fasttext

import requests


def main(text: str, max_length: int, seuil_duplication: int,
         window_duplication: int, postag_repetition: list, lemmatizing: bool, strict_mode: bool,
         max_coref_length: int, with_emotion: bool, 
         voc_cinema_df:pd.DataFrame=None, voc_offensant_df:pd.DataFrame=None) -> Dict[str, Any]:

    """
    Performs all quality checks on a video description

    Args:
        text: Text corresponding to the VD
        max_length: Max length threshold. Required for the length feature
        seuil_duplication: duplication threshold. Required for the duplication feature
        window_duplication: Window size for the duplication feature
        postag_repetition : List of postags for which the repetition feature is required
        lemmatizing : Boolean indicating if lemmatization is required for check of lex_cinema
        strict_mode : for the tense_notpresent feature
        max_coref_length: Max number of elements in a coreference chain
        with_emotion: Boolean indicating if emotion detection is required

    Returns:
        A JSON document
    """
    start_time = time.time()
    
    # load config file, use local if exists
    if os.path.isfile(os.path.join(os.path.dirname(os.path.realpath(__file__)), "config_local.ini")):
        config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config_local.ini")
    else:
        config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.ini")

    # param_conf = load_config(os.path.join(os.path.dirname(os.path.realpath(__file__)), config_path), lang)
    param_conf = load_config(os.path.join(os.path.dirname(os.path.realpath(__file__)), config_path))
   
    # Detect language
    lang_detection_model = fasttext.load_model(param_conf["lang_detection_pretrained_model"])
    # FastText's response is in tuple form (language label, probability, data type)
    # Example: ([['__label__en']], [array([0.8957091], dtype=float32)])
    lang_preds = lang_detection_model.predict([text[:param_conf["lang_detection_max_num_chars"]].replace("\n", " ")])
    lang = lang_preds[0][0][0].replace("__label__", "").upper()
    
    # The text to process should be a single string made up of lines or be in TSV format
    # In TSV format we should have two columns: timestamps and their corresponding lines of text
    # Check the format of the text and remove timestamps if present
    clean_lines = []
    format_found = None
    lines = text.split("\n")
    for line in lines:
        if "\t" in line:
            if format_found is None:
                format_found = "TSV"
            elif format_found == "TXT":
                raise ValueError("The text is neither in TXT nor TSV format with 2 columns")
            columns = line.split("\t")
            if len(columns) != 2:
                raise ValueError("The text is in TSV format but it has more than 2 columns")
            clean_lines.append(columns[1].strip())
        else:
            if format_found is None:
                format_found = "TXT"
            elif format_found == "TSV":
                raise ValueError("The text is neither in TXT nor TSV format with 2 columns")
            clean_lines.append(line.strip())

    text = "\n".join(clean_lines)

    # Error handling
    if not text:
        raise ValueError("No input text was specified")
    if lang not in ("EN", "FR"):
        raise ValueError("Only the English and French languages are supported")

    # Setup Stanza processor https://stanfordnlp.github.io/stanza/pipeline.html
    # There is a tokenization, a lemmatisation, a pos-tagging, a syntactic parsing and
    # the last "mwt" is the multi-word tokenization (useful for French) applied to the text
    processor = Pipeline(lang, processors="tokenize,lemma,pos,depparse,mwt")

    # Obtain a list of annotated Stanza document objects
    # Each document corresponds to a line of the video description
    docs = processor([Document([], text=line) for line in lines])

    # Perform all quality checks
    output_length = check_length(docs, max_length)
    output_duplication = duplication.check_duplication(docs, seuil_duplication, window_duplication, postag_repetition)

    if type(voc_cinema_df) is type(None):
        output_cinema = find_voc.check_lexique(docs, processor, lang, lemmatizing, path_lex=param_conf['voc_cinema'])
    else :
        output_cinema = find_voc.check_lexique(docs, processor, lang, lemmatizing, voc_df=voc_cinema_df)

    if type(voc_offensant_df) is type(None):
        output_offensant = find_voc.check_lexique(docs, processor, lang, lemmatizing, path_lex=param_conf['voc_offensant'])
    else :
        output_offensant = find_voc.check_lexique(docs, processor, lang, lemmatizing, voc_df=voc_offensant_df)


    output_tense = tense_notpresent.detect_non_present_tense(docs, strict_mode)
    output_person = person.detect_non_third_person(docs)
    output_coref = flag_coref_chains(text, docs, lang, max_coref_length)
    output_emotion = {}

    # Initialise Span-ASTE model with pre-trained weights
    # Please refer to this link for more information on how to use pre-trained weights
    # https://github.com/chiayewken/Span-ASTE/blob/main/README.md#predict-using-model-weights
    # as the configuration of the model Span-Aste is not the same as coreferee there is need to have 2 envs,
    # one for coreferee and one for Span-ASTE
    # as the solution is not yet implemented this is an option to disable emotion detection
    if with_emotion:
        try:

            response = requests.post(url=os.environ['EMOTION_SERVICE'], json={'lines': lines, 'lang':lang})
            
            output_emotion = dict(response.json())
            output_emotion = {int(k): v for k,v in output_emotion.items()}

        except (FileNotFoundError, PermissionError) as error:
            print("Warning: Pre-trained Span-ASTE model not found in \"%s\" - %s"
                % (param_conf["span_aste_model_path"], error))


    results = {"length": output_length, "duplication": output_duplication, "cinema": output_cinema, "offensive": output_offensant,
               "tense_notpresent": output_tense, "person": output_person, "coref": output_coref,
               "emotions": output_emotion}

    # print(results)
    # Record the results, only if the feature is detected
    out_json = record_outputs(docs, results)
    # print(out_json)
    print("--- Processing time was: %s seconds" % (time.time() - start_time))
    
    return out_json
