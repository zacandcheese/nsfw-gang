#!/usr/bin/python3 -W ignore::DeprecationWarning
# -*- coding:utf8 -*-
import sys
import spacy
import stanza
from facts_parser import *



nlp_spacy = spacy.load("en_core_web_lg")
def sentence_similarity(question, file):

    q = nlp_spacy(question)
    best_sent = ""
    max = -1
    for sent in file.sents:
        score = sent.similarity(q)
        if (score > max):
            max = score
            best_sent = sent
    # print(max, best_sent)
    subject = [tok for tok in best_sent if (tok.dep_ == "nsubj")]
    return subject[0]

def fol_ask(kb, dep_question, doc, question):
    answer = ""
    """
    print(convert_dep_to_fol(dep_question))
    options = list(kb.ask_generator(expr("Improved(a, b, None, c)")))
    var = Expr("a")
    options = list(filter(lambda x: x[var] != Expr("None"), options))
    print(options)
    """
    sentence_similarity(question, doc)
    return answer
if __name__ == "__main__":
    input_file = sys.argv[1]
    question_file = sys.argv[2]

    config = {
        'verbose': False, 'processors': 'tokenize,pos,lemma,depparse',
        'lang': 'en',
    }

    nlp = stanza.Pipeline(**config)
    logger.removeHandler(stanza.log_handler)

    f = open(file=input_file, encoding="utf-8", mode="r+")
    string = f.read()
    spacy_string = string
    string = preprocess_string(string)
    doc = nlp(string)

    clauses = []
    for sent in doc.sentences:
        clauses.extend(convert_dep_to_fol(sent))

    clauses = list(set(clauses))
    # print(clauses)
    kb = FolKB(clauses)

    list_of_questions = ["What is the genus of the dog?", "Is the dog cool?"]
    q = open(file=question_file, encoding="utf-8", mode="r+")
    spacy_doc = nlp_spacy(spacy_string)
    count = 0
    for question in q:
        print('A' + str(count), sentence_similarity(question, spacy_doc))