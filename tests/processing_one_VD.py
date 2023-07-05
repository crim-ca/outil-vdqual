"""
Script wich load vd file and parameters
and call the main script
"""
import os
from configparser import ConfigParser
from tests import check_config
from run import main

import json


def load_config(file_config: str) -> dict:
    """
    Chargement du fichier de config
    :param file_config: fichier de config
    :return: dic_param : dictionnaire de config
    """

    config = ConfigParser()
    config.read(file_config)
    dic_param = dict()

    dic_param["vd"] = str(config.get("input", "vd"))
    dic_param["max_length"] = int(config.get("input", "length"))
    dic_param["seuil_duplication"] = int(config.get("input", "seuil_duplication"))
    dic_param["window_duplication"] = int(config.get("input", "window_duplication"))
    dic_param['output_file'] = str(config.get("output", "output_file"))
    dic_param['postag_duplication'] = str(config.get("input", "postag_duplication"))
    dic_param['lemmatized_cinema'] = str(config.get("input", "lemmatized_cinema"))
    dic_param['strict_mode_tense'] = bool(config.getboolean("input", "strict_mode_tense"))
    dic_param['max_coref_length'] = int(config.get("input", "max_coref_length"))
    dic_param['with_emotion'] = bool(config.getboolean("input", "with_emotion"))

    return dic_param


if __name__ == '__main__':

    # load config file
    if os.path.isfile(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   "config_test_unitaire_local.ini")):
        config_path_test = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                        "config_test_unitaire_local.ini")
    else:
        config_path_test = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config_test_unitaire.ini")

    param = load_config(os.path.join(os.path.dirname(os.path.realpath(__file__)), config_path_test))

    # transformation du texte en string
    text = open(param['vd']).read()

    # récupération des paramètres
    # (text: str, max_length: int, seuil_duplication: int,
    # window_duplication: int, postag_repetition: list, lemmatizing: bool, strict_mode: bool,
    # max_coref_length: int, with_emotion: bool)

    out_json = main(text, param['max_length'],
                    param['seuil_duplication'], param['window_duplication'],
                    param['postag_duplication'], param['lemmatized_cinema'], param['strict_mode_tense'],
                    param['max_coref_length'], param['with_emotion'])

    # Print du fichier de sortie
    with open(param['output_file'], "w", encoding="utf-8") as output_json:
        json.dump(out_json, output_json)