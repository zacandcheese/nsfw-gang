## class names are in camel case, starting with capital letters, function and variable names in snake case, starting with small letters

## do we want to introduce the concept of a predicate list with conjunctions? To allow for multiple predicates on either side of an implication: if you're Fat and you're Blue => you're from Mars

## since we removed the Verb class, do we want to classify verbs as entities?? If we get something like Efe likes cycling do we want it to be Likes(Efe, Cycling)?

## TODO: modify user_string function of all objects if needed (we will use these as the surface form of our answers)

## TODO: in generate_entity if entity alr exists, we don't want to add it again, add _eq_ functions to entities, coref resolution to replace all linked stuff with the same string? 

## are we assuming that questions have one clause? They might have relative clauses

## Is the 'word' argument in attribute a string? If so, change to .lower() in hash function

## make an almost equal function for entities and stuff?

## TODO: Seperate lists and entities (Look if the verb has a subj)
## TODO: Integerate Add To KB Into Parse Sentence

### ENUM CLASSES ###

import enum
import re


class ConjunctionType(enum.Enum):
    And = 0
    Or = 1

    def to_string(self):
        if self.value == ConjunctionType.And:
            return "and"
        elif self.value == ConjunctionType.Or:
            return "or"

class AttributeType(enum.Enum):
    Adj = 0
    Obl = 1

class ObjectType(enum.Enum):
    Entity = 0
    EntityList = 1
    Predicate = 2
    Relation = 3
    Attribute = 4
    EntityClass = 5


class FillInTheBlankType(enum.Enum):
    pass


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


class RelationType(enum.Enum):
    No_Relation = 0
    Equivalent = 1
    Implication = 2
    Member_Of = 3
    # Hypernymn = 4
    Hyponymn = 5  # don't need hypernym if we have hyponym?? as they are redundant
    Negation = 5

    def to_string(self):
        if self.value == RelationType.No_Relation:
            return ""
        elif self.value == RelationType.Negation:
            return "not"  ##??
        elif self.value == RelationType.Implication:
            return "implies"
        elif self.value == RelationType.Equivalent:
            return "equivalent"
        elif self.value == RelationType.Member_Of:
            return "is a member of"
        elif self.value == RelationType.Hyponym:
            return "is a hyponym of"


### PUBLIC ###

