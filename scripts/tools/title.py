class Title:
    def __init__(self, html_block, tag=None):
        self.x = html_block.x
        self.y = html_block.y
        self.size = html_block.size
        self.font_size = html_block.font_size
        self.tag = tag if tag is not None else html_block.tag
        self.textblocks = None
        self.components = html_block.components
        self.text = ''.join([comp.text for comp in self.components])

    def __str__(self):
        return "TITLE " + '\n' + self.text
