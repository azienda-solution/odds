

class Sentence:
    def __init__(self, text, components):
        self.text = text
        self.components = components
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
        return s
