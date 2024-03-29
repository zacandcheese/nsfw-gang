#!/usr/bin/env python3
import stanza
import sys
from aima3.logic import expr
from aima3.logic import FolKB
import aima3.logic as aima
import num2words
import re
from collections import defaultdict

import os
import re


# stanza.download('en')
def get_subtree(sent, id):
    # RETURN A LIST OF IDS
    forThePhrase = []
    forTheFOL = []
    for word in sent.words:
        head = word.head
        if head == id:
            forThePhrase.append(word.id)
            if word.upos in ["ADJ", "NUM"]:
                forTheFOL.append(word.id)
    for new_id in forThePhrase:
        temp1, temp2 = get_subtree(sent, new_id)
        forTheFOL.extend(temp1)
        forThePhrase.extend(temp2)
    forTheFOL = list(set(forTheFOL))
    forThePhrase = list(set(forThePhrase))
    return forTheFOL, forThePhrase

def phrase_to_fol_string(phrase):
    #phrase = re.sub(r"[\']",'',phrase)
    phrase = re.sub(r"\W", '', phrase)
    phrase = re.sub("\"", "Quote", phrase)
    words = phrase.split(" ")
    final_set = []
    for word in words:
        try:
            word = num2words.num2words(int(word))
            temp_set = re.findall("[a-zA-Z]+", word)
            temp_set = list(map(lambda x: x.lower().capitalize(), temp_set))
            final_set.extend(temp_set)
        except ValueError:
            final_set.append(word.lower().capitalize())

    string = "".join(final_set)
    string = re.sub(r"\W", '', string)

    return string

def preprocess_string(string):
    try:
        (start, stop) = (re.search("See also", string)).span()
        string = string[:start]
    except AttributeError:
        pass

    string = re.sub("%", " percent", string)  # Modify Percents
    string = re.sub("\((.*?)\)", "", string)  # Remove Parenthesis Asides
    return string


def convert_dep_to_fol(sent):
    """

    Parameters
    ----------
    dep: One sentence's dependency tree.

    Returns: A fol
    -------

    """
    # Find root:
    roots = []
    for i, word in enumerate(sent.words):
        if word.deprel == 'root' or 'acl' in word.deprel:
            roots.append(word.text)


    clauses = []
    for root in roots:
        mod = None
        nsubj = None
        iobj = None
        obj = None

        for word in sent.words:
            head = sent.words[word.head - 1].text
            if (head == root):
                # Find mod
                if 'mod' in word.deprel:
                    mod = (word.text, word.id)

                # Find nsubj for root:
                if 'subj' in word.deprel:
                    nsubj = (word.text, word.id)

                # Find iobj for root:
                if (word.deprel == 'iobj'):
                    iobj = (word.text, word.id)

                # Find obj for root:
                if (word.deprel == 'obj'):
                    obj = (word.text, word.id)

        if (nsubj == None and iobj == None and obj == None):
            continue

        # Generate string for expr
        expr_str = ""
        root_intake_str = ""
        counter = 0
        for word in [mod, nsubj, iobj, obj]:
            if word != None:
                (word, i) = word
                variable = chr(ord('a') + counter)
                JJ = ""

                ################################
                #    GET THE JJ or MODIFIERS   #
                forFOL, forPhrase = (get_subtree(sent, i))
                forPhrase.append(i)
                forPhrase = list(set(forPhrase))
                # these are list of ids
                var = ""
                for idx in forPhrase:
                    var += phrase_to_fol_string(sent.words[idx - 1].text)
                for idx in forFOL:
                    temp = sent.words[idx - 1].text
                    FOLHEAD = phrase_to_fol_string(temp)
                    clauses.append(expr(FOLHEAD + "(" + var + ")"))
                    expr_str += FOLHEAD + "(" + variable + ") & "
                ################################
                wordVar = phrase_to_fol_string(word)
                clauses.append(expr(wordVar + "(" + var + ")"))
                expr_str += wordVar + "(" + variable + ") & "
                root_intake_str += variable + ", "
                counter += 1
            else:
                root_intake_str += "None, "
        root_intake_str = root_intake_str[:-2]
        rootVar = phrase_to_fol_string(root)
        expr_str = expr_str[:-2] + "==> " + rootVar + "(" + \
                   root_intake_str + ")"
        clauses.append(expr(expr_str))
    return clauses

