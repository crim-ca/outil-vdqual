"""
Find coreference chains found in a video description that are longer than a certain threshold.
"""

import coreferee
import spacy


def split_chains(doc: spacy.tokens.doc.Doc, coref_chains: dict) -> dict:
    """
    Split a coreference chain whenever the first term of the chain appears in it
    :param doc: 
    :return: Dictionary of coreference chains
    """
    cpt_chain = -1
    output_chain = {}
    for _, chain in coref_chains.items():
        cpt_chain += 1
        # on met la première mention dans la nouvelle chaine
        output_chain[cpt_chain] = [chain[0]]
        # peut-être une liste (mention complexe) ou une string (mention simple) :
        first_token = chain[0][0]

        # cas simple un seul mot
        if isinstance(first_token, str):
            # on parcourt les mentions après la première mention
            for i in range(1, len(chain)):
                mention = chain[i]
                token = mention[0]
                if token.lower() == first_token.lower():
                    # reinitialization de la chaine : we have to cut the chain here
                    cpt_chain += 1
                    output_chain[cpt_chain] = []
                    output_chain[cpt_chain].append(mention)
                else :
                    # on réécrit la chaine telle quelle
                    output_chain[cpt_chain].append(mention)

        # cas complexe plusieurs mots
        else:
            # on extrait les tokens de chaque liste de la mention
            first_list_tok_mention = [tok[0].lower() for tok in chain[0]]
            # on parcourt les mentions après la première mention
            for j in range(1, len(chain)):
                mention = chain[j]
                # si c'est pas la même chose donc on continue de reconstruire la même chaine
                if isinstance(mention, tuple):
                    output_chain[cpt_chain].append(chain[j])
                # si c'est une list
                # grande chance que ce soit la même que le premier token mais on vérifie quand même
                else :
                    # cas qui n'arrive pas dans les fichiers de test
                    list_tok_mention = [tok[0].lower() for tok in mention]

                    if list_tok_mention == first_list_tok_mention:
                        # reinitialization de la chaine
                        cpt_chain += 1
                        output_chain[cpt_chain] = []
                        output_chain[cpt_chain].append(chain[j])
                    else:
                        # on réécrit la chaine telle quelle
                        output_chain[cpt_chain].append(chain[j])

    # finalement, on enlève tous les singletons que nous ne traitons pas
    output_chain2 = {i: output_chain[i] for i in output_chain if len(output_chain[i]) > 1}

    # et on ré-indexe le dictionnaire dans l'ordre avec une clé qui s'incrémente
    output_chain3 = {}
    cpt = 0
    for i, chain in output_chain2.items():
        output_chain3[cpt] = chain
        cpt +=1

    return output_chain3


def add_global_offset(doc: spacy.tokens.doc.Doc, coref_chains: coreferee.data_model.ChainHolder) -> dict:
    """
    Tokens in coreference chains as returned by coreferee are assigned token indices
    But we're also interested in the global offset of these tokens with respect to the full text of a VD
    Here we will add global offsets to coreference chains
    :param doc: List of lines of a VD as returned by spacy
    :param coref_chains: Coreference chains as returned by coreferee
    :return: Dictionary of coreference chains with token indices and global offsets
    """
    cpt_chain = 0
    output_chain = {}
    for chain in coref_chains:
        output_chain[cpt_chain] = []
        # Return start and end span indices instead of token indices 
        for mention in chain:
            if len(mention) > 1:
                subchain = []
                for sub in mention:
                    # Warning = 0
                    subchain.append((doc[sub].text, doc[sub].idx, doc[sub].idx + len(doc[sub])))
                output_chain[cpt_chain].append(subchain)
            else:
                # Warning = 0
                output_chain[cpt_chain].append((doc[mention.root_index].text, 
                    doc[mention.root_index].idx, doc[mention.root_index].idx + len(doc[mention.root_index])))
        cpt_chain += 1

    return output_chain