class FOLParser():
    def __init__(self, parser):
        # rules and facts are sets of statements
        self.nlp = parser
        rules = set()  # we will manually import this from another file
        self.facts = set()
        self.set_of_attrs = set()
        self.set_of_entities = set()
        self.self_of_entity_classes = set()
        self.set_of_predicates = set()
        self.set_of_relations = set()
        self.list_of_entity_lists = []

        self.KB = (rules, self.facts)

    def get_subj(self, sent, id, child=True):

        lhs_id = None
        lhs_word = None
        for word in sent.words:
            if word.head == id and ("subj" in word.deprel or
                                    "expl" in word.deprel):
                lhs_id = word.id
                lhs_word = word

        if child:
            if lhs_word == None or lhs_word.upos == "PRON":
                temp_id = sent.words[id - 1].head
                if (temp_id != 0):
                    if (sent.words[id - 1].deprel == "conj"):
                        lhs_id, lhs_word = self.get_subj(sent, temp_id,
                                                         child=True)
                    else:
                        lhs_id = temp_id
                        lhs_word = sent.words[lhs_id - 1]

        return lhs_id, lhs_word

    def get_id_cop(self, sent, id):
        # Need to return the ids of the head of the right/left sides
        lhs_id = None
        lhs_word = None
        cop = None
        for word in sent.words:
            if word.id == id:
                cop = word

        lhs_id, lhs_word = self.get_subj(sent, cop.head)
        # if lhs_word.upos == "PRON":
        #    temp_id = sent.words[cop.head - 1].head
        #    lhs_id, _ = self.get_id_cop(sent, temp_id)

        rhs_id = sent.words[cop.head - 1].id
        return lhs_id, rhs_id

    def get_id_verb(self, sent, id):
        verb = None
        obj = None
        iobj = None
        obl = []
        subj, _ = self.get_subj(sent, id)
        for word in sent.words:
            if word.id == id:
                verb = word
            if word.head == id and "subj" in word.deprel:
                pass
            elif word.head == id and "iobj" in word.deprel:
                iobj = word.id
            elif word.head == id and "obj" in word.deprel:
                obj = word.id
            elif word.head == id and ("obl" in word.deprel or
                                      "xcomp" in word.deprel):
                obl.append(word.id)
        return verb, subj, obj, iobj, obl

    def is_definite(self, sent, id):
        for word in sent.words:
            if word.head == id and word.lemma in ["a", "an"]:
                return False
        return True

    def get_subtree(self, sent, id):
        id_list = []
        for word in sent.words:
            if word.head == id and word.deprel != "conj":
                id_list.extend(self.get_subtree(sent, word.id))
        id_list.append(id)
        return id_list
    def get_name_from_id_list(self, sent, id_list):
        id_list = list(set(id_list))
        string = ""
        for id in id_list:
            string += sent.words[id - 1].text + " "
        return string[:-1]

    def get_name(self, sent, id):
        string = ""
        for word in sent.words:
            if word.id == id:
                string += word.text + " "
            if word.head == id and word.deprel in ["compound", "det", "amod",
                                                   "case, advmod"]:
                string += word.text + " "
        return string[:-1]

    def get_attributes(self, sent, id):
        attribute_list = []
        for word in sent.words:
            if word.head == id and word.deprel in ["compound", "amod",
                                                   "advmod"]:
                attribute_list.append(word)
        return attribute_list

    def get_modifier(self, sent, id):
        nmod = None
        for word in sent.words:
            if word.head == id and (word.deprel in ["nmod", "appos", "nummod"]
                                    or "relcl" in word.deprel):
                nmod = word
                break #FIXME I was added in post, unsure if I should be removed

        if nmod is not None:
            if "relcl" in nmod.deprel:
                id_list = self.get_subtree(sent, nmod.id)
                return self.get_name_from_id_list(sent, id_list)
            return self.get_name(sent, nmod.id)
        else:
            return ""

    def generate_entity(self, sent, id, entity_list=None):
        if id is None:
            return None
        # Determine if it is an Entity
        word = sent.words[id - 1]
        if (word.upos == "VERB"):  # and  #("cl" in word.deprel or
            # PREDICATE                 #"conj" == word.deprel or
            # "root" == word.deprel)):
            name = self.get_name(sent, id)
            attribute_list = self.get_attributes(sent, id)
            modifier = self.get_modifier(sent, id)
            obj = Verb(name, attribute_list, None, modifier)
            self.facts.add(obj)
            self.list_of_entity_lists.append(obj)
            return obj


        # TODO
        # Determine if it is a List
        else:
            if entity_list == None:  ## equivalent to "not in_list"
                is_list = False
                temp_list = []
                conj = "and"
                for word in sent.words:
                    if word.id == id:
                        temp_list.append(word.id)
                    if word.head == id and word.deprel == "conj":
                        is_list = True
                        temp_list.append(word.id)
                    if word.head == id and word.deprel == "cc":
                        conj = word.text

                if is_list:
                    entity_list = []
                    obj = EntityList(conj, entity_list)
                    for temp_id in temp_list:
                        entity_list.append(
                            self.generate_entity(sent, temp_id, obj))
                    # Create Entity List
                    self.facts.add(obj)
                    self.list_of_entity_lists.append(entity_list)
                    return obj

            # Determine Definiteness

            definite = self.is_definite(sent, id)
            name = self.get_name(sent, id)
            attribute_list = self.get_attributes(sent, id)
            modifier = self.get_modifier(sent, id)
            if definite:
                blank = False
                if (sent.words[id - 1].xpos == "WP"):
                    blank = True
                obj = Entity(name, attribute_list, entity_list, modifier, blank)
                self.set_of_entities.add(obj)
            else:
                obj = EntityClass(name, attribute_list, entity_list, modifier)
                self.set_of_entities.add(obj)

            for attribute in attribute_list:
                fact = (Attribute(attribute, obj))
                self.set_of_attrs.add(fact)
                self.facts.add(fact)
            return obj

    def generate_predicate(self, sentence, id):
        verb, subj_id, obj_id, iobj_id, obl_id_list = \
            self.get_id_verb(sentence, id)

        obl_list = []


        subj = self.generate_entity(sentence, subj_id)
        obj = self.generate_entity(sentence, obj_id)
        iobj = self.generate_entity(sentence, iobj_id)

        # Create Predicate
        attribute_list = self.get_attributes(sentence, id)
        pred = Predicate(verb, attribute_list, subj, obj, iobj, None)
        self.set_of_predicates.add(pred)

        for obl_id in obl_id_list:
            obl = self.generate_entity(sentence, obl_id)
            id_list = self.get_subtree(sentence, obl_id)
            word = self.get_name_from_id_list(sentence, id_list)
            fact = Attribute(word, pred, attribute_type=AttributeType.Obl) # Note
            self.set_of_attrs.add(fact)
            pred.attributes.append(fact)
            self.facts.add(fact)

        return pred

    def preprocess_text(self, string):
        try:
            (start, stop) = (re.search("See also", string)).span()
            string = string[:start]
        except AttributeError:
            try:
                (start, stop) = (re.search("References", string)).span()
                string = string[:start]
            except AttributeError:
                pass

        string = re.sub("\([^()]*\)", "", string)  # Remove Parenthesis Asides

        return string

    def add_to_KB_from_text(self, text):
        text = self.preprocess_text(text)
        document = self.nlp(text)
        # deplacy.render(document)

        for sentence in document.sentences:
            self.parse_sentence(sentence, True)

    def parse_sentence(self, sentence, add_to_KB=False):
        # Break down sentence into clauses #
        # get set ids for heads of clauses
        ids_of_verbs = []
        ids_of_cops = []
        for word in sentence.words:
            if word.upos == "VERB" and \
                    ("cl" in word.deprel or "conj" == word.deprel or "root"
                     == word.deprel):
                ids_of_verbs.append(word.id)
            if word.lemma == "be":
            # if word.deprel == "cop":
                ids_of_cops.append(word.id)

        # PARSE THE COPULAS
        for id in ids_of_cops:
            lhs_id, rhs_id = self.get_id_cop(sentence, id)
            print(sentence.text, lhs_id, sentence.words[rhs_id - 1].text)
            if sentence.words[lhs_id - 1].upos == "VERB":
                lhs = self.generate_predicate(sentence, lhs_id)
            else:
                lhs = self.generate_entity(sentence, lhs_id)
            # either generates class or obj
            if sentence.words[rhs_id - 1].upos == "VERB":
                rhs = self.generate_predicate(sentence, rhs_id)
            else:
                rhs = self.generate_entity(sentence, rhs_id)  #
            # Create Relation
            rel = Relation(RelationType.Equivalent, lhs, rhs)
            if add_to_KB:
                self.set_of_relations.add(rel)
                self.facts.add(rel)

        # PARSE THE VERBS
        for id in ids_of_verbs:
            self.generate_predicate(sentence, id)

            # TODO RELATION FOR VERBS

        list_of_objects = None
        return list_of_objects

    def get_options(self, obtype):
        if obtype == ObjectType.Attribute:
            return self.set_of_attrs
        elif obtype == ObjectType.Entity:
            return self.set_of_entities
        elif obtype == ObjectType.EntityList:
            return self.list_of_entity_lists
        elif obtype == ObjectType.Predicate:
            return self.set_of_predicates
        elif obtype == ObjectType.Relation:
            return self.set_of_relations
        elif obtype == ObjectType.EntityClass:
            return self.self_of_entity_classes

    def question_type(self, parsed_question, question_string):
        # TODO: figure out which kind of question it is
        return QuestionType.TF_question

    def answer_question(self, question_string):
        parsed_question = self.parse_sentence(question_string)
        if self.question_type(parsed_question,
                              question_string) == QuestionType.TF_question:
            if self.statement_entailed_by_KB(parsed_question):
                return "True"
            else:
                return "False"
        else:
            obtype = None
            fill_in_the_blank_type = None
            ## TODO: update above two variables by checking where the 'Wh' word is in the question
            answer = self.fill_in_the_blank(parsed_question, obtype,
                                            fill_in_the_blank_type)
            return (self.capitalize_first_letter(
                answer.user_string())).strip()  ## capitalize first letter when returning if not alr capitalized

    def capitalize_first_letter(self, s):
        if s == "":
            return s
        else:
            return s[0].upper() + s[1:]

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
            attribute  # to delete
            pass
            ## if attr doesn't exist, create it. self.attributes.add(Attr)
            ## create a predicate Attr(entity) and add to KB

    # for true false questions
    def statement_entailed_by_KB(self, statement):
        assert (statement.object_type() == ObjectType.Relation)
        # relation_type = statement.rel_type
        for relation in self.set_of_relations:
            if relation == statement:
                return True
        return False
        # if relation_type == RelationType.Implication:
        #     pass
        #     ## 
        # elif relation_type == RelationType.No_Relation:
        #     pass

        # elif relation_type == RelationType.Negation:
        #     pass

    # for wh- questions
    def fill_in_the_blank(self, incomplete_statement, obtype,
                          fill_in_the_blank_type):
        options = self.get_options(obtype)
        for option in options:
            ## for entities, try entity lists too.  
            ## entity_lists get preference over entities if both satisfy the statement
            complete_statement = self.fill_predicate(option,
                                                     fill_in_the_blank_type,
                                                     incomplete_statement)
            if self.statement_entailed_by_KB(complete_statement):
                return option

    # fills a predicate with a blank/blanks with the given object 
    def fill_predicate(self, option, fill_in_the_blank_type,
                       incomplete_statement):
        X = incomplete_statement
        ## TODO: create a new statement 
        return X

    def generate_all_questions(self):
        ## TODO: link this to Mehul + Efe's code
        return []

    # tells you which question is better or if they're the same
    def compare_questions(self, question1, question2):
        ## TODO: implement using depth (chaining depth) and other factors
        pass

    def generate_n_best_questions(self, n):
        questions = self.generate_all_questions()
        ## TODO: sort the list using compare_questions
        return questions[:n]

    ## add more functions to interact with below objects


