class Image:

    def __init__(self, *args):
        if not isinstance(args[0], dict):
            self.x = args[0].x
            self.y = args[0].y
            self.caption = args[0].caption
            self.src = args[0].src
            self.figcaption = args[0].figcaption
            if hasattr(args[0], 'link'):
                self.link = args.get('link')
            else:
                self.link = None

        else:
            self.x = args[0].get('x')
            self.y = args[0].get('y')
            self.caption = args[0].get('text')
            self.src = args[0].get('preview')
            self.figcaption = args[0].get('type')
            self.link = args[0].get('link')

    def __str__(self):
        return "IMAGE\n" + self.caption + "\n" + self.src

    def is_valid(self):
        return self.size['height'] * self.size['width'] > 300*300


