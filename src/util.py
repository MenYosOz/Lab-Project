import re


def get_f1(tp, fp, fn):
    if sum(tp.values())+sum(fp.values()) == 0:
        precision = 0
    else:
        precision = sum(tp.values())/(sum(tp.values())+sum(fp.values()))

    if sum(tp.values())+sum(fn.values()) == 0:
        recall = 0
    else:
        recall = sum(tp.values())/(sum(tp.values())+sum(fn.values()))

    if precision + recall == 0:
        f1 = 0
    else:
        f1 = 2 * precision * recall / (precision + recall)
    
    return 100 * precision, 100 * recall, 100 * f1


def get_f1_macro(tp, fp, fn, prnt=False):
    if prnt:
        print('{:<10}  {:>10}  {:>10}  {:>10}    {:<10}'.format(f"type", f"precision", f"recall", f"f1", f"support"))

    p = []
    r = []
    f = []
    s = []
    for rtype in tp.keys():
        if tp[rtype]+fn[rtype] == 0:
            continue
        if tp[rtype]+fp[rtype] == 0:
            precision = 0
        else:
            precision = tp[rtype]/(tp[rtype]+fp[rtype])

        if tp[rtype]+fn[rtype] == 0:
            recall = 0
        else:
            recall = tp[rtype]/(tp[rtype]+fn[rtype])

        if precision + recall == 0:
            f1 = 0
        else:
            f1 = 2 * precision * recall / (precision + recall)
        
        support = tp[rtype]+fn[rtype]
        if prnt:
            print('{:<10}  {:>10}  {:>10}  {:>10}    {:<10}'.format(f"{rtype}", f"{100*precision:.2f}", f"{100*recall:.2f}", f"{100*f1:.2f}", f"{support}"))
        p.append(precision)
        r.append(recall)
        f.append(f1)
        s.append(support)

    if prnt:
        print('{:<10}  {:>10}  {:>10}  {:>10}    {:<10}'.format("-", "-", "-", "-", "-",))
        print('{:<10}  {:>10}  {:>10}  {:>10}'.format(f"macro", f"{100*sum(p)/len(p):.2f}", f"{100*sum(r)/len(r):.2f}", f"{100*sum(f)/len(f):.2f}"))
    
    return 100*sum(p)/len(p), 100*sum(r)/len(r), 100*sum(f)/len(f)


def process_sentences_BioRED(sentences_text):
    ret_list = []
    sentences = re.split(r'((?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s)', sentences_text)
    offset_between_sentences = list([len(sentences[i]) for i in range(1, len(sentences), 2)]) + [0]
    sentences = [sentences[i] for i in range(0, len(sentences), 2)]
    # print(sum([len(s) for s in sentences]) + sum(offset_between_sentences), len(sentences_text))
    # print(sum([len(s) for s in sentences_tmp]), len(sentences_text), len(sentences), len(sentences_tmp))
    for i_s, s in enumerate(sentences):
        l = re.split(r'(?!\.(?!$))(\W)', s)
        l = list([item for item in l if item not in ('', ' ', '\n')])
        ret_list.append(l)
    return ret_list, sentences, offset_between_sentences


def apply_window_fix(pos, name, sentence):
    ret_pos = pos
    list_of_words = sentence[pos[0]:pos[1]]
    list_of_words_left_shift = ''.join(sentence[max(pos[0] - 1, 0):pos[1]])
    list_of_words_right_shift = ''.join(sentence[pos[0]:min(pos[1] + 1, len(sentence))])

    if name != ''.join(list_of_words):
        if name == list_of_words_left_shift:
            ret_pos = max(pos[0] - 1, 0), pos[1]
        elif name == list_of_words_right_shift:
            ret_pos = pos[0], min(pos[1] + 1, len(sentence))
    return ret_pos


