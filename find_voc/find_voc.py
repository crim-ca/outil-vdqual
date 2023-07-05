# -*- coding:Utf-8 -*-

import pandas as pd
from stanza import Document, Pipeline

from flashtext import KeywordProcessor
import numpy as np

"""
Check use of cinematographic vocabulary in a text.
thanks to a cinematographic lexicon
Lemmatization of the text to check and the word in the lexicon
"""


def load_lexicon(lang: str, path_lex_current: str=None, voc_current_df:pd.DataFrame=None) -> list:
    """
    Load the lexicon in a list
    :param lang: FR or EN
    :param path_lex_current: path of the lexicon
    :param voc_current_df: panda DataFrame of the lexicon
    :return: list of lexicon of the selected language
    """
    if type(voc_current_df) is type(None):
        lex_voc = pd.read_csv(path_lex_current, sep="\t").astype(str)
    else:
        lex_voc = voc_current_df.astype(str)

    # check the name of the columns if this a personal dictionary
    if lang == "FR" and "TERM_FR" not in lex_voc.columns:
        if "FR" not in lex_voc.columns:
            raise ValueError("The column FR or TERM_FR is not in the lexicon")
        else:
            lex_voc.rename(columns={"FR": "TERM_FR"}, inplace=True)

    elif lang == "EN" and "TERM_EN" not in lex_voc.columns:
        if "EN" not in lex_voc.columns:
            raise ValueError("The column EN or TERM_EN is not in the lexicon")
        else:
            lex_voc.rename(columns={"EN": "TERM_EN"}, inplace=True)



    if lang == "FR":
        lex = [word.lower() for word in lex_voc.TERM_FR.unique().tolist()]
    elif lang == "EN":
        lex = [word.lower() for word in lex_voc.TERM_EN.unique().tolist()]
    else:
        raise ValueError("Language of dictionnary not supported")

    return lex


def lemmatize_lexicon(processor, lexicon):
    """
    Lemmatize alexicon
    """
    documents = processor([Document([], text=line) for line in lexicon])
    return [" ".join(w.lemma for s in doc.sentences for w in s.words) for doc in documents]


def extract_keywords_lemmas(
        index: KeywordProcessor, doc: Document
) -> list:
    """
    Extracts keywords from a document, matching words lemmas instead of words.
    The returned offsets are relative to the document text.

    Important: the index must be built with the lemmas of the words/phrases.

    Parameters
    ----------
    doc : Document
        Document to extract keywords from.
    index : KeywordProcessor
        Index to use for keyword extraction.

    Returns
    -------
    List[Tuple[str, int, int]]
        List of (keyword, offset_start, offset_end) tuples.
    """

    if not doc.text or (len(doc.sentences) == 0):
        return []

    words = [w for sentence in doc.sentences for w in sentence.words]
    lemmas = [w.lemma for w in words]

    # Lemmatize document:
    lemma_text = " ".join(lemmas)

    # Compute lemma start and end offsets in the lemmatized document:
    lemma_start_offsets = np.cumsum(np.array([0] + [len(lemma) + 1 for lemma in lemmas[:-1]]))
    lemma_end_offsets = lemma_start_offsets + np.array([len(lemma) for lemma in lemmas])

    # Extract keywords in lemmatized text
    for _, start, end in index.extract_keywords(lemma_text, span_info=True):
        # Retrieve start and end lemmas indices
        i_start = np.searchsorted(lemma_start_offsets - 1, start) - 1
        i_end = np.searchsorted(lemma_end_offsets, end)

        # Retrieve text offset from lemmas:
        text_start_offset = words[i_start].start_char
        text_end_offset = words[i_end].end_char

        yield doc.text[text_start_offset:text_end_offset], text_start_offset, text_end_offset


def _detect_lexicon(docs: list, apply_matching_on_lemmatized_text: bool,
                    lexicons: KeywordProcessor) -> dict:
    """
    Detect occurrences of word and phrases in a list of documents (VD lines)
    :param docs: list of documents (stanza)
    :param apply_matching_on_lemmatized_text: apply matching on lemmatized lexicon (True)
    or not (False)
    :param lexicons: KeywordProcessor
    :return: dict of results by id of vd line
    """

    # For each document
    results = {}

    for i_vd, document in enumerate(docs):
        output = []
        if apply_matching_on_lemmatized_text:
            matches_dict = [
                extract_keywords_lemmas(lexicons, document)
            ]
        else:
            matches_dict = [
                lexicons.extract_keywords(document.text, span_info=True)
            ]

        for matches in matches_dict:
            for (text, offset_start, offset_end) in matches:
                # TODO : add postag on lexicon and check if pos-tag is adequate
                output.append(
                    {
                        "token": {
                            "text": text,
                            "offset_start": offset_start,
                            "offset_end": offset_end,
                        }
                    }
                )
        if output != [[]]:
            results[i_vd] = output

    return results


def check_lexique(docs: list, processor: Pipeline,
                  lang: str, apply_matching_on_lemmatized_text: bool,
                  path_lex: str = None, voc_df:pd.DataFrame=None) -> dict:
    """
    Find cinematographic vocabulary in a text
    using Lemmatization or optionally using the raw text
    :param docs: docs already processed by Stanza
    :param processor: Pipeline of Stanza
    :param lang: FR or EN are supported
    :param apply_matching_on_lemmatized_text:way to detect the lexicon:lemmatized text(True)
    :param path_lex: path to the lexicon
    :param voc_df: panda DataFrame of the lexicon
    or raw (False)
    :return:
    """

    # load the lexicon
    if type(voc_df) is type(None):
        lex_voc = load_lexicon(lang, path_lex_current=path_lex)
    else:
        lex_voc = load_lexicon(lang, voc_current_df=voc_df)
    

    # detect the lexicon in the text
    # option1 : use lemmatization of lexique and vds to detect find_voc
    if apply_matching_on_lemmatized_text:

        # lemmatization of lexicon
        lexicon_lemmatized = lemmatize_lexicon(processor, lex_voc)

        # initialisation of flashtext with lemmatized lexicon
        lexicons_lemmatized_tofind = KeywordProcessor()
        lexicons_lemmatized_tofind.add_keywords_from_list(lexicon_lemmatized)

        # detect occurrences of the lexicon in the vd text
        outputs = _detect_lexicon(docs, apply_matching_on_lemmatized_text=True,
                                  lexicons=lexicons_lemmatized_tofind)

    # option2 : use raw text
    # TODO : remove this option if finally not needed
    else:
        # initialize_flashtext_with raw lexicon and add it to the pipeline
        lexicons_tofind = KeywordProcessor()
        lexicons_tofind.add_keywords_from_list(lex_voc)

        # detect occurrences of the lexicon in the vd text
        outputs = _detect_lexicon(docs, apply_matching_on_lemmatized_text=False,
                                  lexicons=lexicons_tofind)

    return outputs