def correct_tense (verb):
    return nlp(verb).sentences[0].words[0].lemma

def is_noun (verb):
    return (nlp(verb).sentences[0].words[0].upos == "NOUN")

def is_plural (subject):
    wordslist = nlp(subject).sentences[0].words
    if (len(wordslist) == 0):
        return False
    else:
        return (wordslist[len(wordslist) - 1].upos == "NOUN" and "Number=Plur" in wordslist[len(wordslist) - 1].feats)

def a_or_t (verb):
    if verb in ["capital"]:
        return "the"
    else:
        return "a"

def try_capitalize (nouni) :
    nouns = nouni.split()
    res = ""
    for noun in nouns:
        noun = noun.lower()
        if nlp(noun).sentences[0].words[0].upos == "PROPN":
            noun = noun.capitalize()
        res += " " + noun
    return res[1:]

def which_w (subject):
    entity = nlp(subject).sentences[0].tokens[0].ner
    if entity in ["S-PERSON", "S-NORP", "S-PER"]:
        return "Who"
    elif entity in ["S-GPE", "S-LOC", "S-LOCATION"]:
        return "Where"
    elif entity in ["S-DATE", "S-TIME"]:
        return "When"
    return "What"

def write_w_question (verb, subject_list, indirect_object_list, object_list, positive):

    questions = set()
    verb = try_capitalize(verb)

    
    if (len(object_list) == 0):
        # Is relationship

        if (len(mod_list) == 0):
            for subject in subject_list:
                subject = try_capitalize(subject)
                w = which_w(subject)

                plural = is_plural(verb)

                # What, who, where, when
                if plural:
                    if positive:
                        questions.add(w + " are " + verb + "?")
                    else:
                        questions.add(w + " are not " + verb + "?")
                else:
                    if positive:
                        questions.add(w + " is " + verb + "?")
                    else:
                        questions.add(w + " is not " + verb + "?")
        else:
            if mod_list[0] in ["Not", "Nt"]:
                for subject in subject_list:
                    subject = try_capitalize(subject)
                    w = which_w(subject)

                    plural = is_plural(verb)

                    # What, who, where, when
                    if plural:
                        if positive:
                            questions.add(w + " are " + verb + "?")
                        else:
                            questions.add(w + " are not " + verb + "?")
                    else:
                        if positive:
                            questions.add(w + " is " + verb + "?")
                        else:
                            questions.add(w + " is not " + verb + "?")
            else:
                for subject in subject_list:
                    subject = try_capitalize(subject)
                    w = which_w(subject)

                    plural = is_plural(verb)
                    mod_list[0] = try_capitalize(mod_list[0])


                    # What, who, where, when
                    if plural:
                        if positive:
                            questions.add(w + " are " + verb + " " + mod_list[0] + "?")
                        else:
                            questions.add(w + " are not " + verb + " " + mod_list[0] + "?")
                    else:
                        if positive:
                            questions.add(w + " is " + a_or_t(verb) + " " + verb + " " + mod_list[0] + "?")
                        else:
                            questions.add(w + " is not " + a_or_t(verb) + " " + verb + " " + mod_list[0] + "?")

    elif (len(indirect_object_list) == 0):
        # No indirect object
        for subject in subject_list:
            for objects in object_list:

                subject = try_capitalize(subject)
                objects = try_capitalize(objects)
                w = which_w(subject)

                if is_noun(verb):
                    # Noun verb
                    plural = is_plural(verb)
                    
                    if plural:
                        if positive:
                            questions.add(w + " are " + verb + " " + objects + "?")
                        else:
                            questions.add(w + " are not " + verb + " " + objects + "?")
                    else:
                        if positive:
                            questions.add(w + " is " + a_or_t(verb) + " " + verb + " " + objects + "?")
                        else:
                            questions.add(w + " is not " + a_or_t(verb) + " " + verb + " " + objects + "?")
                    
                else :
                    # Verb verb
                    if positive:
                        questions.add(w + " " + verb + " " + objects + "?")
                    else:
                        verb = correct_tense(verb)
                        questions.add(w + " doesn't " + verb + " " + objects + "?")

    else:
        # Indirect object
        for subject in subject_list:
            for objects in object_list:
                for indirect_object in indirect_object_list:

                    subject = try_capitalize(subject)
                    objects = try_capitalize(objects)
                    indirect_object = try_capitalize(indirect_object)
                    w = which_w(subject)

                    if positive:
                        questions.add(w + " " + verb + " " + indirect_object + " " + objects + "?")
                    else:
                        verb = correct_tense(verb)
                        questions.add(w + " doesn't " + verb + " " + indirect_object + " " + objects + "?")
    
    return questions

