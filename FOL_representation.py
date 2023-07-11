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
import spacy
import stanza
import warnings
warnings.filterwarnings("ignore", message=r"\[W008\]", category=UserWarning)
warnings.filterwarnings("ignore")

import io

config = {
    'verbose':False, 'processors': 'tokenize,pos,lemma,depparse',
    'lang': 'en',
}
nlp = stanza.Pipeline(**config)
nlp_spacy = spacy.load('en_core_web_lg')


def sentence_similarity(question, file):

    q = nlp_spacy(question)
    best_sent = ""
    max = -1
    for sent in file.sents:
        score = sent.similarity(q)
        if (score > max):
            max = score
            best_sent = sent
    # print(max, best_sent)
    subject = [tok for tok in best_sent if (tok.dep_ == "nsubj")]
    return subject[0]

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
        self.file = None
        self.KB = (rules, self.facts)
        self.question_mode = False

    def is_a_child_subj(self, sent, id):
        # THIS ID IS A VERB BECAUSE IS HAS DEPENDENTS LIKE A VERB
        for word in sent.words:
            if word.head == id and (word.deprel in ["obl"] or
                                    "obj" in word.deprel):
                return True
        return False
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
            if sent.words[id - 1].xpos == "POS":
                string = string[:-1] + sent.words[id - 1].text + " "
            else:
                string += sent.words[id - 1].text + " "
        return string[:-1]

    def get_name(self, sent, id):
        string = ""
        for word in sent.words:
            if word.id == id:
                string += word.text + " "
            if word.head == id and word.deprel in ["compound", "det", "amod",
                                                   "case", "advmod", "flat",
                                                   "nummod"]:
                if word.xpos == "POS":
                    string = string[:-1] + word.text + " "
                else:
                    string += word.text + " "
            if word.head == id and word.xpos in ["HYPH"]:
                string = string[:-1] + word.text
            if word.head == id and word.deprel in ["nmod", "nmod:poss"]:
                string += self.get_name(sent, word.id) + " "
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
            if word.head == id and (word.deprel in ["nmod", "appos",
                                                    "nummod", "advmod"]
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
        # PREVIOUSLY CHECKED IF VERB
        #if self.is_a_child_subj(sent,word.id):
        #    print("VERB:", word.text)
        #    obj = self.generate_predicate(sent, id)
        #    return obj


        # TODO
        # Determine if it is a List
        if True:
            if entity_list == None:  ## equivalent to "not in_list"
                is_list = False
                temp_list = []
                conj = "and"
                for word in sent.words:
                    if word.id == id:
                        temp_list.append(word.id)
                    if word.head == id and word.deprel == "conj" and \
                            not self.is_a_child_subj(sent, word.id):
                        # print(word.text, self.is_a_child_subj(sent, word.id))
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
                    if not self.question_mode:
                        self.facts.add(obj)
                        self.list_of_entity_lists.append(entity_list)
                    return obj

            # Determine Definiteness

            definite = self.is_definite(sent, id)
            name = self.get_name(sent, id)
            #print("NAME: ", name)
            attribute_list = self.get_attributes(sent, id)
            modifier = self.get_modifier(sent, id)
            if definite:
                blank = False
                if (sent.words[id - 1].xpos == "WP"):
                    blank = True
                obj = Entity(name, attribute_list, entity_list, modifier, blank)
                if not self.question_mode:
                    self.set_of_entities.add(obj)
            else:
                obj = EntityClass(name, attribute_list, entity_list, modifier)
                if not self.question_mode:
                    self.set_of_entities.add(obj)

            for attribute in attribute_list:
                fact = (Attribute(attribute, obj))
                if not self.question_mode:
                    self.set_of_attrs.add(fact)
                    self.facts.add(fact)
            return obj

    def generate_predicate(self, sentence, id):
        verb, subj_id, obj_id, iobj_id, obl_id_list = \
            self.get_id_verb(sentence, id)

        obl_list = []
        if obl_id_list == []:
            obl_id_list.append(None)

        for obl_id in obl_id_list:
            subj = self.generate_entity(sentence, subj_id)
            obj = self.generate_entity(sentence, obj_id)
            iobj = self.generate_entity(sentence, iobj_id)
            obl = self.generate_entity(sentence, obl_id)


            # Create Predicate
            attribute_list = self.get_attributes(sentence, id)
            pred = Predicate(verb, attribute_list, subj, obj, iobj, obl)
            obl_list.append(pred)
            if not self.question_mode:
                self.set_of_predicates.add(pred)

        for i in range(len(obl_id_list)):
            for j in range(i+1, len(obl_id_list)):
                rel = Relation(RelationType.Equivalent, obl_list[i],
                               obl_list[j])
                if not self.question_mode:
                    self.set_of_relations.add(rel)
        """
        for obl_id in obl_id_list:
            obl = self.generate_entity(sentence, obl_id)
            id_list = self.get_subtree(sentence, obl_id)
            word = self.get_name_from_id_list(sentence, id_list)
            fact = Attribute(word, pred, attribute_type=AttributeType.Obl) # Note
            self.set_of_attrs.add(fact)
            pred.attributes.append(fact)
            self.facts.add(fact)
        """
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
        self.file = nlp_spacy(text)
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
                if (self.is_a_child_subj(sentence, word.id)):
                    ids_of_verbs.append(word.id)
            if word.lemma == "be":
                # if word.deprel == "cop":
                ids_of_cops.append(word.id)

        # PARSE THE COPULAS
        for id in ids_of_cops:
            lhs_id, rhs_id = self.get_id_cop(sentence, id)
            #print(sentence.text, sentence.words[lhs_id-1].text,
            #      sentence.words[rhs_id - 1].text)

            #if sentence.words[lhs_id - 1].upos == "VERB": FIXME
            if self.is_a_child_subj(sentence, lhs_id):
                lhs = self.generate_predicate(sentence, lhs_id)
            else:
                lhs = self.generate_entity(sentence, lhs_id)
            # either generates class or obj
            # if sentence.words[rhs_id - 1].upos in "VERB": FIXME
            if self.is_a_child_subj(sentence, rhs_id):
                rhs = self.generate_predicate(sentence, rhs_id)
            else:
                rhs = self.generate_entity(sentence, rhs_id)  #
            # Create Relation
            # print("REL", lhs, rhs)
            rel = Relation(RelationType.Equivalent, lhs, rhs)
            if not self.question_mode:
                self.set_of_relations.add(rel)
                self.facts.add(rel)

        # PARSE THE VERBS
        for id in ids_of_verbs:
            rel = self.generate_predicate(sentence, id)

            # TODO RELATION FOR VERBS
        if self.question_mode:
            return rel

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

    def question_type(self, sent):
        # TODO: figure out which kind of question it is
        for word in sent.words:
            if word.xpos == "WP":
                return QuestionType.Wh_question

        return QuestionType.TF_question
    def has_negation(self, sent):
        for word in sent.words:
            if word.lemma == "not":
                return True
        return False
    def answer_question(self, question_string):
        self.question_mode = True
        text = self.preprocess_text(question_string)
        document = self.nlp(text)
        sentence = document.sentences[0]

        print(sentence, question_string)
        parsed_question = self.parse_sentence(sentence, True)
        if self.question_type(sentence) == QuestionType.TF_question:
            if self.statement_entailed_by_KB(parsed_question):
                return "True"
            else:
                if (self.has_negation(sentence)):
                    return "False"
                return "True"
        else:

            obtype = ObjectType.Entity
            # fill_in_the_blank_type = None
            ## TODO: update above two variables by checking where the 'Wh' word is in the question
            answer = self.fill_in_the_blank(parsed_question, obtype, question_string)
            return (self.capitalize_first_letter(answer.user_string())).strip() ## capitalize first letter when returning if not alr capitalized


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

        # assert (statement.object_type() == ObjectType.Relation)
        # relation_type = statement.rel_type
        """
        for relation in self.set_of_relations:
            if relation == statement:
                return True

        for relation in self.set_of_predicates:
            if relation == statement:
                return True

        for relation in self.set_of_attrs:
            if relation == statement:
                return True
        """
        return False
        # if relation_type == RelationType.Implication:
        #     pass
        #     ##
        # elif relation_type == RelationType.No_Relation:
        #     pass

        # elif relation_type == RelationType.Negation:
        #     pass

    # for wh- questions

    def fill_in_the_blank(self, incomplete_statement, obtype, string):
        """

    def fill_in_the_blank(self, incomplete_statement, obtype,
                          fill_in_the_blank_type):
    >>>>>>> 3c15ba4fa7e8a4eaad1c62f6c1b68eacd415b228`
        options = self.get_options(obtype)
        for option in options:
            ## for entities, try entity lists too.
            ## entity_lists get preference over entities if both satisfy the statement
            complete_statement = self.fill_predicate(option,
                                                     fill_in_the_blank_type,
                                                     incomplete_statement)
            if self.statement_entailed_by_KB(complete_statement):
                return option

        """
        return sentence_similarity(string, self.file)
    # fills a predicate with a blank/blanks with the given object 
    def fill_predicate(self, option, incomplete_statement):
        if incomplete_statement.object_type() == ObjectType.Attribute:
            if incomplete_statement.entity.blank:
                incomplete_statement.entity = option
            return incomplete_statement
        elif incomplete_statement.object_type() == ObjectType.Predicate:
            if incomplete_statement.subject.blank:
                incomplete_statement.subject = option
            elif incomplete_statement.direct_obj.blank:
                incomplete_statement.direct_obj = option
            elif incomplete_statement.indirect_obj.blank:
                incomplete_statement.indirect_obj = option
            return incomplete_statement
        # elif incomplete_statement.object_type() == ObjectType.Relation:
        #     return

        ## TODO: create a new statement 
        # return X


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
            return (self.rel_type.to_string() + " " + self.LHS.user_string()).strip()
        return (self.LHS.user_string() + " " + self.rel_type.to_string() + " " + self.RHS.user_string()).strip()

    def make_copy(self):
        return Relation(self.rel_type, self.LHS, self.RHS)

    def __eq__(self, other):
        """
        otherL = nlp_spacy(other.LHS.name)
        otherR = nlp_spacy(other.RHS.name)

        currentL = nlp_spacy(self.LHS.name)
        currentR = nlp_spacy(self.RHS.name)
        score1 = otherL.similarity(currentL) > 0.97
        score2 = otherR.similarity(currentR) > 0.97
        if score1 and score2:
            return True
        score1 = otherR.similarity(currentL) > 0.97
        score2 = otherL.similarity(currentR) > 0.97
        """
        if (other.LHS.name == self.LHS.name and
            other.RHS.name == self.LHS.name):
            return True
        if (other.RHS.name == self.LHS.name and
            other.LHS.name == self.RHS.name):
            return True
        return False

class Predicate():
    def __init__(self, name, attributes, subject, obj, iobj, obl, blank=False):
        self.name = name.lemma
        self.name_lemma = name
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
            (self.name.lower(), str(self.subject), str(self.direct_obj),
             str(self.indirect_obj), str(self.obl)))

    def __str__(self):
        return self.name + "(" + str(self.subject) + ", " + str(
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

        string = ""
        for ent in self.entity_list:
            string += str(ent) + " " + self.conj + " "
        self.name = string[:-len(self.conj) - 2]

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


fol_parser = FOLParser(nlp)


if __name__ == '__main__':
    """
    import stanza
    import io

    config = {
        'processors': 'tokenize,pos,lemma,depparse',
        'lang': 'en',
    }
    nlp = stanza.Pipeline(**config)


    fol_parser = FOLParser(nlp)

    f = open("NLP_PROJ/set5/a1.txt", "r", encoding="utf-8")
    # string = "largest known dog is an English Mastiff."
    fol_parser.add_to_KB_from_text(f.read())
    # fol_parser.add_to_KB_from_text(string)
    f.close()

    print(fol_parser.answer_question("Is the largest known dog an English "
                                     "Mastiff?"))
    """
    import sys
    input_file = sys.argv[1]
    question_file = sys.argv[2]


    f = open(file=input_file, encoding="utf-8", mode="r+")
    string = f.read()
    fol_parser.add_to_KB_from_text(string)


    q = open(file=question_file, encoding="utf-8", mode="r+")
    spacy_doc = nlp_spacy(q.read())
    count = 0

    for question in spacy_doc.sents:
        print(question.text)
        answer = fol_parser.answer_question(question.text)
        print()

    f.close()
    q.close()