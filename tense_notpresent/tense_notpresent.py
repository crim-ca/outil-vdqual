# -*- coding:Utf-8 -*-
"""
Flag all verbs found in the video description in a tense other than present indicative mood
Two moods possibles : regular and strict
Strict mode : flag on periphrastic verbs like "be going to + V" (future),
"venir de + V" (past), "aller + V" (future)
"""


def detect_non_present_tense(
        documents, strict_mode: bool
) -> dict:
    """
    Detects non-present tense words in documents.

    Parameters
    ----------
    documents : List[Document]
        List of documents to detect non-present tense words in.
    strict_mode : Boolean
        If True, adds flag on periphrastic verbs like "be going to + V", "venir de + V", "aller + V"

    Returns
    -------
    DetectorOutput
        Dict structures containing detected non-present tense words for each document (vd lines).
    """

    outputs = {}
    for i_doc in range(len(documents)):

        document = documents[i_doc]
        non_present_tense = []

        for j, sentence in enumerate(document.sentences):

            # Collecting verbal expressions in the sentence
            express_verb_sentence = create_verbal_expression(sentence)

            for i, expression in enumerate(express_verb_sentence):
                is_not_present = False
                # on fait une liste de pos et une liste de feats
                lemma = [word.lemma for word in expression]
                feats = [w.feats if w.feats else "" for w in expression]
                pos = [w.upos for w in expression]

                # First case : auxiliary verb at the beginning of the expression
                if pos[0] == "AUX":

                    # Tense is not present
                    if "Tense=Pres" not in feats[0]:

                        # This is not an infinitive
                        # (this condition should be here and not in the previous condition)
                        if "VerbForm=Inf" not in feats[0]:
                            is_not_present = True

                    # Tense is not in indicative mood
                    elif "Mood=Ind" not in feats[0]:
                        is_not_present = True

                    # Case like perfect tense (there is a verb after the auxiliary)
                    elif lemma[0] == "avoir" or lemma[0] == "have" and len(expression) > 1:
                        is_not_present = True

                    # Case :  "est allé" ou "is going"
                    elif (lemma[0] == "être" or lemma[0] == "be") and len(expression) > 1:
                        if lemma[1] == "aller":
                            is_not_present = True
                        # "is going" alone is ok
                        # "is going to + V" is flagged
                        elif len(expression) > 3:
                            if lemma[1] == "go" and lemma[2] == "to" and "VerbForm=Inf" in feats[3]:
                                is_not_present = True

                # Second case : verb at the beginning of the expression:
                elif pos[0] == "VERB":

                    # Tense is not present, not an infinitive,
                    # not a perfect tense used alone
                    # not a gerondive ( like " Watching the movie, Paul is sitting on the couch")
                    if "Tense=Pres" not in feats[0] and \
                            "VerbForm=Inf" not in feats[0] and \
                            "VerbForm=Part" not in feats[0] and \
                            "VerbForm=Ger" not in feats[0]:

                        # for the perfect tense used alone
                        # ex : He flicks it shut - SHUT = VERB should not be flagged
                        # distinctive sign is = Mood is absent
                        if "Mood" in feats[0]:
                            is_not_present = True

                    # Strict mode (periphrastic tense) :  "venir de"
                    elif lemma[0] == "venir" and len(expression) > 1 and strict_mode:
                        is_not_present = True

                    # Strict mode (periphrastic tense): "aller"
                    elif lemma[0] == "aller" and len(expression) > 1 and strict_mode:
                        is_not_present = True

                if is_not_present:

                    # Tokens of same verbal expression  are recorded with the same "ref_token"
                    for word in expression:
                        non_present_tense.append(
                            {
                                "token": {
                                    "text": word.parent.text,
                                    "offset_start": word.parent.start_char,
                                    "offset_end": word.parent.end_char,
                                    "ref_token": (j, i)  # number of verbal expression
                                }
                            }
                        )

                    outputs[i_doc] = non_present_tense

        # If the Vd received no alert, we record an empty list
        if i_doc not in outputs:
            outputs[i_doc] = []

    return outputs


