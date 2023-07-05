# -*- coding:Utf-8 -*-
"""
Flag non-third-person pronouns
"""



def detect_non_third_person(documents) -> dict:
    """
    Detects non-third-person pronouns in documents.
    For french, there are some mistakes made by Stanza, so we have to correct them.
     - "donne-moi" : lemmatization gives only 1 token ("donne-moi")
                    instead of 3 tokens ( donner, -, moi)
                    (fortunately "peux-tu" or "puis-je" have 3 tokens : this is correct )
     - "Tu" in this pattern : ["Tu peux" + infinitive verb]  is lemmatized as 2 tokens "de le" :
                            it occurs only in this pattern and at the beginning of a sentence.


    :param documents: list of documents
    :return dictionary containing detected non-third-person pronouns for each document (vd_lines).
    """

    outputs = {}

    for i_doc in range(len(documents)):

        document = documents[i_doc]
        list_alert = []

        for sentence in document.sentences:

            for i in range(len(sentence.words)):
                word = sentence.words[i]
                word_feats = word.feats if word.feats else ""

                not_third_person = False

                # Pas à la troisième personne
                if word.upos in {"PRON"} and (("Person=2" in word_feats) or ("Person=1" in word_feats)):
                    not_third_person = True
                elif word.upos in {"DET"} and (("Person[psor]=2" in word_feats) or ("Person[psor]=1" in word_feats)):
                    not_third_person = True
                elif "-moi" in sentence.text and word.lemma == "donne-moi":
                    not_third_person = True
                elif "Tu" in sentence.text and word.lemma == "de" and i == 0:
                    not_third_person = True

                elif word.parent.text == "du" and word.text.lower == "tu" and i == 0:
                    not_third_person = True

                if not_third_person:
                    list_alert.append(
                        {
                            "token": {
                                "text": word.parent.text,
                                "offset_start": word.parent.start_char,
                                "offset_end": word.parent.end_char,
                            }
                        }
                    )

        outputs[i_doc] = list_alert


    return outputs
