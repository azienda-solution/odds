
class HtmlBlock:
    def __init__(self, info):
        self.x = info["x"]
        self.y = info["y"]
        self.size = {"height": info["size"]["height"], "width": info["size"]["width"]}
        self.font_size = info["font_size"]
        self.tag = info["tag"]
        self.components = [Component(text=sentence, tag=info["tag"]) for sentence in info["sentences"]]
        self.text = ''.join([comp.text for comp in self.components])
        self.sentences = [Sentence(sentence=sentence, tag=info["tag"]) for sentence in info["sentences"]]



class Component:
    def __init__(self, text, tag=None, href=None):
        self.text = text
        self.tag = tag
        
class Sentence:
    def __init__(self, sentence, tag):
        self.sentence = sentence
        self.elements = [Element(code=sentence, text=sentence, location=0, href=None, tag=tag,)]

        
class Element:
    def __init__(self, code, href, location, tag, text):
        self.href = href
        self.location = location
        self.tag = tag
        self.text = text
        self.code = code

"""class Sentence:
    def __init__(self, text, components=None, sentence=[]):
        self.text = text
        self.components = components
        self.sentences = sentence
        self.entities = None
        self.comments = []
        self.paragraph_entities = []
        self.is_summary = False
        self.is_bold = False
        self.is_link = False
        self.textblocks = {}
        self.keywords = []
        self.keywords_type = ''

    def __str__(self):
        s = ""
        for comp in self.components:
            s += str(comp) + '\n'
        return s"""