def flag_coref_chains(text: str, docs, lang: str, max_length: int):
    """
    Flag all elements in coreference chains that go over a certain threshold
    :param text: Text of the videodescription
    :param lang: Language
    :param max_length: Threshold
    :return: JSON document
    """

    # Setup coreferee + spacy
    if lang == "EN":
        coref_model = spacy.load('en_core_web_trf')
    else:
        coref_model = spacy.load('fr_core_news_lg')
    coref_model.add_pipe('coreferee')



    # Retrieve coreference chains
    doc = coref_model(text)
    coref_chains_token_indices = doc._.coref_chains
    coref_chains_global_offset = add_global_offset(doc, coref_chains_token_indices)

    # Split coreference chains if needed
    split_coref_chains = split_chains(doc, coref_chains_global_offset)

    # List of chain elements
    # Each element will be stored as a list of: id_chain, text, begin offset, end offset, warning code
    # this is the offset for the whole VD
    flagged_coref_elems = []
    for key, chain in split_coref_chains.items():
        for idx, elem in enumerate(chain):
            # Simple elements
            # Example: ('Peter', 9, 41, 46)            
            if isinstance(elem, tuple):
                flagged_coref_elems.append(
                    [key, elem[0], elem[1], elem[2], 1 if idx + 1 > max_length else 0]
                )
            # Compound elements
            # Example: [('she', 69, 71), ('husband', 80, 84)] 
            else:
                for sub_elem in elem:
                    flagged_coref_elems.append(
                        [key, sub_elem[0], sub_elem[1], sub_elem[2], 1 if idx + 1 > max_length else 0]
                    )

    # Sort chain elems by begin offset
    flagged_coref_elems = sorted(flagged_coref_elems, key=lambda x: x[2] )

    # List of sentence offsets as returned by stanza
    last_offset_sentence = 0
    dict_sent_offset = {}

    # find the offset of sentences
    for j, doc in enumerate(docs):
        dict_sent_offset[j] = []

        for i, sent in enumerate(doc.sentences):
            sent_beg_idx = sent.tokens[0].start_char
            sent_end_idx = sent.tokens[-1].end_char

            if j == 0:
                # Each doc begin with 0 so for the first doc the offset are already correct
                dict_sent_offset[j].append([sent_beg_idx, sent_end_idx])
                last_offset_sentence = sent_end_idx + 1

            else:
                # Each doc begin with 0 so we have to calculate the real offset of the VD
                if i == 0:
                    dict_sent_offset[j].append(
                        [sent_beg_idx + last_offset_sentence, sent_end_idx + last_offset_sentence])
                    last_offset_sentence = sent_end_idx + last_offset_sentence + 1

                else:
                    # for the other sentences we just have to add the offset of the previous sentence
                    dict_sent_offset[j].append([last_offset_sentence, sent_end_idx + last_offset_sentence])
                    last_offset_sentence = sent_end_idx + last_offset_sentence + 1

    # create an aligne dictionary of offset stanza "relative" (official stanza) and "absolute" (offset like in spacy)
    dic_offset = dict()
    last_offset = 0
    last_char_rel = 0
    for j, one_doc in enumerate(docs):
        dic_offset[j] = dict()
        for i, sent in enumerate(one_doc.sentences):
            dic_offset[j][i] = []
            for k, token in enumerate(sent.tokens):

                # on va inscrire l'offset absolu dans le dictionnaire'
                if j == 0:  # first doc
                    begin = token.start_char
                    end = token.end_char
                else:
                    if i == 0:

                        if k == 0:
                            # suite de combien on saute de token
                            saut = 1

                            begin = last_offset + saut + token.start_char
                            end = begin + (token.end_char - token.start_char)
                            # last_offset = end + 1
                        else:
                            # on saute de combien de token
                            saut = token.start_char - last_char_rel

                            # begin = last_offset
                            # end = token.end_char + last_offset
                            begin = last_offset + saut
                            end = begin + (token.end_char - token.start_char)

                    else:
                        if k == 0:
                            # suite de combien on saute de token
                            saut = 1
                        else:
                            saut = token.start_char - last_char_rel

                        begin = last_offset + saut
                        # end = token.end_char + last_offset
                        end = begin + (token.end_char - token.start_char)
                # pour savoir de combien on saute
                last_char_rel = token.end_char
                last_offset = end
                dic_offset[j][i].append(
                    {"relative": (token.start_char, token.end_char), "absolute": (begin, end), "text": token.text})

    # creation d'un dic pour chaque id
    main_output = dict()
    for j, doc in dic_offset.items():
        main_output[j] = []

    for elem in flagged_coref_elems:
        for j, doc in dic_offset.items():
            for i, sent in doc.items():
                for k, token in enumerate(sent):
                    if elem[2] == token["absolute"][0] and elem[3] == token["absolute"][1]:
                        main_output[j].append({
                            "token": {
                                "text": elem[1],
                                "offset_start": token["relative"][0],  # on change pour le relative
                                "offset_end": token["relative"][1],
                                "ref_id_chain": elem[0],
                                "warning": elem[4]
                            }
                        })

    return main_output
