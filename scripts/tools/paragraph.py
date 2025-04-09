from .sentence import Sentence

AD_SENTENCES = ["Lire aussi", "La vidéo du jour", "ARTICLE RECOMMAND"]


def merge_paragraphs(par_1, par_2):
    if par_1.is_ad:
        return par_2
    elif par_2.is_ad:
        return par_1
    par_1.components += par_2.components
    par_1.text += ' ' + par_2.text
    par_1.sentences += par_2.sentences
    return par_1


class Paragraph:
    def __init__(self, html_block, domain, lang='french'):
        self.x = html_block.x
        self.y = html_block.y
        self.size = html_block.size
        self.font_size = html_block.font_size
        self.tag = html_block.tag
        self.components = html_block.components
        self.text = ''.join([comp.text + ' ' if comp.text and comp.text[-1] != ' ' else comp.text for comp in self.components])
        self.text = self.text.replace(' .', '.')
        self.is_ad = self.find_ad(domain)
        self.sentences = []
        self.nb_sentence = 0
        for sentence in html_block.sentences:
            self.sentences.append(Sentence(sentence.sentence, sentence.elements))
        self.title = None

    def __str__(self):
        s = "PROBABLY AD\n"*(self.is_ad)
        s += ("PAR TITLE " + str(self.title)+"\n")*bool(self.title)
        for sent in filter(lambda s: s.is_summary, self.sentences):
            s += str(sent) + '\n'
        return s

    def find_ad(self, domain):
        if any([self.text.startswith(ad_sent) for ad_sent in AD_SENTENCES]):
            return True
        href_len = sum([len(component.text) for component in self.components if 'a' in component.tag.replace('span', '')])
        all_len = sum([len(component.text) for component in self.components])
        if href_len/all_len >= 0.7:
            return True
        hyperlink_tab = []
        for elem in self.components:
            if elem.tag in ['astrong', 'a', 'aspan', 'aem']:
                hyperlink_tab.append(elem)
        if len(hyperlink_tab) == 1:
            for link in hyperlink_tab:
                if domain in link.code or 'youtube' in link.code or 'insta' in link.code \
                        or 'twitter' in link.code or 'tweet' in link.code or '' == link.code:
                    return False
                else:
                    return True
        return False
