## class names are in camel case, starting with capital letters, function and variable names in snake case, starting with small letters

import enum

class QuestionType(enum.Enum):
    # example of usage : return QuestionType.TF_question
    Wh_question = 0
    TF_question = 1
    # can be generalized?? 'Explain'-type questions etc.

class EntityType(enum.Enum):
    Person = 0
    Thing = 1
    Place = 2
    Abstract = 3
    Event = 4
    # list more if you feel like

### PUBLIC ###

class FOLParser():
    def __init__(self, parser):
        # rules and facts are sets of statements
        self.nlp = parser
        rules = set() # we will manually import this from another file
        self.facts = set()
        self.set_of_attrs = set()
        self.set_of_entities = set()
        self.set_of_predicates = set()
        self.set_of_entity_relations = set()
        self.set_of_predicate_relations = set()
        self.self_of_entity_classes = set()
        self.set_of_verbs = set()
        self.KB = (rules, self.facts)

    def get_subtree(self, sentence, id):
        subtree = []
        attributes = []
        definiteness = True
        for word in sentence.words:
            if (word.head == id):
                if (word.deprel in ["det", "compound"]) or \
                        ("mod" in word.deprel):
                    if (word.deprel == "det"):
                        if word.text in ["a", "an"]: # INDEFINITE
                            definiteness = False
                    attributes.append(word)
                else:
                    subtree.append(word)
            if (word.id == id):
                head_word = word
        return subtree, attributes, definiteness, head_word
    def add_to_KB_from_text(self, text):
        document = self.nlp(text)
        for sentence in document.sentences:
            self.add_to_KB_from_sentence(sentence)
        pass

    def add_to_KB_from_sentence(self, sentence):
        # Break down sentence into clauses #
        # get set ids for heads of clauses
        ids_of_roots = []
        for word in sentence.words:
            if (word.deprel == 'root' or ('cl' in word.deprel)):
                ids_of_roots.append(word.id)

        # PARSE THE CLAUSES
        for id in ids_of_roots:
            subtree, attributes, definitness, head_word = \
                self.get_subtree(sentence, id)

            # HANDLE THE SUBTREE
            subj = None
            direct_obj = None
            indirect_obj = None
            for word in subtree:
                # HOW DO I HANDLE DEFINITENESS?
                # print(head_word.text, word.text, word.deprel)
                if word.deprel not in ["punct"] or "cl" not in word.deprel:
                    _ , tmp_attributes, tmp_definitness, _ = \
                        self.get_subtree(sentence, word.id)
                    if tmp_definitness:
                        # THIS IS AN ENTITY
                        tmp = Entity(word.text, None)
                        tmp.add_attributes(word.text, tmp_attributes)
                        self.facts.add(tmp)
                    else:
                        tmp = EntityClass(word.text, None, tmp_attributes)
                        self.facts.add(tmp)

                    if "subj" in word.deprel:
                         subj = word
                    elif word.deprel == "iobj":
                        indirect_obj = word
                    elif "obl" in word.deprel:
                        direct_obj = word

            # HANDLE HEAD OF TREE
            # THIS IS A PREDICATE?
            self.facts.add(Predicate(word.text, attributes,subj,
                                         direct_obj, indirect_obj))


    def add_to_KB_from_clause(self, clause):

        pass

    def question_type(self, question):
        return QuestionType.TF_question

    def answer_question(self, question):
        pass

    def add_entity(self, name):
        # create entity if doesn't already exists
        pass

    def add_entity_class(self, name, attribute_set):
        # create class if it doesn't already exist
        # if a class exists with a subset of these attributes, we use that as the base class and add on the remaining attributes 
        pass

    def add_attributes_to_entity(self, attribute_set, entity):
        entity.add_attributes(attribute_set)
        for attribute in attribute_set:
            pass
            ## if attr doesn't exist, create it. self.attributes.add(Attr)
            ## create a predicate Attr(entity) and add to KB

    ## add more functions to interact with below objects


### PRIVATE : can only interact with following objects through functions in above parser (add more functions above ^ if needed) ###
    
class Statement():
    pass

class PredicateRelation(Statement):
    # child predicate(s)
    # relation: None, Negation, Implication (implication can have a list of predicates on either side representing conjunction?? What about disjunction)
    pass

class EntityRelation(Statement):
    pass

class Predicate(): 
    def __init__(self, name, attributes, subject, direct_obj, indirect_obj):
        self.name = name
        self.attributes = attributes
        self.subject = subject
        self.direct_obj = direct_obj
        self.indirect_obj = indirect_obj
    # given a verb, say, Shop, and a subject, Zach, and maybe modifiers, slowly, we make a predicate which is equivalent to the knowledge that Zach shops slowly. This gives us the ability to automatically have Zach shops because the modifiers don't need to be checked.


class Verb(): # this won't be a predicate/statement, just the verb: like Shop
    def __init__(self, name):
        self.name = name

class Attribute(): # again, not a statement or a predicate, just 'Blue'
    def __init__(self, name):
        self.name = name

class EntityClass():
    def __init__(self, name, base_class, attribute_set):
        self.name = name
        if base_class == None:
            self.name = name
            # assert(attribute_set == None)
            self.attributes = None # base class doesn't have attributes
        else:
            self.base_class = base_class
            self.attribute_set = attribute_set


class Entity():
    def __init__(self, name, entity_type):
        self.name = name
        self.attributes = set()
        self.entity_type = entity_type ## can be None

    def add_attributes(self, name, attribute_set):
        for attribute in attribute_set:
            self.attributes.add(attribute) # ...


if __name__ == '__main__':
    import stanza

    config = {
        'processors': 'tokenize,pos,lemma,depparse',
        'lang': 'en',
    }
    nlp = stanza.Pipeline(**config)

    string = "The Old Kingdom is the period in the third millennium also known as the 'Age of the Pyramids' or 'Age of the Pyramid Builders' as it includes the great 4th Dynasty when King Sneferu perfected the art of pyramid building and the pyramids of Giza were constructed under the kings Khufu, Khafre, and Menkaure."
    # string = "I sold megan a gun."
    fol_parser = FOLParser(nlp)
    fol_parser.add_to_KB_from_text(string)
