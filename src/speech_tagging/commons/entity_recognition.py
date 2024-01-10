import spacy

nlp = spacy.load('en_core_web_sm')
nlp.max_length = 3227675

def recognize_ents(transcript_text, action_phrases):
    if len(action_phrases) == 1:
        new_action_phrases = []
        action_phrase = extract_entity(transcript_text, action_phrases[0])
        new_action_phrases.append(action_phrase)

    elif len(action_phrases) == 2:
        new_action_phrases = []
        first_action_phrase, second_action_phrase, text_remaining = transcript_text.split("</mark>")
        # action_phrase_list = transcript_text.split("</mark>")
        action_phrase_with_entity = extract_entity(first_action_phrase, action_phrases[0])
        new_action_phrases.append(action_phrase_with_entity)
        action_phrase_with_entity = extract_entity(second_action_phrase, action_phrases[1])
        new_action_phrases.append(action_phrase_with_entity)

        # action_phrases = extract_entity(action_phrase_list, action_phrases)

    # print("action phrases from entity recognition ***************") 
    # print(new_action_phrases)               
    return new_action_phrases

def extract_entity(text_phrase, action_phrase):
    remove_mark_tag = text_phrase.replace('<mark>','')
    remove_mark_tag_with_slash = remove_mark_tag.replace('</mark>','')
    doc = nlp(remove_mark_tag_with_slash)
    if doc.ents:
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                # print(ent.text + '--' + ent.label_ + '==>' + str(spacy.explain(ent.label_)))
                person = {"assign_to":ent.text}
                action_phrase.update(person)
            else:
                action_phrase.update({"assign_to":""})
            if ent.label_ == "DATE":
                # print(ent.text + '--' + ent.label_ + '==>' + str(spacy.explain(ent.label_)))   
                date = {"due_date":ent.text}
                action_phrase.update(date)
            else:
                action_phrase.update({"due_date":""})
    else:
        entity_dict = {'assign_to':'',
                        'due_date':''}
        action_phrase.update(entity_dict)
    #     # action_phrase.update({'assign_to':""})
    return action_phrase



if __name__ == "__main__":
    # test for two action
    transcript_text = "<mark>go through the plan updated mike, i'd like to get it updated by next March 5</mark> also good morning to all <mark>sarah, please send me file on tuesday</mark>"
    action_phases = [
                        {"action": "go through the plan updated mike, i'd like to get it updated by next March 5",
                        "start_position": 10,
                        "end_position": 63
                        },
                        {"action": "sarah, please send me file on tuesday",
                        "start_position": 10,
                        "end_position": 63
                        },
                    ]

    # # test for one action
    # transcript_text = "<mark>go through the plan updated mike, i'd like to get it updated by next March 5</mark> also good morning to all"
    # action_phases = [
    #                 {"action": "go through the plan updated mike, i'd like to get it updated by next March 5",
    #                 "start_position": 10,
    #                 "end_position": 63
    #                 }
    #             ]
    recognize_ents(transcript_text, action_phases)
    
