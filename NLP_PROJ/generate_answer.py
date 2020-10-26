import sys
import io
import os
from .parser import Parser

if __name__ == '__main__':
    print(os.getcwd())
    if len(sys.argv) != 2:
        print("Usage: python3 parser.py FILE_NAME")
        sys.exit(1)

    txt = sys.argv[1]

    with io.open(txt, 'r', encoding='utf8') as f:
        train_data = f.read()

    # Parser(train_data)