def create_verbal_expression(sentence) -> list:
    """
    Creates a list of verbal expressions in a sentence.
    Concatenation of verbes or auxiliary + verbes with the same head
    Special case :
        - "venir de + V. inf " is one expression
        - "is going to + V. inf"  is one expression
        - "aller + V.inf"  is one expression
    :param sentence: Stanza Sentence
    :return: list of verbal expressions
    """

    express_verb_sentence = []
    for i in range(len(sentence.words)):
        word = sentence.words[i]

        # CASE 1 : VERBE is the beginning of the expression
        if word.upos == "VERB":
            verbal_expression = [word]

            # VENIR DE + V.inf
            if word.lemma == "venir" and sentence.words[i + 1].lemma == "de":
                verbal_expression.append(sentence.words[i + 1])

                tete_prep = i + 1
                search_span = sentence.words[i + 2:]
                for w in search_span:
                    if w.feats and "VerbForm=Inf" in w.feats and w.head == tete_prep:
                        verbal_expression.append(w)
                        break

            # ALLER + V.inf
            elif word.lemma == "aller":
                if sentence.words[i + 1].feats and "VerbForm=Inf" in sentence.words[i + 1].feats:
                    verbal_expression.append(sentence.words[i + 1])

            # Check :if there is a similar expression, we choose the longest one
            express_verb_sentence = keep_longest(verbal_expression,
                                                 express_verb_sentence)

        # CASE 2 : AUXILIAIRE is the beginning of the expression

        elif word.upos == "AUX":
            tete = word.head
            verbal_expression = [word]

            search_start = min(i + 1, len(sentence.words))
            search_span = sentence.words[search_start:]

            for j, w in enumerate(search_span):

                # If there is a preposition, we stop the search
                # if we do not : "être capable de manger" ---> "être manger"
                if w.upos == "ADP":
                    break

                # we concatenate all the verbs with the same head
                if w.feats and "VerbForm" in w.feats and w.head == tete:

                    # Special case : "is going to + verbe"
                    # the "to" is required only if there is a verb after it
                    if verbal_expression[-1].lemma == "go" and search_span[j - 1].lemma == "to":
                        verbal_expression.append(search_span[j - 1])

                    verbal_expression.append(w)

                # we concatenate also the head
                # (if/as the auxiliary is not the head of the expression)
                # ex : Paul is watching the movie : head is "watching" and not "is"
                elif w.feats and "VerbForm" in w.feats and w.id == tete:
                    verbal_expression.append(w)

            # Check :if there is a similar expression, we choose the longest one
            if len(verbal_expression) >= 1:
                express_verb_sentence = keep_longest(verbal_expression,
                                                     express_verb_sentence)

    # Special final check :
    # if there is two side by side expressions which share a same word, we fuse them
    # ex :  être aller / aller manger = être aller manger
    new_express_verb_sentence = fuse_side_by_side(express_verb_sentence)

    return new_express_verb_sentence


def fuse_side_by_side(express_verb_sentence: list) -> list:
    """
    In a list if there are two side by side expressions
    with a same shared word ( the end for one and the beginning for the next)
    we fuse them
    :param express_verb_sentence: liste des expressions verbales
    :return: liste des expressions verbales
    """

    new_express_verb_sentence = []

    # more than a verbal expression in the list
    if len(express_verb_sentence) > 1:
        new_express = []
        for express_ver in express_verb_sentence:

            # first occurrence of the expression
            if new_express == []:
                new_express = express_ver

            # for the next occurrences
            else:

                # if this is the same id of the last item in new_express
                if new_express[-1].id == express_ver[0].id:
                    # we jump the current word
                    express_ver.pop(0)

                    # and we concatenate the rest of the expression
                    for element in express_ver:
                        new_express.append(element)

                # else this is a new expression, we record the old one
                else:
                    new_express_verb_sentence.append(new_express)
                    new_express = [element for element in express_ver]

        # Add the last verbal expression
        new_express_verb_sentence.append(new_express)

    else:
        new_express_verb_sentence = express_verb_sentence

    return new_express_verb_sentence


def keep_longest(new_expression: list, express_verb_sentence: list) -> list:
    """
    Check if the expression is already in the list and choose the longest one
    :param new_expression:verbal expression to analyze (list of words)
    :param express_verb_sentence:list of verbal expressions
    :return:  express_verb_sentence : cleaned list of verbal expressions
    """

    flag = False
    if new_expression:

        if not express_verb_sentence:
            express_verb_sentence.append(new_expression)

        else:

            for expression in express_verb_sentence:
                expression_string = " ".join([w.text for w in expression])
                new_expression_string = " ".join([w.text for w in new_expression])

                # CASE 1:  new expression is the same as the recorded one
                # we do nothing (we keep the recorded one)
                if expression_string == new_expression_string:

                    # (same offset)
                    if expression[0].start_char == new_expression[0].start_char and \
                            expression[-1].end_char == new_expression[-1].end_char:
                        flag = True

                # CASE 2 : new expression is smaller than the recorded one
                # we do nothing (we keep the recorded one)
                elif new_expression_string in expression_string:
                    flag = True

                # CASE 3  : new expression is bigger
                # we remove the old one and we add the new one
                elif expression_string in new_expression_string:
                    express_verb_sentence.remove(expression)
                    express_verb_sentence.append(new_expression)
                    flag = True

            # CASE 4 : no recorded expression, this is an entirely new one
            # we add it to the list
            if not flag:
                express_verb_sentence.append(new_expression)

    return express_verb_sentence
