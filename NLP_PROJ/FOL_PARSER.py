import nltk
from nltk.corpus import treebank
from nltk import induce_pcfg

productions = []
for item in treebank.fileids():
    for tree in treebank.parsed_sents(item):
        tree.collapse_unary(collapsePOS = False)
        tree.chomsky_normal_form(horzMarkov = 2)
        productions += tree.productions()

from nltk import Nonterminal
S = Nonterminal('S')
grammar = induce_pcfg(S, productions)


result = nltk.sem.interpret_sents(['a dog barks'], grammar)
(syntree, semrep) = result['a dog barks'][0]
print(syntree)