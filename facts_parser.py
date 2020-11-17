import stanza
from aima3.logic import expr
from aima3.logic import FolKB
import num2words
# stanza.download('en')

config = {
    'processors':'tokenize,pos,lemma,depparse',
    'lang':'en',
}
nlp = stanza.Pipeline(**config)
doc = nlp("The dog and the extant gray wolf are sister taxa as modern wolves are not closely related to the wolves that were first domesticated, which implies that the direct ancestor of the dog is extinct. The dog was the first species to be domesticated and has been selectively bred over millennia for various behaviors, sensory capabilities, and physical attributes.")
print(*[f'id: {word.id}\tword: {word.text}\t\thead id: {word.head}\thead:'
        f' {sent.words[word.head-1].text if word.head > 0 else "root"}\tdeprel: '
        f'{word.deprel}' for sent in doc.sentences for word in sent.words], sep='\n')

def remove_rel_clause(sent):
    clauses = [] # Set of tuples, head and phrase
    return sent, clauses

def convert_dep_to_fol(sent):
    """

    Parameters
    ----------
    dep: One sentence's dependency tree.

    Returns: A fol
    -------

    """
    dep, clauses = remove_rel_clause(sent)
    # Find root:
    root = None

    for i, word in enumerate(sent.words):
        if (word.deprel == 'root'):
            root = word.text
        if (root == 'the'):
          for word in sent.words:
              if (word.deprel == 'acl:relcl'):
                  root = word.text
        if (root == "Britain"):
            for word in sent.words:
                if (word.deprel == 'acl'):
                    root = word.text

    nsubj = None
    iobj = None
    obj = None
    for word in sent.words:
        head = sent.words[word.head-1].text

        if (head == root):
            # Find nsubj for root:
            if (word.deprel == 'nsubj' or word.deprel == 'nsubj:pass' or
            word.deprel == 'obl' or word.deprel == 'csubj' or word.deprel ==
                    'expl'):
                nsubj = word.text.capitalize()
            # Find iobj for root:
            if (word.deprel == 'iobj' or word.deprel == 'nmod'):
                iobj = word.text.capitalize()
            # Find obj for root:
            if (word.deprel == 'obj'):
                obj = word.text.capitalize()

    # Generate string for expr
    clauses = []
    expr_str = ""
    root_intake_str = ""
    i = 0
    if (nsubj == None and iobj == None and obj == None):
        return []
    for word in [nsubj, iobj, obj]:
        if word != None:
            try:
                int(word)
                word = num2words.num2words(word)
            except ValueError:
                pass
            clauses.append(expr(str(word) + "(" + str(word) + ")"))
            variable = chr(ord('a') + i)
            expr_str += word + "(" + variable + ") & "
            root_intake_str += variable + ", "
            i += 1
    root_intake_str = root_intake_str[:-2]
    expr_str = expr_str[:-2] + "==> " + root.capitalize() + "(" + \
               root_intake_str + ")"
    print(expr_str)
    clauses.append(expr(expr_str))
    return clauses

import os
print(os.getcwd())
f = open(file="NLP_PROJ\\set5\\a1.txt", encoding="utf-8", mode="r+")
import re

string = f.read()
(start, stop) = (re.search("See also", string)).span()

string = re.sub("%", " percent", string)
# print(start)
# print(string[:start])


doc = nlp(string[:start])


clauses = []
for sent in doc.sentences:
    if (len(sent.words) > 5):
        clauses.extend(convert_dep_to_fol(sent))

clauses = list(set(clauses))
print(clauses)
kb = FolKB(clauses)
print(kb.ask(expr("Die(x)")))