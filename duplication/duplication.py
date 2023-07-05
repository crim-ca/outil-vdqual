# -*- coding:Utf-8 -*-
"""
Check duplication in all the VD
for a liste of specific pos-tag like ADJ, ADV, VERB
#TODO : faire une version qui prend tout, pour tester plus facilement.
"""

from collections import Counter

def build_dic_lemme(docs:list) -> dict:
    """
    Build a dictionary with key (id_count) and value (lemma)
    :param docs: list of VD
    :return: dictionary with key (id_count) and value (lemma)
    """
    dic_lemme = {}
    compteur = 0

    for doc in docs:
        for sentence in doc.sentences:
            for word in sentence.words:
                if word.lemma not in dic_lemme:
                    dic_lemme[word.lemma] = compteur
                    compteur += 1

    return dic_lemme


def check_duplication(docs: list, seuil_duplication: int, repetition_span: int, postag: list) -> dict:
    """
    Find all the repetitions in a VDS by searching in a window of lines
    and return the result for one line of VD
    :param docs: VDs
    :param seuil_duplication: minimum threshold of repetition
    :param repetition_span: number of lines to look before and after the line
    :param postag : list of postag to look for
    :return: dictionary with key (index of vd) and value (list of repetitions)
    """

    dic_repetitions = {}

    # Iterate over the VDs and find the repetitions in the window
    # As the window is bigger than one line,
    # we begin after the repetition span (same for the end, stop before)

    # cas où la fenêtre entière (repetition_span*2 +1 ( la ligne en cours de traitment)
    # est plus grande ou égale au nombre de lignes dans le VD : on prend tout
    if (2 * repetition_span + 1) >= len(docs):
        start = 0
        end = len(docs)
        all_lines = True

    # sinon on prend une fenêtre glissante
    else:
        start = repetition_span
        end = len(docs) - repetition_span
        all_lines = False

    for i in range(start, end):

        # Select the window of lines to analyze
        windows = docs[i - repetition_span:i + repetition_span + 1]

        # Count the number of repetitions for a lemma in the window
        repetitions_window = count_in_window(windows, postag)

        # find the duplication and record id_line where it's occur
        dic_repetitions_local = find_repetitions_in_window(repetitions_window, seuil_duplication,
                                                           windows, i,
                                                           repetition_span, postag, all_lines)

        # Record in the dictionary  of repetition for each line of VD
        # And use set to delete doublons
        for key, value in dic_repetitions_local.items():
            if key in dic_repetitions:
                for val in dic_repetitions_local[key]:
                    dic_repetitions[key].add(val)
            else:
                dic_repetitions[key] = set()
                for val in dic_repetitions_local[key]:
                    dic_repetitions[key].add(val)


    # Build the output by line of VD
    output_repetition = build_output_repetition(dic_repetitions, docs)

    return output_repetition


def count_in_window(vd_docs: list, postag: list) -> dict:
    """
    Count the number of repetition in a window of lines
    :param vd_docs: VDs
    :param postag: postag of repetition
    :return: counter_lemme : dict of lemmes and their number of repetition
    """

    counter_lemme = Counter(
        word.lemma
        # for item in look back_window
        for item in vd_docs
        for sentence in item.sentences
        for word in sentence.words
        if word.upos in postag
    )

    return counter_lemme


def find_repetitions_in_window(repetitions_windows: dict, seuil_duplication: int, vds: list,
                               index: int, repetition_span: int, postag: list, all_lines: bool) -> dict:
    """
    Find the repetitions in the windows of lines if their number of repetition is superior to
    the max_duplication
    (only for POS tag : ADJ, ADV, VERB)
    :param vds : list of vds in the window
    :param repetitions_windows: repetition in the window
    :param repetition_span : number of lines to look before and after the line
    :param seuil_duplication: minimum threshold of repetition (flag when it's reached
    :param index: line index of the window
    :param postag : list of postag to look for
    :param all_lines : boolean to know if the window is the whole VD
    :return: dict of repetitions (key : real index) - value : word in the line of vd
    (object "word" of stanza)
    """
    dict_repetitions_window = {}

    # Iterate over the lemmes of the counter if there is a repetition
    if repetitions_windows != {}:

        for i, vd in enumerate(vds):

            # real index of the line in the vds
            # dépend si on a pris toutes les lignes ou une fenêtre glissante
            if all_lines:
                true_index = index + i

            else:
                true_index = i + index - repetition_span
            dict_repetitions_window[true_index] = []

            for sentence in vd.sentences:
                for word in sentence.words:
                    if (word.upos in postag) and \
                            (repetitions_windows[word.lemma] >= seuil_duplication):
                        dict_repetitions_window[true_index].append(word)

    return dict_repetitions_window


def build_output_repetition(repetitions: dict, docs: list) -> dict:
    """
    Build the output by line of VD
    :param repetitions: list of repetitions in the line of vd (object "word" of stanza)
    :param docs: list of VDs (stanza)
    :return: output : list of repetitions in the line of vd with specific info by token
    """
    results = {}

    # récupération d'un id par lemme
    dic_lemme = build_dic_lemme(docs)


    if repetitions != {}:

        for i in range(len(docs)):
            output = []
            if i in repetitions:

                output.append(
                    [
                        {
                            "token": {
                                "text": word.parent.text,
                                "offset_start": word.parent.start_char,
                                "offset_end": word.parent.end_char,
                                "id_lemma": dic_lemme[word.lemma],
                            }
                        }
                        for word in repetitions[i]
                    ]
                )
                # cas où il y a une répétition dans la ligne et pas une liste vide à l'intérieur
                if output != [[]]:
                    results[i] = output
    else:
        results = {}

    return results
