from depccg.download import load_model_directory
from depccg.parser import EnglishCCGParser
from depccg.printer import print_
from depccg.printer import ConvertToJiggXML
from depccg.printer import to_jigg_xml
from depccg.download import SEMANTIC_TEMPLATES
import spacy
from spacy.tokens import Doc
from depccg.semantics.ccg2lambda import parse as ccg2lambda


class Token(dict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __getattr__(self, item):
        return self[item]

    def __repr__(self):
        res = super().__repr__()
        return f'Token({res})'

    @classmethod
    def from_piped(cls, string: str) -> 'Token':
        # WORD|POS|NER or WORD|LEMMA|POS|NER
        # or WORD|LEMMA|POS|NER|CHUCK
        items = string.split('|')
        if len(items) == 5:
            word, lemma, pos, entity, chunk = items
        elif len(items) == 4:
            word, lemma, pos, entity = items
            chunk = 'XX'
        else:
            assert len(items) == 3
            word, pos, entity = items
            lemma = 'XX'
            chunk = 'XX'

        return Token(word=word,
                     lemma=lemma,
                     pos=pos,
                     entity=entity,
                     chunk=chunk)

    @classmethod
    def from_word(cls, word: str) -> 'Token':
        return Token(word=word,
                     lemma='XX',
                     pos='XX',
                     entity='XX',
                     chunk='XX')



def annotate_using_spacy(sentences, n_threads=2, batch_size=10000):
    nlp = spacy.load('en_core_web_sm', disable=['parser'])
    docs = [Doc(nlp.vocab, sentence) for sentence in sentences]
    for name, proc in nlp.pipeline:
        docs = proc.pipe(docs,
                        n_threads=n_threads,
                        batch_size=batch_size)

    res = []
    for sentence in docs:
        tokens = []
        for token in sentence:
            if token.ent_iob_ == 'O':
                ner = token.ent_iob_
            else:
                ner = token.ent_iob_ + '-' + token.ent_type_

            # takes care of pronoun
            if token.lemma_ == '-PRON-':
                lemma = str(token).lower()
            else:
                lemma = token.lemma_.lower()
            tokens.append(
                Token(word=str(token),
                        pos=token.tag_,
                        entity=ner,
                        lemma=lemma,
                        chunk='XX'))
            res.append(tokens)
    return res

model, config = load_model_directory("en")
parser = EnglishCCGParser.from_json(config, model)

story = [["This is a test ."],["Zach is cool ."],["I love NLP ."]]
knowledge_base = []
for fin in story:
    doc = [l.strip() for l in fin]
    doc = [sentence for sentence in doc if len(sentence) > 0]
    tagged_doc = annotate_using_spacy([[word for word in sent.split(' ')] for sent in doc])

    res = parser.parse_doc(doc)

    semantic_templates = SEMANTIC_TEMPLATES.get('en')


    # CONVERT TO FOL
    nbest_trees = res
    jigg_xml = to_jigg_xml(nbest_trees, tagged_doc)
    templates = semantic_templates
    _, formulas_list = ccg2lambda.parse(jigg_xml, str(templates))
    for i, (parsed, formulas) in enumerate(zip(nbest_trees, formulas_list)):
        for (tree, prob), formula in zip(parsed, formulas):
            knowledge_base.append(formula)
            print(f'ID={i} log probability={prob:.4e}\n{formula}') # file=file)

print("\n")
print(knowledge_base)