### PRIVATE : can only interact with following objects through functions in above parser (add more functions above ^ if needed) ###

class Relation():
    def __init__(self, rel, LHS, RHS=None, blank=False):
        # RESTRICT TYPE
        self.rel_type = rel
        self.LHS = LHS
        self.RHS = RHS

    def object_type(self):
        return ObjectType.Relation

    def __hash__(self):
        return hash((self.rel_type, self.LHS, self.RHS))

    def __str__(self):
        if self.rel_type == RelationType.No_Relation:
            return str(self.LHS)
        elif self.rel_type == RelationType.Equivalent:
            return str(self.LHS) + " <==> " + str(self.RHS)
        elif self.rel_type == RelationType.Implication:
            return str(self.LHS) + " ==> " + str(self.RHS)
        elif self.rel_type == RelationType.Member_Of:
            return str(self.LHS) + " is a member of " + str(self.RHS)
        elif self.rel_type == RelationType.Hyponymn:
            return str(self.LHS) + " is a hyponym of " + str(self.RHS)
        else:
            assert (False and "not a valid relation type")

    def user_string(self):
        if self.RHS == None:
            return (
                        self.rel_type.to_string() + " " + self.LHS.user_string()).strip()
        return (
                    self.LHS.user_string() + " " + self.rel_type.to_string() + " " + self.RHS.user_string()).strip()

    def make_copy(self):
        return Relation(self.rel_type, self.LHS, self.RHS)


