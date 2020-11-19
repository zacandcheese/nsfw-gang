import stanza
from aima3.logic import expr
from aima3.logic import FolKB
import num2words

import os
import re


# stanza.download('en')
def get_subtree(sent, id):
    # RETURN A LIST OF IDS
    forThePhrase = []
    forTheFOL = []
    for word in sent.words:
        head = word.head
        if head == id:
            forThePhrase.append(word.id)
            if word.upos in ["ADJ", "NUM"]:
                forTheFOL.append(word.id)
    for new_id in forThePhrase:
        temp1, temp2 = get_subtree(sent, new_id)
        forTheFOL.extend(temp1)
        forThePhrase.extend(temp2)
    forTheFOL = list(set(forTheFOL))
    forThePhrase = list(set(forThePhrase))
    return forTheFOL, forThePhrase

def phrase_to_fol_string(phrase):
    #phrase = re.sub(r"[\']",'',phrase)
    phrase = re.sub(r"\W", '', phrase)
    phrase = re.sub("\"", "Quote", phrase)
    words = phrase.split(" ")
    final_set = []
    for word in words:
        try:
            word = num2words.num2words(int(word))
            temp_set = re.findall("[a-zA-Z]+", word)
            temp_set = list(map(lambda x: x.lower().capitalize(), temp_set))
            final_set.extend(temp_set)
        except ValueError:
            final_set.append(word.lower().capitalize())

    string = "".join(final_set)
    string = re.sub(r"\W", '', string)

    return string

def preprocess_string(string):
    try:
        (start, stop) = (re.search("See also", string)).span()
        string = string[:start]
    except AttributeError:
        pass

    string = re.sub("%", " percent", string)  # Modify Percents
    string = re.sub("\((.*?)\)", "", string)  # Remove Parenthesis Asides
    return string


def convert_dep_to_fol(sent):
    """

    Parameters
    ----------
    dep: One sentence's dependency tree.

    Returns: A fol
    -------

    """
    # Find root:
    roots = []
    for i, word in enumerate(sent.words):
        if word.deprel == 'root' or 'acl' in word.deprel:
            roots.append(word.text)


    clauses = []
    for root in roots:
        mod = None
        nsubj = None
        iobj = None
        obj = None

        for word in sent.words:
            head = sent.words[word.head - 1].text
            if (head == root):
                # Find mod
                if 'mod' in word.deprel:
                    mod = (word.text, word.id)

                # Find nsubj for root:
                if 'subj' in word.deprel:
                    nsubj = (word.text, word.id)

                # Find iobj for root:
                if (word.deprel == 'iobj'):
                    iobj = (word.text, word.id)

                # Find obj for root:
                if (word.deprel == 'obj'):
                    obj = (word.text, word.id)

        if (nsubj == None and iobj == None and obj == None):
            continue

        # Generate string for expr
        expr_str = ""
        root_intake_str = ""
        counter = 0
        for word in [mod, nsubj, iobj, obj]:
            if word != None:
                (word, i) = word
                variable = chr(ord('a') + counter)
                JJ = ""

                ################################
                #    GET THE JJ or MODIFIERS   #
                forFOL, forPhrase = (get_subtree(sent, i))
                forPhrase.append(i)
                forPhrase = list(set(forPhrase))
                # these are list of ids
                var = ""
                for idx in forPhrase:
                    var += phrase_to_fol_string(sent.words[idx - 1].text)
                for idx in forFOL:
                    temp = sent.words[idx - 1].text
                    FOLHEAD = phrase_to_fol_string(temp)
                    clauses.append(expr(FOLHEAD + "(" + var + ")"))
                    expr_str += FOLHEAD + "(" + variable + ") & "
                ################################
                wordVar = phrase_to_fol_string(word)
                clauses.append(expr(wordVar + "(" + var + ")"))
                expr_str += wordVar + "(" + variable + ") & "
                root_intake_str += variable + ", "
                counter += 1
            else:
                root_intake_str += "None, "
        root_intake_str = root_intake_str[:-2]
        rootVar = phrase_to_fol_string(root)
        expr_str = expr_str[:-2] + "==> " + rootVar + "(" + \
                   root_intake_str + ")"
        clauses.append(expr(expr_str))
    return clauses


if __name__ == "__main__":
    config = {
        'processors': 'tokenize,pos,lemma,depparse',
        'lang': 'en',
    }
    nlp = stanza.Pipeline(**config)

    f = open(file="NLP_PROJ\\set5\\a2.txt", encoding="utf-8", mode="r+")
    string = f.read()
    # DELETE ME IF YOU WANT TO TRY YOUR OWN PASSAGE #
    # string = "The cool man walked down the street."
    string = preprocess_string(string)

    doc = nlp(string)

    clauses = []
    for sent in doc.sentences:
        clauses.extend(convert_dep_to_fol(sent))

    clauses = list(set(clauses))
    print(clauses)
    kb = FolKB(clauses)
