import io

from NLP_PROJ.oracle import Oracle

# Answering Questions Example
txt = "NLP_PROJ\\set2\\a1.txt"
with io.open(txt, 'r', encoding='utf8') as f:
    train_data1 = f.read()

txt = "NLP_PROJ\\set5\\a1.txt"
with io.open(txt, 'r', encoding='utf8') as f:
    train_data2 = f.read()
q1 = "What was a Bronze Age civilisation?"
Oracle1 = Oracle(train_data1)
Oracle2 = Oracle(train_data2)
print(Oracle1.answer(q1))
q2 = "What is a bitch?"
print(Oracle2.answer(q2))