def write_question (verb, subject_list, indirect_object_list, object_list):

    questions = set()
    verb = try_capitalize(verb)

    if (len(object_list) == 0):
        # Is relationship
        if (len(mod_list) == 0):
            for subject in subject_list:
                plural = is_plural(subject)
                subject = try_capitalize(subject)

                if plural:
                    questions.add("Are " +  subject + " " + verb + "?")
                    questions.add("Are " +  subject + " not " + verb + "?")
                else:
                    questions.add("Is " +  subject + " " + verb + "?")
                    questions.add("Is " +  subject + " not " + verb + "?")
        else:
            if mod_list[0] in ["Not", "Nt"]:
                for subject in subject_list:
                    plural = is_plural(subject)
                    subject = try_capitalize(subject)
                    
                    if plural:
                        questions.add("Are " +  subject + " " + verb + "?")
                        questions.add("Are " +  subject + " not " + verb + "?")
                    else:
                        questions.add("Is " +  subject + " " + verb + "?")
                        questions.add("Is " +  subject + " not " + verb + "?")
            else:
                for subject in subject_list:
                    plural = is_plural(subject)
                    subject = try_capitalize(subject)
                    mod_list[0] = try_capitalize(mod_list[0])

                    
                    if plural:
                        questions.add("Are " +  subject + " " + a_or_t(verb) + " " + verb + " " + mod_list[0] + "?")
                        questions.add("Are " +  subject + " not " + a_or_t(verb) + " " + verb + " " + mod_list[0] + "?")
                    else:
                        questions.add("Is " +  subject + " " + a_or_t(verb) + " " + verb + " " + mod_list[0] + "?")
                        questions.add("Is " +  subject + " not " + a_or_t(verb) + " " + verb + " " + mod_list[0] + "?")

    elif (len(indirect_object_list) == 0):
        # No indirect object
        for subject in subject_list:
            for objects in object_list:
                plural = is_plural(subject)

                subject = try_capitalize(subject)
                objects = try_capitalize(objects)

                if is_noun(verb):
                    # Noun verb
                    if plural:
                        questions.add("Are " + subject + " " + verb + " " + objects + "?")
                        questions.add("Are " + subject + " not " + verb + " " + objects + "?")
                    else:
                        questions.add("Is " + subject + " " + a_or_t(verb) + " " + verb + " " + objects + "?")
                        questions.add("Is " + subject + " not " + a_or_t(verb) + " " + verb + " " + objects + "?")
                    
                else :
                    # Verb verb
                    verb = correct_tense(verb)
                    if plural:
                        questions.add("Do " + subject + " " + verb + " " + objects + "?")
                        questions.add("Do " + subject + " not " + verb + " " + objects + "?")
                    else:
                        questions.add("Does " + subject + " " + verb + " " + objects + "?")
                        questions.add("Does " + subject + " not " + verb + " " + objects + "?")

    else:
        # Indirect object
        for subject in subject_list:
            for objects in object_list:
                for indirect_object in indirect_object_list:

                    plural = is_plural(subject)
                    verb = correct_tense(verb)

                    subject = try_capitalize(subject)
                    objects = try_capitalize(objects)
                    indirect_object = try_capitalize(indirect_object)

                    if plural:
                        questions.add("Do " + subject + " " + verb + " " + indirect_object + " " + objects + "?")
                        questions.add("Do " + subject + " not " + verb + " " + indirect_object + " " + objects + "?")
                    else:
                        questions.add("Does " + subject + " " + verb + " " + indirect_object + " " + objects + "?")
                        questions.add("Does " + subject + " not " + verb + " " + indirect_object + " " + objects + "?")
    
    return questions


