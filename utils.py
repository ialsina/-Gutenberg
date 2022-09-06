import random
from copy import deepcopy
import requests
import re
from itertools import zip_longest
import sys


def readfile(path):
    with open(path, 'r') as f:
        return f.read()

def writefile(path, content):
    with open(path, 'w') as f:
        f.write(content)

class ParsingError(Exception):
    pass

class TooManyGutidError(ParsingError):
    pass

class NoGutidError(ParsingError):
    pass

class SkipParsing(ParsingError):
    pass

class Library:
    def __init__(self, name):
        self.name = name
        self._library = set()

    def __len__(self):
        return len(self._library)

    def __iter__(self):
        return iter(self._library)

    def __repr__(self):
        return "Library containing {} books.".format(self.__len__())


    def add(self, book):
        assert isinstance(book, Book)
        self._library.add(book)

    def find(self, mode='any', **kwargs):
        if mode == 'any':
            return self.findany(**kwargs)
        elif mode == 'all':
            return self.findall(**kwargs)
        else:
            raise ValueError('mode can only take the values "all" or "any"')

    def findall(self, **kwargs):
        findings = Library('Findings')
        for book in self._library:
            if book.check(**kwargs):
                findings.add(book)
        return findings

    def findany(self, **kwargs):
        library = deepcopy(self._library)
        while library:
            book = library.pop()
            if book.check(**kwargs):
                return book
        return None

    def findid(self, query_id):
        if isinstance(query_id, list):
            output = []
            for el in query_id:
                output.append(self.findid(el))
            return output
        else:
            query_id = str(query_id)
            return self.findany(gutid=query_id)

    def pick(self, n=1):
        n = min(n, len(self))
        result = random.sample(self._library, k=n)
        if n == 1:
            return result[0]
        else:
            return result


    def peek(self, n=10):
        pick = self.pick(n=n)
        for i, book in enumerate(pick):
            print("{:>2d}: {}".format(i+1, book))
    



class Book:

    CHECK_DEFAULTS_EQUAL = {'title': False, 'author': False, 'subtitle': False}
    URL_PATTERNS = [
        "https://www.gutenberg.org/files/{0}/{0}-0.txt",
        "https://www.gutenberg.org/cache/epub/{0}/pg{0}.txt",
    ]

    def __init__(self, title = '', author = '', gutid = None, gutyear = None, **kwargs):
        self.title = title
        self.author = author
        self.gutid = gutid
        self.gutyear = gutyear
        for key, val in kwargs.items():
            setattr(self, key.lower().strip(), val.strip())
        if not hasattr(self, 'language'):
            self.language = 'english'
        else:
            self.language = self.language.lower()

    def __repr__(self):
        if self.author:
            return self.title + ', by ' + self.author
        else:
            return self.title

    @property
    def attrs(self):
        return self.__dict__

    @property
    def url(self):
        return [el.format(self.gutid) for el in self.URL_PATTERNS]

    def get_html(self):
        session = requests.Session()
        session.mount("http://", requests.adapters.HTTPAdapter(max_retries=2))
        session.mount("https://", requests.adapters.HTTPAdapter(max_retries=2))

        for url in self.url:
            response = session.get(url)
            if response.status_code == 200:
                return response.text
        else:
            raise requests.HTTPError


    def get_text(self):
        pattern = r'\*\*\*.*START.*\*\*\*(.*)\*\*\*.*END.*\*\*\*'
        html = self.get_html()
        search = re.search(pattern, html, flags=re.S)
        book = search.groups()[0]
        return book
        

    

    def check(self, default=True, equal=None, **kwargs):
        for key, val in kwargs.items():
            if val is None:
                continue
            if not self._condition(key, val, default=default, equal=equal):
                return False
        return True

    def _condition(self, key, val, default=True, equal=None):
        """Checks if the instance's attribute 'key' has the value 'val'
        key: attribute to check
        val: value towards which the attribute is checked
        default: if False: the checking is done via the value of 'equal'
                 if True: the checking is done via the default behavior
        equal: if True: the checking is done via an equality
               if False: the checking is done via a 'contains'
        Note: if default is True, equal is ignored
        Note: if the instance doesn't have the attribute 'key', returns
              False
        """
        if not hasattr(self, key):
            return False
        if default:
            _equal = self.CHECK_DEFAULTS_EQUAL.get(key, True)
        else:
            _equal = equal
        if _equal:
            return getattr(self, key) == val
        else:
            return val in getattr(self, key)


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



    #books_text = [el.strip() for el in text_data.split('\n\n') if el != '']
    #for text in books_text:

def parse_year(text_raw, year=None):
    pattern = r'(TITLE.*?\n)(.*)'
    matches1 = re.search(pattern, text_raw, flags=re.S)
    pattern_sub = r'(~ ~ ~ ~)(.*)(~ ~ ~ ~)'
    text_data = matches1.groups()[1]
    text_data = re.sub(pattern_sub, '', text_data)
    text_data = re.sub(pattern, '', text_data)
    books = get_list_of_books(text_data, method=0)
    return books


def get_list_of_books(text_raw, method=0, year=None):
    if method >= 3:
        return []
    books = []
    matches = list(separate_books(text_raw, method=method))
    for match in matches:
        text = match.groups()[0]
        try:
            book = parse_book(text, year, method=method)
            books.append(book)
        except SkipParsing:
            pass
            # print('SKIPPING {}'.format(text))
        except TooManyGutidError as e:
            # print('METHOD = {}'.format(method))
            # print('RETRYING: too many IDs found:\n{}\n'.format(text))
            retry_result = get_list_of_books(text, method=method+1, year=year)
            # print('RESULT:\n{}\n'.format(retry_result))
            books.extend(retry_result)
        except NoGutidError as e:
            pass
            # print('METHOD = {}'.format(method))
            # print('ERROR: no ID found:\n{}\n'.format(text))
        except ParsingError as e:
            # print('METHOD = {}'.format(method))
            # print('ERROR:\n{}\n'.format(text))
            raise e
        except Exception as e:
            raise e
    return books



def separate_books(text_raw, method=0):
    """
    method: 0: separates by double newline
            1: separates indentation-based
            2: separates indentation-based
    """

    pattern_sub = r'^ +$'
    pattern0 = r'^(\S.*?)(?=\n\n)'
    pattern1 = r'^(\S.*?)\n(?=\n|\S)'
    patterns = (pattern0, pattern1, pattern1)

    text = re.sub(pattern_sub, '', text_raw+'\n\n', flags=re.M)
    return re.finditer(patterns[method], text, flags=re.S+re.M)


def find_occurrences(target, text):
    pass


def parse_book(text_raw, year=None, method=0):
    if all(char == '=' for char in text_raw):
        raise SkipParsing
    text_lines = text_raw.split('\n')
    text_raw = text_raw.strip() + '\n\n'
    pattern = r'\s?(.+\S+)\s+(\d+\w?)\s*$'
    match_count = len(re.findall(pattern, text_raw, flags=re.M))
    if match_count > 1 and method < 1:
        raise TooManyGutidError
    elif match_count == 0:
        raise NoGutidError
    for i, line in enumerate(text_lines):
        search = re.search(pattern, line)
        if search is not None:
            break
    else:
        raise ParsingError(text_raw)
    text_lines[i] = search.groups()[0]
    text_lines = [el.strip() for el in text_lines]
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


gutenberg = parse_gutindex(readfile('data/GUTINDEX.ALL'))