def find_sent_id_and_pos(locations, sentences, initial_offset, passage, name, offset_between_sentences,
                         original_sentences, k=10):
    entity_position = locations[0]["offset"] - initial_offset
    crop_with_entity = passage[max(entity_position - k, 0): min(entity_position + locations[0]["length"] + k,
                                                                len(passage))]
    crop_with_entity = crop_with_entity.replace(' ', '')
    # print(crop_with_entity, entity_position)
    index = -1
    counter_offset = 0
    counter_space = 0
    counter_name_space = name.count(' ')
    pos = [0, 1]
    # for i, s in enumerate(sentences):
    #     join_sentence = ''.join(s)
    #     if crop_with_entity in join_sentence:
    #         index = i
    #         break
    for i, s in enumerate(original_sentences):
        counter_offset += len(s) + offset_between_sentences[i]
        if counter_offset >= locations[0]["offset"]:
            index = i
            break

    flag_in_name = False
    selected_sentence = original_sentences[index]
    # counter_space = sum(s.count(' ') for s in original_sentences[:index])
    counter_offset -= (len(selected_sentence) + offset_between_sentences[index])
    counter_offset_word = counter_offset
    l = re.split(r'(?!\.(?!$))(\W)', selected_sentence)
    l = list([item for item in l if item not in ('', '\n')])
    tmp = 0
    for word in l:
        if counter_offset_word > locations[0]["offset"] and not (flag_in_name):
            pos[0] = tmp - 1
            # print(word, pos[0])
            flag_in_name = True
        if counter_offset_word >= locations[0]["offset"] + locations[0]["length"] - 1 and flag_in_name:
            # print(word, tmp)
            pos[1] = tmp
            break
        counter_offset_word += len(word)

        if not (str.isspace(word)):
            tmp += 1

        # if str.isspace(word) and counter_offset_word <= locations[0]["offset"]:
        #   counter_space+=1;

    pos = apply_window_fix(pos, name.replace(' ', ''), sentences[index])

    # print(word, str.isspace(word), len(word))
    # print("*************************8")

    # print(counter_offset)
    # for i, word in  enumerate(sentences[index]):
    #     # print(counter_offset + counter_space, locations[0]["offset"])
    #     if  (counter_offset + counter_space) >= locations[0]["offset"] and (not flag_in_name):
    #         pos[0] = i
    #         flag_in_name = True

    #     if (counter_offset + counter_space + counter_name_space) >= locations[0]["offset"] + locations[0]["length"]  and flag_in_name:
    #         pos[1] = i
    #         break
    #     counter_offset += len(word)

    # print(index, pos, counter_offset, locations[0]["offset"], len(original_sentences) )
    # print(counter_space, locations[0]["offset"], locations[0]["length"] , name )
    # print(sentences[index], name)
    # print(index, pos,counter_offset + counter_space + counter_name_space, counter_offset_word, locations[0]["offset"] + locations[0]["length"], l)# , counter_space, selected_sentence, sentences[index])
    # print(index, pos)
    return index, pos


def convert_BioRED_to_FREDo_format(input_file_BioRED):
    ret_json = []
    for d_i in range(len(input_file_BioRED["documents"])):
        ret_sentences = []
        dict_vertex_set = {}
        ret_vertex_set = []
        ret_labels = []
        sentences_original_document = []
        offset_between_sentences_document = []
        counter_vertex_id = 0
        docmurnt_entity_to_annotation = {}
        for i, p in enumerate(input_file_BioRED["documents"][d_i]["passages"]):
            sentences, sentences_original, offset_between_sentences = process_sentences_BioRED(p["text"])
            ret_sentences.extend(sentences)
            sentences_original_document.extend(sentences_original)
            offset_between_sentences_document.extend(offset_between_sentences)
            for a in p["annotations"]:
                for id in a["infons"]["identifier"].split(','):
                    if id in docmurnt_entity_to_annotation:
                        entity_vertex_id = docmurnt_entity_to_annotation[id][0][1]
                        docmurnt_entity_to_annotation[id].append((a, entity_vertex_id))
                    else:
                        docmurnt_entity_to_annotation[id] = [(a, counter_vertex_id)]
                        dict_vertex_set[id] = []
                        counter_vertex_id += 1

                    name_vertex_var = a["text"]
                    type_vertex_var = a["infons"]["type"]
                    sent_id_vertex_var, pos_vertex_var = find_sent_id_and_pos(a["locations"], ret_sentences,
                                                                              p["offset"], p["text"], a["text"],
                                                                              offset_between_sentences_document,
                                                                              sentences_original_document)
                    dict_vertex_set[id].append({"pos": pos_vertex_var, "type": type_vertex_var, "name": name_vertex_var,
                                                "sent_id": sent_id_vertex_var})

        ret_vertex_set = [(v, docmurnt_entity_to_annotation[k][0][1]) for k, v in dict_vertex_set.items()]
        ret_vertex_set = list([v for v, _ in sorted(ret_vertex_set, key=lambda x: x[1])])
        # return
        for r in input_file_BioRED["documents"][d_i]["relations"]:
            entity1_type = docmurnt_entity_to_annotation[r["infons"]["entity1"]][0][0]["infons"]["type"]
            entity2_type = docmurnt_entity_to_annotation[r["infons"]["entity2"]][0][0]["infons"]["type"]
            r_label_ret = entity1_type + "-" + r["infons"]["type"] + "-" + entity2_type
            ret_labels.append({"r": r_label_ret, "h": docmurnt_entity_to_annotation[r["infons"]["entity1"]][0][1], "t":
                docmurnt_entity_to_annotation[r["infons"]["entity2"]][0][1], "evidence": []})
            # set_of_entity_type.extend([entity1_type, entity2_type])
            # set_of_relations.append(entity1_type + "-" + r["infons"]["type"] + "-" + entity2_type)
            # set_of_associations.append(r["infons"]["type"])
        ret_json.append({"sents": ret_sentences, "title": "None for now", "vertexSet": ret_vertex_set,
                         "labels": ret_labels})
    return ret_json
