import sys
import io
import re

import nltk
from nltk.tokenize import sent_tokenize
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag

import spacy


class Parser:
    def __init__(self, document):
        self.flatten = lambda t: [item for sublist in t for item in sublist]
        self.ref_doc = sent_tokenize(document)
        self.nlp = spacy.load("en_core_web_lg")

        # NLTK NE_CHUNKING
        self.tagged_sents = self.preprocess(document)
        self.chunked_sentences = [nltk.chunk.ne_chunk(sent) for sent in
                                  self.tagged_sents]
        # SPACY NER
        doc = [self.nlp(sent) for sent in self.ref_doc]
        self.spacy_ents = [(X, X.label_) for sent in doc for X in sent.ents]

        self.entites = self.namedEntityRecognitionParse()
        self.people = self.personParse()
        self.locations = self.locationParse()
        self.times = self.temporalParse()
        self.prepositionalPhraseParse()
        # print("PEOPLE: ", self.people)
        # print("LOCATIONS: ", self.locations)
        # print("TIMES: ", self.times)

    def parseForFeatures(self, chunked_sentences, featureList):
        returnList = []
        for sent in chunked_sentences:
            for tuple in sent:
                try:
                    if (tuple.label()) in featureList:
                        tuple = list(map(lambda x: str(x[0]), tuple))
                        entity = ' '.join(tuple)
                        returnList.append(entity)
                except AttributeError:
                    pass
        return returnList

    def preprocess(self, document):
        sentences = sent_tokenize(document)
        sentences = [word_tokenize(sent) for sent in sentences]
        sentences = [pos_tag(sent) for sent in sentences]
        return sentences

    def namedEntityRecognitionParse(self):
        # ne_chunk(sent, binary=True) if we don't care what class it's in
        chunked_sentences = [nltk.chunk.ne_chunk(sent, binary=True) for sent in
                             self.tagged_sents]
        entities = [re.findall(r'NE\s(.*?)/', str(chunk)) for chunk in
                    chunked_sentences]
        nltk_ents = list(filter(lambda x: x != [], entities))

        doc = [self.nlp(sent) for sent in self.ref_doc]
        spacy_ents = [X.text for sent in doc for X in sent.ents]
        return nltk_ents + spacy_ents

    def temporalParse(self):
        dates = [re.findall(r'\d+\S\d+\S\d+', str(sent)) for sent in
                 self.ref_doc]
        times = [re.findall(r'\d?\d:\d\d ?[a|p]?\.?m?\.?', str(sent)) for
                 sent in self.ref_doc]
        # ADD TEMPORAL WORDS and DATES WITH MONTHS
        times = self.flatten(times)
        dates = self.flatten(dates)

        featureList = "TIME"
        spacy_ents = list(
            filter(lambda x: x[1] in featureList, self.spacy_ents))
        spacy_ents = list(map(lambda x: str(x[0]), spacy_ents))
        return list(set(spacy_ents + dates + times))

    def locationParse(self):
        featureList = ["LOCATION", "GPE"]
        nltk_ents = self.parseForFeatures(self.chunked_sentences, featureList)

        spacy_ents = list(
            filter(lambda x: x[1] in featureList, self.spacy_ents))
        spacy_ents = list(map(lambda x: str(x[0]), spacy_ents))
        return list(set(nltk_ents + spacy_ents))

    def personParse(self):
        featureList = ["PERSON"]
        nltk_ents = self.parseForFeatures(self.chunked_sentences, featureList)

        spacy_ents = list(
            filter(lambda x: x[1] in featureList, self.spacy_ents))
        spacy_ents = list(map(lambda x: str(x[0]), spacy_ents))
        return list(set(nltk_ents + spacy_ents))

    def prepositionalPhraseParse(self):
        #doc = [self.nlp(sent) for sent in self.ref_doc]
        #for token in doc[3]:
        #    print(token, token.dep_)
        return

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python3 parser.py FILE_NAME")
        sys.exit(1)

    txt = sys.argv[1]

    with io.open(txt, 'r', encoding='utf8') as f:
        train_data = f.read()

    Parser(train_data)
