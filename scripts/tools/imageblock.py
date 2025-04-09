class ImageBlock:
    def __init__(self, info):
        self.x = info["x"]
        self.y = info["y"]
        self.caption = info["caption"]
        self.src = info["src"]
        self.text = info["text"]
        self.font_size = None
        self.tag = None
        self.components = []
        self.figcaption = info["figcaption"]
