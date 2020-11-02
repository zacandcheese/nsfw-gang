"Types of Questions"
import sys
import io
from .parser import Parser

class Oracle:
    def __init__(self, Document):
        self.document = Document
        self.parser = Parser(Document)
        self.wh = ["who","what","where","when"]
    def answer(self, question):
        self.question = str.lower(question)
        self.q_parser = Parser(question)
        if "is" in question or "was" in question:
            return self.case0()

    def case0(self):
        "Sentence: ENT is/was a ___. "
        "Question: What is/was ENT? A: ___"
        "Question: What was ___? A: ENT"
        phrase = str.replace(self.question, "?", "")
        phrase = str.replace(phrase, " is ", "?")
        phrase = str.replace(phrase, " was ", "?")
        for wh in self.wh:
            phrase = str.replace(phrase, wh, "")
        returnList = []
        for verb in [" is ", " was "]:
            temp = str.replace(phrase, "?", verb)
            returnList += list(filter(lambda x: temp in str.lower(x),
                                      self.parser.ref_doc))
        print(returnList)
        print(phrase)
        return "Not Implemented"

    def case1(self):
        "Sentence: ENT (DATE)"
        "QUESTION: When was ENT? A: DATE"
        return "Not Implemented"

    def case2(self):
        "Sentence: ENT VP."
        "Question: What was ENT V? A: P"
        return "Not Implemented"

    def case3(self):
        "Sentence: ENT, PP."
        "Question: Who/What was PP? A: ENT"
        return "Not Implemented"

    def case4(self):
        "Sentence: \"ENT/SUBJ: ATRB\"."
        "Question: Who/What is/has ATRB? A: ENT"
        return "Not Implemented"

    def case5(self):
        "Sentence: ENT1 (ENT2 / not date)"
        "Question: What is another name for ENT1? A: ENT"
        return "Not Implemented"

    def case6(self):
        "Sentence: X% __?"
        "Question: What percent of ____? A: X"
        return "Not Implemented"

    def case7(self):
        "Sentence: ENT V ___? "
        "Question: ENT V what A: ___"
        return "Not Implemented"

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 parser.py FILE_NAME")
        sys.exit(1)

    txt = sys.argv[1]

    with io.open(txt, 'r', encoding='utf8') as f:
        train_data = f.read()

    Oracle(train_data)