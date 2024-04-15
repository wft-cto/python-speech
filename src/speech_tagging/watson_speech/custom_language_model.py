import json
import time
from src.speech_tagging.watson_speech.watson import Watson


class CustomLanguageModel(Watson):
    def __init__(self):
        super().__init__()

    def create_language_model(self, model_name, description="Language Model"):

        language_model = self._speech_to_text.create_language_model(
            model_name,
            'en-US_BroadbandModel',
            description=description
        ).get_result()
        return language_model.get('customization_id')

    def list_language_models(self):
        language_models = self._speech_to_text.list_language_models().get_result()
        return language_models

    def delete_language_model(self, customization_id):
        try:
            self._speech_to_text.delete_language_model(customization_id)
            return True
        except:
            return False

    def train_language_model(self, customization_id):
        try:
            self._speech_to_text.train_language_model(customization_id, strict=False)
            # Poll for language model status.
            while True:
                model = self.get_language_model(customization_id)
                status = model['status']
                print(status)
                if status == "available":
                    return True
                time.sleep(10)
        except:
            return False

    def list_text_corpora(self, customization_id):
        corpora = self._speech_to_text.list_corpora(customization_id).get_result()
        return corpora

    def _remove_faulty_words(self, customization_id):
        """
        Faulty words are those for which Watson couldn't produce the sound
        Presence of faulty words results in training failure of language model
        :param customization_id:
        :return:
        """
        words = self._speech_to_text.list_words(customization_id).get_result()

        for word_json in words["words"]:
            if word_json.get("error") is not None:
                word = word_json["display_as"]
                print("Removed word: ", word)
                self._speech_to_text.delete_word(
                    customization_id,
                    word
                )

    def add_text_corpus(self,  customization_id, corpus_name,text_path="./data/war_and_peace.txt"):

        try:
            with open(text_path, 'rb') as corpus_file:
                self._speech_to_text.add_corpus(
                    customization_id,
                    corpus_name,
                    corpus_file,
                    allow_overwrite=True
                )

            while True:
                corpus = self.get_corpus(customization_id, corpus_name)
                status = corpus["status"]
                print(status)
                if status == "analyzed":
                    break

                time.sleep(5)

            self._remove_faulty_words(customization_id)
            return True
        except:
            return False

    def delete_text_corpus(self, customer_id, corpus_name):
        try:
            self._speech_to_text.delete_corpus(
                customer_id,
                corpus_name
            )
            return True
        except:
            return False

    def list_custom_words(self, customization_id):
        words = self._speech_to_text.list_words(customization_id).get_result()
        return words

    def get_language_model(self, customization_id):

        language_model = self._speech_to_text.get_language_model(customization_id).get_result()
        return language_model

    def get_corpus(self, customization_id, corpus_name):
        corpus = self._speech_to_text.get_corpus(
            customization_id,
            corpus_name
        ).get_result()
        return corpus


if __name__ == "__main__":
    lm = CustomLanguageModel()
    # cid = lm.create_language_model("first_language_model")
    # print(cid)
    lm_models = lm.list_language_models()
    print(lm_models)

    # lm.delete_language_model("dddf59ab-dc16-488e-a39c-ea95decc3ef8")
    # lm.add_text_corpus("cfea6fd1-33da-4a3f-ad34-928785934cc8", "two_cities","./data/tale_of_two_cities.txt")

    # lm.train_language_model("cfea6fd1-33da-4a3f-ad34-928785934cc8")
    # print(lm.list_text_corpora("cfea6fd1-33da-4a3f-ad34-928785934cc8"))
    # lm.list_custom_words("5f816990-047e-458b-a743-573828d50bba")
    # lm.delete_text_corpus("5f816990-047e-458b-a743-573828d50bba","war_and_peace")
    # lm.get_corpus("5f816990-047e-458b-a743-573828d50bba","war_and_peace")

    # print(lm.get_language_model("cfea6fd1-33da-4a3f-ad34-928785934cc8"))
    #
    for model in lm_models['customizations']:
        lm.delete_language_model(model["customization_id"])
    # print(lm.get_language_model("8727ae66-563d-475a-84c3-4954889110a5"))
    # print(lm.list_text_corpora(customization_id="8727ae66-563d-475a-84c3-4954889110a5"))
