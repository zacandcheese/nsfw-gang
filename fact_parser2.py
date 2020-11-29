import re
import stanza
import deplacy

config = {
    'processors': 'tokenize,pos,lemma,depparse',
    'lang': 'en',
}
nlp = stanza.Pipeline(**config)

string = "The Old Kingdom is the period in the third millennium (c. 2686-2181 BC) also known as the 'Age of the Pyramids' or 'Age of the Pyramid Builders' as it includes the great 4th Dynasty when King Sneferu perfected the art of pyramid building and the pyramids of Giza were constructed under the kings Khufu, Khafre, and Menkaure. "

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
#print(nlp(string))
deplacy.render(doc)