class Predicate():
    def __init__(self, name, attributes, subject, obj, iobj, obl, blank=False):
        self.name = name
        self.name_lemma = name.lemma
        self.meta_data = name.feats
        self.attributes = attributes
        self.subject = subject
        self.direct_obj = obj
        self.indirect_obj = iobj
        self.obl = obl
        self.blank = blank

    def object_type(self):
        return ObjectType.Predicate

    # given a verb, say, Shop, and a subject, Zach, and maybe modifiers, slowly, we make a predicate which is equivalent to the knowledge that Zach shops slowly. This gives us the ability to automatically have Zach shops because the modifiers don't need to be checked.
    def __hash__(self):
        return hash(
            (self.name_lemma.lower(), str(self.subject), str(self.direct_obj),
             str(self.indirect_obj), str(self.obl)))

    def __str__(self):
        return self.name_lemma + "(" + str(self.subject) + ", " + str(
            self.direct_obj) + ", " + str(self.indirect_obj) + ", " + str(
            self.obl) \
               + ")"

    def user_string(self):
        pass  # TODO: define. Need to conjugate the verb?

    def make_copy(self):
        return Predicate(self.name, self.attributes, self.subject,
                         self.direct_obj, self.indirect_obj, self.obl)


class Attribute():  # again, not a statement or a predicate, just 'Blue'
    def __init__(self, word, entity, attribute_type = AttributeType.Adj,
                 blank=False):
        self.word = word
        self.entity = entity
        self.blank = blank
        self.type = attribute_type
    def object_type(self):
        return ObjectType.Attribute

    def __hash__(self):
        if self.type == AttributeType.Adj:
            return hash((self.word, str(self.entity)))
        else:
            return hash((self.word, str(self.entity)))
    def __str__(self):
        if self.type == AttributeType.Adj:
            return self.word.lemma + "(" + str(self.entity) + ")"
        else:
            return self.word + "(" + str(self.entity) + ")"
    def make_copy(self):
        return Attribute(self.word, self.entity)


