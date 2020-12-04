import spacy
nlp = spacy.load("en_core_web_lg")
doc = nlp(question)