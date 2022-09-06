def readfile(path):
	with open(path, 'r') as f:
		return f.read()

def writefile(path, content):
	with open(path, 'w') as f:
		f.write(content)


class Library:
	def __init__(self, name):
		self.name = name
		self._library = set()

	def add(self, book):
		assert isinstance(book, Book)
		self._library.add(book)

	def browse(self, language=None, **kwargs):
		kwargs.update(language=language)
		findings = set()
		for book in self._library:
			if book.check(**kwargs):
				findings.add(book)
		return findings


class Book:
	def __init__(self, text_to_parse):
		raise NotImplementedError()