class Verb():
    def __init__(self, name, attribute_set, entity_class_list, modifiers,
                 blank=False):
        self.name = name
        self.attributes = attribute_set
        self.modifiers = modifiers
        self.entity_class_list = entity_class_list
        self.blank = blank

    def object_type(self):
        return ObjectType.Verb

    def __hash__(self):
        return hash((self.name.lower(), self.modifiers))

    def __str__(self):
        return self.name + "(" + self.modifiers + ")"

    def user_string(self):
        return self.name

    def make_copy(self):
        return Verb(self.name, self.attributes, self.entity_class_list,
                    self.modifiers)


class EntityClass():
    def __init__(self, name, attribute_set, entity_class_list, modifiers,
                 blank=False):
        self.name = name
        self.attributes = attribute_set
        self.modifiers = modifiers
        self.entity_class_list = entity_class_list
        self.blank = blank

    def object_type(self):
        return ObjectType.EntityClass

    def __hash__(self):
        return hash((self.name.lower(), self.modifiers))

    def __str__(self):
        return self.name + "(" + self.modifiers + ")"

    def user_string(self):
        return self.name

    def make_copy(self):
        return EntityClass(self.name, self.attributes, self.entity_class_list,
                           self.modifiers)


class Entity():
    def __init__(self, name, attribute_set, entity_list, modifiers,
                 blank=False):
        self.name = name
        self.attributes = attribute_set
        self.modifiers = modifiers
        self.entity_list = entity_list
        self.blank = blank

    def object_type(self):
        return ObjectType.Entity

    def __hash__(self):
        return hash(
            self.name.lower())  # for two entities to be equal, we don't need the attribute set, but for entity classes we do need the attributes

    def __str__(self):
        if self.blank:
            return self.name + "(TRUE)"
        return self.name + "(" + self.modifiers + ")"

    def user_string(self):
        return self.name

    def make_copy(self):
        return Entity(self.name, self.attributes, self.entity_list,
                      self.modifiers)

