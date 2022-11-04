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
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', sentences_text)
    for i_s, s in enumerate(sentences):
        l = re.split(r'(?!\.(?!$))(\W)', s)
        l = list([item for item in l if item not in ('', ' ', '\n')])
        ret_list.append(l)
    return ret_list


def find_sent_id_and_pos(locations, sentences, initial_offset, passage, name, k=3):
    entity_position = locations["offset"] - initial_offset
    crop_with_entity = passage[max(entity_position-k, 0): min(entity_position + locations["length"] + k,
                                                              len(passage))]
    crop_with_entity = crop_with_entity.replace(' ', '')
    index = -1
    pos = [0, 1]
    for i, s in enumerate(sentences):
        join_sentence = ''.join(s)
        if crop_with_entity in join_sentence:
            index = i
            break
    flag_in_name = False

    for i, word in  enumerate(sentences[index]):
        if word in name and (not flag_in_name):
            pos[0] = i
            flag_in_name = True

        if word not in name and flag_in_name:
            pos[1] = i
            break

    return index, pos



def convert_BioRED_to_FREDo_format(input_file_BioRED):
    ret_json = []
    docmurnt_entity_to_annotation = {}
    for i in range(len(input_file_BioRED["documents"])):
        ret_sentences = []
        ret_vertex_set = []
        ret_labels = []
        for i, p in enumerate(input_file_BioRED["documents"][i]["passages"]):
            sentences = process_sentences_BioRED(p["text"])
            ret_sentences.extend(sentences)
            for a in p["annotations"]:
                if ',' in a["infons"]["identifier"]:
                    for id in a["infons"]["identifier"].split(','):
                        docmurnt_entity_to_annotation[id] = a
                else:
                    docmurnt_entity_to_annotation[a["infons"]["identifier"]] = a
                name_vertex_var = a["text"]
                type_vertex_var = a["infons"]["type"]
                sent_id_vertex_var, pos_vertex_var = find_sent_id_and_pos(a["locations"], sentences, p["offset"], a["text"], p["text"])
                ret_vertex_set.append([{"pos": pos_vertex_var, "type": type_vertex_var, "name": name_vertex_var,
                                        "sent_id": sent_id_vertex_var}])

        for r in input_file_BioRED["documents"][i]["relations"]:
            entity1_type = docmurnt_entity_to_annotation[r["infons"]["entity1"]]["infons"]["type"]
            entity2_type = docmurnt_entity_to_annotation[r["infons"]["entity2"]]["infons"]["type"]
            r_label_ret = entity1_type + "-" + r["infons"]["type"] + "-" + entity2_type
            ret_labels.append({"r": r_label_ret, "h": "", "t": "", "evidence": []})
            # set_of_entity_type.extend([entity1_type, entity2_type])
            # set_of_relations.append(entity1_type + "-" + r["infons"]["type"] + "-" + entity2_type)
            # set_of_associations.append(r["infons"]["type"])
        ret_json.append({"sents": ret_sentences, "title": "None for now", "vertexSet": ret_vertex_set,
                         "labels": ret_labels})


    return ret_json
