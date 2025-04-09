

class Video:
    def __init__(self, video):
        self.type = video.type
        self.x = video.x
        self.y = video.y
        self.html = video.html
        # self.size = video.size
        self.src = video.src
        self.preview = video.preview
        self.id = video.id
        if hasattr(video, 'comment'):
            self.caption = video.comment
        else:
            self.caption = None
        if hasattr(video, 'link'):
            self.link = video.link
        else:
            self.link = None


    def __str__(self):
        s = "VIDEO\n"
        s += self.type + '\n'
        s += self.src + '\n'
        return s
