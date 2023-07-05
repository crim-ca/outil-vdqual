"""
Script that contains the code related for all checks that need to be performed
to make sure video descriptions (VDs) comply with quality requirements
"""

from typing import Any, Dict, List
from configparser import ConfigParser


def check_length(docs: dict, max_length: int) -> dict:
    """
    Verifies the length of each sentence of a VD is less than a given threshold

    Args:
        docs: List of vds contained in a VD
        max_length: Max length threshold

    Returns:
        Dictionary containing the results of the check.
        Each key contins the id of the VD and a list of dictionaries. Each dictionary contains the ID of a sentence,
        its offset with respect to the start of the VD, the number of words it
        contains and whether it's longer than a given threshold
    """
    # Offset with respect to the start of the VD that is being processed
    results = {}
    for i, doc in enumerate(docs):
        offset = 0
        results_vd = []
        for j, sentence in enumerate(doc.sentences):
            results_vd.append(
                {
                    "id": j,
                    "offset": {"start": offset, "end": offset + len(sentence.text)},
                    "num_words": len(sentence.words),
                    "warning": int(len(sentence.words) > max_length),
                }
            )
            # Compute new offset
            offset += len(sentence.text) + 1

        results[i] = results_vd

    return results


def record_outputs(docs: list, results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Record the results of the checks performed on all VDs

    Args:
        docs: List of vds contained in a VD
        results: Dictionary Key " document" and List of results by VD
    """
    out_json = {"documents": []}
    for i, doc in enumerate(docs):

        # Record global information
        out_json_en_cours = {
            "id": i,
            "text": docs[i].text,
            "features": {}}

        # add the results of the checks(feature) performed on each vds
        for feature in results:
            # si cette vds a des erreurs
            if i in results[feature]:
                out_json_en_cours["features"][feature] = results[feature][i]

        out_json["documents"].append(out_json_en_cours)

    return out_json



def load_config(file_config: str) -> dict:
    """
    Chargement du fichier de config
    :param file_config: fichier de config
    :return: dic_param : dictionnaire de config
    """

    config = ConfigParser()
    config.read(file_config)
    dic_param = dict()

    dic_param['voc_cinema'] = str(config.get("input", "voc_cinema"))
    dic_param['voc_offensant'] = str(config.get("input", "voc_offensant"))
    dic_param['span_aste_model_path_en'] =  config.get("span_aste", "pre_trained_path_en")
    dic_param['span_aste_model_path_fr'] =config.get("span_aste", "pre_trained_path_fr")
    dic_param['lang_detection_pretrained_model'] = config.get("input", "lang_detection_pretrained_model")
    dic_param['lang_detection_max_num_chars'] = int(config.get("input", "lang_detection_max_num_chars"))


    return dic_param
