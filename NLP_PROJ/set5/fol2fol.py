old_fol = "exists x01.(_zach(x01) & exists x02.(_weapon(x02) & exists e03.(_sell(e03) & (Subj(e03) = x01) & (Acc(e03) = x02) & exists x04.(_megan(x04) & (Dat(e03) = x04)))))"

import re

class FOL:
    def __init__(self, old_fol):
        self.old_fol = old_fol
        self.new_fol = self.convert(old_fol)

    def convert(self, old_fol):
        """
        Ex.
        exists x01.(_zach(x01) & exists x02.(_weapon(x02) & exists e03.(
        _sell(e03) & (Subj(e03) = x01) & (Acc(e03) = x02) & exists x04.(_megan(x04) & (Dat(e03) = x04)))))

        <->

        (_zach(x01) & _weapon(x02) & _sell(e03) & _megan(x04) &
        (Subj(e03) = x01) & (Acc(e03) = x02) & (Dat(e03) = x04))

        <->

        (_zach(x01) & _weapon(x02) & _megan(x04) & _sell(x01, x02, x04))
        """
        # Get rid of exists
        old_fol = re.sub('exists [x|e]\d*\.', '', old_fol)
        Predicates = re.findall(r"_[a-zA-Z\d(]*\)", old_fol)
        Predicates = list(map(lambda x: Predicate(x), Predicates))
        Rules =
        return old_fol

class Predicate:
    def __init__(self, string):
        self.string = string
        self.Property = self.extract_Property(string)
        self.Variables = self.extract_Variables(string)

    def extract_Property(self, string):
        return re.search(r"[a-zA-Z\d]+(?=\()", string).group()
    def extract_Variables(self, string):
        return re.findall(r'(?<=\()[a-zA-Z\d]+', string)
    def __str__(self):
        return self.Property + ": " + ' '.join(self.Variables)
class Variable:
    def __init__(self):
        self.name = ""

print(FOL(old_fol).new_fol)

