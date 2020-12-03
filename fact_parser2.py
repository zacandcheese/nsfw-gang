import re
import stanza
import deplacy

config = {
    'processors': 'tokenize,pos,lemma,depparse',
    'lang': 'en',
}
nlp = stanza.Pipeline(**config)

string = "The Old Kingdom is the period in the third millennium also known as the 'Age of the Pyramids' or 'Age of the Pyramid Builders' as it includes the great 4th Dynasty when King Sneferu perfected the art of pyramid building and the pyramids of Giza were constructed under the kings Khufu, Khafre, and Menkaure. "
string += "Zach is happy and Zach is sad."
string = "Megan wants a corn dog in her mouth."
string = "In 1758, the taxonomist Linnaeus published in his Systema Naturae the classification of species."
#string = "To these ends, over a period of time, Egyptian artists adopted a
# limited repertoire of standard types and established a formal artistic canon that would define Egyptian art for more than 3,000 years, while remaining flexible enough to allow for subtle variation and innovation."
#string = "I like to run and jump and swim"
#string = "There were military expeditions into Canaan and Nubia,
# with Egyptian influence reaching up the Nile into what is today the Sudan."
#string = "The largest known dog was an English Mastiff which weighed 155.6
# kg and was 250 cm from the snout to the tail"
string = "Who is cool. "
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
