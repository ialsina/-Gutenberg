import re
from itertools import zip_longest
from utils import readfile, writefile, Book, Library



def parse_gutindex(gutindex_raw):
    pattern = r'(<===LISTINGS===>\n)(.*)(<==End of GUTINDEX.ALL==>)'
    gutindex_stripped = re.search(pattern, gutindex_raw, flags=re.S).groups()[1]
    findings = list(re.finditer('={2,}', gutindex_stripped))
    years = []

    for cur, nex in zip_longest(findings, findings[1:], fillvalue=None):
        val_beg = cur.span()[1]
        if nex is None:
            val_end = len(gutindex_stripped)
        else:
            val_end = nex.span()[0]
        years.append(gutindex_stripped[val_beg:val_end])

    return years


def find_occurrences(target, text):
    pass


def parse_book(gugtenberg_raw):
    pattern = r'(\*\*\*.*START.*\*\*\*)(.*)(\*\*\*.*END.*\*\*\*)'
    search = re.search(pattern, text, flags=re.S)
    book = search.groups()[1]
    return book


text_example = readfile('data/example.txt')

years = parse_gutindex(readfile('data/GUTINDEX.ALL'))

for i, text in enumerate(years):
    writefile('data/years/year_{:0>2d}.txt'.format(i), text)