class EntityList():
    def __init__(self, conj, entity_set, blank=False):
        self.conj = conj
        self.entity_list = entity_set
        self.blank = blank

    def object_type(self):
        return ObjectType.EntityList

    def __hash__(self):
        string = ""
        for ent in self.entity_list:
            string += " " + str(ent)
        return hash((self.conj.lower(), string))

    def __str__(self):
        string = ""
        for ent in self.entity_list:
            string += str(ent) + " " + self.conj + " "
        return string[:-len(self.conj) - 2]

    def user_string(self):
        result = ""
        for i in range(len(self.entity_list)):
            entity = self.entity_list[i]
            if i == len(self.entity_list) - 1:
                result += self.conj.to_string() + " " + entity.user_string
            else:
                result += entity.user_string + ", "

    def make_copy(self):
        return EntityList(self.conj, self.entity_list)


if __name__ == '__main__':
    import stanza
    import io

    config = {
        'processors': 'tokenize,pos,lemma,depparse',
        'lang': 'en',
    }
    nlp = stanza.Pipeline(**config)

    string = "The Old Kingdom is the period in the third millennium also known as the 'Age of the Pyramids' or 'Age of the Pyramid Builders' as it includes the great 4th Dynasty when King Sneferu perfected the art of pyramid building and the pyramids of Giza were constructed under the kings Khufu, Khafre, and Menkaure."
    # string = "Zach is happy and Zach is sad."
    # string = "An adult female dog is a bitch."
    string = "In 1758, the taxonomist Linnaeus published in his Systema Naturae the classification of species."
    # string = "To these ends, over a period of time, Egyptian artists adopted a limited repertoire of standard types and established a formal artistic canon that would define Egyptian art for more than 3,000 years, while remaining flexible enough to allow for subtle variation and innovation."
    # string = "I like to run."
    # string = "He passed the data from the server to the client."
    """
    string = "There were military expeditions into Canaan and Nubia, with Egyptian influence reaching up the Nile into what is today the Sudan."
    string = "The largest known dog was an English Mastiff which weighed 155.6 kg and was 250 cm from the snout to the tail"
    """
    # string = "Happy Doug is happy. Sad Doug is sad. Who is sad?"
    fol_parser = FOLParser(nlp)

    f = open("NLP_PROJ/set1/a1.txt", "r", encoding="utf-8")
    fol_parser.add_to_KB_from_text(f.read())
    # fol_parser.add_to_KB_from_text(string)
    f.close()
    print("\nentities are\n")
    for ent in fol_parser.set_of_entities:
        print(ent, type(ent))

    print("\npredicates are\n")
    for ent in fol_parser.set_of_predicates:
        print(ent)

    print("\nattributes are\n")
    for ent in fol_parser.set_of_attrs:
        print(ent)

    print("\nrelations are\n")
    for ent in fol_parser.set_of_relations:
        print(ent)

    print("\nchaining\n")
    # given a relation object, we can tell if it's entailed by the KB
    # now we just need to create a relation object out of a question string
    """
    for rel in fol_parser.set_of_relations:
        print("relation is ", rel)
        print(fol_parser.statement_entailed_by_KB(rel))
        rel_copy = rel.make_copy()
        print("copy relation is ", rel_copy)
        for entity in fol_parser.set_of_entities:
            if rel_copy.LHS.object_type() == ObjectType.Predicate:
                rel_copy.LHS.subject = entity
                print("modified copy relation is ", rel_copy)
                print()
                print(fol_parser.statement_entailed_by_KB(rel_copy))
                print()
    """
