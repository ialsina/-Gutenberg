import re
from itertools import zip_longest
from utils import readfile, writefile, Book, Library, ParsingError, SkipParsing, gutenberg
import sys


text_example = readfile('data/example.txt')
gutenberg
gutauthors = set()
for book in gutenberg:
    gutauthors.add(book.author)

