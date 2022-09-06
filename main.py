import re
from itertools import zip_longest
from utils import readfile, writefile, Book, Library
import sys


def parse_gutindex(gutindex_raw):
    pattern = r'(<===LISTINGS===>\n)(.*)(<==End of GUTINDEX.ALL==>)'
    main_match = re.search(pattern, gutindex_raw, flags=re.S)
    main_span = main_match.span()
    gutindex_stripped = main_match.groups()[1]
    years_text = separate_by_year(gutindex_stripped)
    years_book = {year: parse_year(text, year) for year, text in years_text.items()}
    library = Library('Gutenberg')
    for _, books in years_book.items():
        for book in books:
            library.add(book)
    return library




def separate_by_year(gutindex_stripped):
    headers = list(re.finditer(r'[\s\t]+GUTINDEX\.(\d{4})[\s\t]*\n', gutindex_stripped))
    years_dict = dict()
    for cur_header, nex_header in zip_longest(headers, headers[1:]):
        year = int(cur_header.groups()[0])
        pos0 = cur_header.span()[1]
        if nex_header:
            pos1 = nex_header.span()[0]
        else:
            pos1 = len(gutindex_stripped)
        cur_text = gutindex_stripped[pos0:pos1] 
        years_dict[year] = cur_text
    return years_dict


def parse_year(text_raw, year=None):
    pattern = r'(TITLE.*?\n)(.*)'
    matches = re.search(pattern, text_raw, flags=re.S)
    pattern_sub = r'(~ ~ ~ ~)(.*)(~ ~ ~ ~)'
    text_data = matches.groups()[1]
    text_data = re.sub(pattern_sub, '', text_data)
    text_data = re.sub(pattern, '', text_data)
    books_text = [el.strip() for el in text_data.split('\n\n') if el != '']
    books = [parse_book(el, year) for el in books_text]
    books = [el for el in books if isinstance(el, Book)]
    return books


def find_occurrences(target, text):
    pass



def parse_book(text_raw, year=None):
    text_lines = []
    text_raw_lines = text_raw.split('\n')
    pattern = r'(\D+\s+)(\d+\w?)'
    search = re.search(pattern, text_raw_lines[0])
    if search is None:
        print("Error in:", text_raw)
        return "Error"
    text_lines.append(search.groups()[0].strip())
    gutid = search.groups()[1]  
    text_lines.extend(text_raw_lines[1:])
    column1 = ' '.join(text_lines)
    attrs = parse_elements(column1)
    return Book(gutid=gutid, gutyear=year, **attrs)


# WORK IN PROGRESS. PROBLEM TRYING TO SOLVE: TITLE OVER MULTIPLE LINES (ex. 40233)
def parse_book(text_raw, year=None):
    text_lines = text_raw.split('\n')
    pattern = r'\s?(.+\S+)\s+(\d+\w?)'
    for i, line in enumerate(text_lines):
        search = re.search(pattern, line)
        if search:
            break
        else:
            print(i, line)
    else:
        print("Error in:", text_raw)
        return "Error"
    text_lines[i] = search.groups()[0]
    gutid = search.groups()[1]
    column1 = ' '.join(text_lines)
    attrs = parse_elements(column1)
    return Book(gutid=gutid, gutyear=year, **attrs)


def parse_elements(line):

    attrs = {}
    pattern = r'\[(.*?):(.*?)\]'
    title_author = re.sub(pattern, '', line).strip()
    sep = ', by '
    sep_count = title_author.count(sep)
    if sep_count == 1:
        title, author = title_author.split(sep)
    elif sep_count == 0:
        title = title_author
        author = ''
    elif sep_count > 1:
        separated = title_author.split(sep)
        title = sep.join(separated[:-1])
        author = separated[-1]
    attrs['title'] = title
    attrs['author'] = author
    for match in re.finditer(pattern, line):
        attrs.update({match.groups()[0].strip(): match.groups()[1].strip()})
    return attrs
    



text_example = readfile('data/example.txt')

library = parse_gutindex(readfile('data/GUTINDEX.ALL'))

#for year, text in years.items():
#    writefile('data/years/year_{:0>2d}.txt'.format(year), text)

