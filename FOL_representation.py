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
    
    def __init__(self): 
        # rules and facts are sets of statements
        rules = {} # we will manually import this from another file
        facts = {} 
        self.set_of_attrs = {}
        self.set_of_entities = {}
        self.set_of_predicates = {}
        self.set_of_entity_relations = {}
        self.set_of_predicate_relatoins = {}
        self.self_of_entity_classes = {}
        self.set_of_verbs = {}
        self.KB = (rules, facts)

    def add_to_KB_from_text(self, text):
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
     
    # given a verb, say, Shop, and a subject, Zach, and maybe modifiers, slowly, we make a predicate which is equivalent to the knowledge that Zach shops slowly. This gives us the ability to automatically have Zach shops because the modifiers don't need to be checked.
    pass

class Verb(): # this won't be a predicate/statement, just the verb: like Shop
    pass

class Attribute(): # again, not a statement or a predicate, just 'Blue'
    pass

class EntityClass():

    def __init__(self, name, base_class, attribute_set):
        self.name = name
        if base_class == None:
            self.name = name
            assert(attribute_set == None)
            self.attributes = None # base class doesn't have attributes
        else:
            self.base_class = base_class
            self.attribute_set = attribute_set


class Entity():
    def __init__(self, name, entity_type):
        self.name = name
        self.attributes = {}
        self.entity_type = entity_type ## can be None

    def add_attributes(self, name, attribute_set):
        self.attributes.add() # ...



