import spacy
import re

nlp = spacy.load('en_core_web_sm')
nlp.max_length = 3227675

# def get_actions(transcript):
#     nlp = spacy.load('en_core_web_lg')
#     # doc = nlp(transcript)
#     doc = nlp(u"")
    
#     for token in doc:


class ExtractAction():
    def __init__(self):
        super().__init__()    

    def check_imperative(self,transcript):
        action_list = []
        # print(transcript)
        # transcript = transcript.lower()
        doc = nlp(transcript)

        try:
            if (doc[0].text == doc[0].head.text):
                if doc[0].pos_ == 'VERB':
                    if (doc[0].text == doc[0].lemma_):
                        if (doc[1].pos_ != "PRON"):
                            token_head = doc[0]
                            token_head_edge = doc[0].right_edge
                            
                            action_regex = re.compile(u'{}(.*){}'.format(token_head,re.escape(str(token_head_edge))))
                            actions = action_regex.search(str(doc))
                            if actions is not None:
                                # print(actions.group(0))                                 
                                start_position = 0
                                end_position = len(actions.group(0)) - 1
                                
                                action_dict ={
                                        'action':actions.group(0),
                                        'start_position':start_position,
                                        'end_position':end_position
                                        }
                                action_list.append(action_dict)
                                print(action_list)
                                return action_list                       
        except:
            pass

        for token in doc:
            # if (token.text == token.head.text):
                if token.pos_ == 'VERB':
                    # if (token.text == token.lemma_ or token.text == token.lemma_):
                        try:
                            if (
                                token.nbor(-1).pos_ == "PROPN"
                                or token.nbor(-1).pos_ == "CCONJ"
                                or token.nbor(-1).pos_ == "INTJ"
                                or token.nbor(-1).pos_ == "ADV"

                                or (token.nbor(-1).text == "you" and token.nbor(-2).tag_ in ["MD", "IN"])
                                or token.nbor(-1).tag_ == "NNS"

                                or token.nbor(1).tag_ == "JJ"
                                or (token.nbor(-1).text == "you" and token.nbor(1).pos_ in ["NOUN", "VERB"])
                                or (token.nbor(-1).pos_ == "PART" and token.nbor(-2).pos_ in ["VERB", "PRON"])

                                or token.text == "recommend" and token.nbor(1).pos_ == "ADP"
                                or (token.nbor(-2).text == "you" and token.nbor(-1).tag_ == "MD")
                                ):

                                # print("yes neighbour, imperative sentence")
                                token_head = token.text

                                token_head_edge = token.right_edge

                                action_regex = re.compile(u'{}(.*){}'.format(token_head,re.escape(str(token_head_edge))))
                                actions = action_regex.search(str(doc))
                                if actions is not None:
                                    start_position = transcript.index(actions.group(0))
                                    end_position = start_position + len(actions.group(0)) -1
                                    action_dict ={
                                                'action':actions.group(0),
                                                'start_position':start_position,
                                                'end_position':end_position
                                                }
                                    action_list.append(action_dict)
                                    # print(action_list)
                                    return action_list
                        except:
                            pass

            
    
if __name__ == '__main__':
    # print("I am in main function")
    ea = ExtractAction()
    transcript = "okay yeah go to the plan updated on white to get it updated by with by the end of the week and then on the on the M. you numbers what I'm looking for is by in you the total pipeline created for twenty nineteen so to be a some of all opportunities won or lost"
    ea.check_imperative(transcript)