if __name__ == "__main__":

    nlp = stanza.Pipeline('en', processors= 'tokenize,pos,lemma,depparse,ner',verbose=False)

    f = open(file=sys.argv[1], encoding="utf-8", mode="r+")
    string = f.read()
    # DELETE ME IF YOU WANT TO TRY YOUR OWN PASSAGE #
    # string = "Pittsburgh is not the capital of Pennsylvania."
    string = preprocess_string(string)
    num_questions = int(sys.argv[2])

    doc = nlp(string)

    clauses = []
    for sent in doc.sentences:
        clauses.extend(convert_dep_to_fol(sent))
    #print(set(clauses))
    clauses = list(set(clauses))
    #print(clauses)
    kb = FolKB(clauses)

    #print(kb.ask_generator(expr("Property(a)")))

    # Extract list of just words word(mod)
    words = []
    str_words = []
    str_relationships = []
    relationships = []
    for clause in clauses:
        str_clause = str(clause)
        if (str_clause[0] != '('):
            words.append(clause)
            str_words.append(str_clause)
        else:
            relationships.append(words)
            str_relationships.append(str_clause[1:][:-1])
        

    #print(str_relationships)
    #print(words)
    
    # Make list of all [word, mod] (2d list)
    word_mod_list = []
    for item in str_words:
        for i in range(len(item)):
            if (item[i] == '('):
                word = item[:i]
                mod = item[(i+1):][:-1]
                mod_list = [s for s in re.split("([A-Z][^A-Z]*)", mod) if s]
                mod = " ".join(mod_list)
                word_mod_list.append([word, mod])
    
    #print(word_mod_list)

    word_dict = defaultdict(list)

    for i in range(len(word_mod_list)):
        word_dict[word_mod_list[i][0]].append(word_mod_list[i][1])

    #print(word_dict)
    final_questions = set()
    # For each relationship, get parameters
    for relationship in str_relationships:
        word_side = []
        verb_side = []
        breakup = relationship.split()
        for i in range(len(breakup)):
            if (breakup[i] == '==>'):
                word_side = breakup[:i]
                verb_side = "".join(breakup[(i+1):])
                #print(word_side)
                #print(verb_side)
        
        # Cleaning word_side
        # Removing & from word_side
        word_side = [ elem for elem in word_side if elem != '&'] 
        #print(word_side)

        new_word_order = []
        for word in word_side:
            new_word = word.replace('(','')
            new_word = new_word.replace(')','')
            new_word_order.append(new_word)
        #print(new_word_side)
        

        
        verb_split = verb_side.split('(')
        verb = verb_split[0]
        #print(verb)
        word_order = verb_split[1][:-1].split(',')
        #print(word_order)

        # Mapping word order
        subject_list = []
        mod_list = []
        indirect_object_list = []
        object_list = []
        positive = True
        for word in new_word_order:
            if word[-1] == word_order[0]:
                mod_list = word_dict[word[:-1]]
                if((word[:-1] == "Nt") or (word[:-1] == "Not")):
                    positive = False
            elif word[-1] == word_order[1]:
                subject_list = word_dict[word[:-1]]
            elif word[-1] == word_order[2]:
                indirect_object_list = word_dict[word[:-1]]
                #print(indirect_object_list)
            elif word[-1] == word_order[3]:
                object_list = word_dict[word[:-1]]
                #print(object_list)

        # print(subject_list)
        # print(indirect_object_list)
        # print(object_list)
        final_questions |= (write_w_question(verb, subject_list, indirect_object_list, object_list, positive))
        if len(final_questions) >= num_questions:
            break
        final_questions |= (write_question(verb, subject_list, indirect_object_list, object_list))
        if len(final_questions) >= num_questions:
            break

    counter = 1
    for final_question in final_questions:
        print(final_question)
        if counter == num_questions:
            break
        counter += 1

