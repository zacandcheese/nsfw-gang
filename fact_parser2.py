import re
import stanza
import deplacy

config = {
    'processors': 'tokenize,pos,lemma,depparse',
    'lang': 'en',
}
nlp = stanza.Pipeline(**config)

string = "The Old Kingdom is the period in the third millennium also known as the 'Age of the Pyramids' or 'Age of the Pyramid Builders' as it includes the great 4th Dynasty when King Sneferu perfected the art of pyramid building and the pyramids of Giza were constructed under the kings Khufu, Khafre, and Menkaure. "

def preprocess_string(string):
    try:
        (start, stop) = (re.search("See also", string)).span()
        string = string[:start]
    except AttributeError:
        pass

    string = re.sub("\((.*?)\) ", "", string)  # Remove Parenthesis Asides
    return string

string = preprocess_string(string)
doc = nlp(string)
print(nlp(string))
deplacy.render(doc)

import spacy
nlp_spacy = spacy.load("en_core_web_lg")

str1 = nlp_spacy("implies")
str2 = nlp_spacy("also known")
str3 = nlp_spacy("as it includes")
print(str1.similarity(str2))
print(str1.similarity(str3))
