class Text:
    def __init__(self, text, parent):
        self.text = text
        self.children = []
        self.parent = parent

    def __repr__(self):
        return repr(self.text)

class Element:
    def __init__(self, tag, attributes, parent):
        self.tag = tag
        self.attributes = attributes
        self.children = []
        self.parent = parent

    def __repr__(self):
        attrs = [" " + k + "=\"" + v + "\"" for k, v  in self.attributes.items()]
        return "<" + self.tag + "".join(attrs) + ">"

def print_tree(node, indent=0):
    print(" " * indent, node)
    for child in node.children:
        print_tree(child, indent + 2)

class HTMLParser:
    '''
    source html를 파싱하여 DOM tree를 그립니다.
    '''
    def __init__(self, body):
        self.body = body
        self.unfinished = [] # 닫히지 않고 열린 태그가 여기에 담김 

    def parse(self):
        text = ""
        in_tag = False
        for c in self.body:
            # <h1>wow</h1> 꼴에서 Text(wow)는 <를 만나면 끝난다.
            # <h1>wow</h1> 꼴에서 Element(h1)는 >를 만나면 끝난다.
            if c == "<":
                in_tag = True
                if text: self.add_text(text) # <를 만났으므로 여기까지가 Text
                text = ""
            elif c == ">":
                in_tag = False
                self.add_tag(text) # >를 만났으므로 여기까지가 Tag
                text = ""
            else:
                text += c
        if not in_tag and text:
            self.add_text(text)
        return self.finish()

    def get_attributes(self, text):
        parts = text.split()
        tag = parts[0].lower()
        attributes = {}
        for attrpair in parts[1:]:
            if "=" in attrpair:
                key, value = attrpair.split("=", 1)
                if len(value) > 2 and value[0] in ["'", "\""]:
                    value = value[1:-1]
                attributes[key.lower()] = value
            else:
                attributes[attrpair.lower()] = ""
        return tag, attributes

    def add_text(self, text):
        if text.isspace(): return # 문자가 공백일 경우
        self.implicit_tags(None)
        parent = self.unfinished[-1] # 마지막에 열린 태그
        node = Text(text, parent)
        parent.children.append(node) # Text 노드 추가

    SELF_CLOSING_TAGS = [
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
    ]

    def add_tag(self, tag):
        tag, attributes = self.get_attributes(tag)
        if tag.startswith("!"): 
            # <!doctype html>와 같은 special tag나 html 주석 <!-- comment text --> 무시 (원래 브라우저는 다 처리 하는데 우리는 공부용이니 pass)
            return 
        self.implicit_tags(tag)

        
        if tag.startswith("/"): # </h1> 꼴로 태그가 닫히므로 /로 시작한다는 것은 close tag를 말함.
            if len(self.unfinished) == 1: return
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        elif tag in self.SELF_CLOSING_TAGS: 
            parent = self.unfinished[-1]
            node = Element(tag, attributes, parent)
            parent.children.append(node)
        else: # open tag를 다루는 로직
            parent = self.unfinished[-1] if self.unfinished else None
            node = Element(tag, attributes, parent)
            self.unfinished.append(node)

    HEAD_TAGS = [
        "base", "basefont", "bgsound", "noscript",
        "link", "meta", "title", "style", "script",
    ]

    def implicit_tags(self, tag):
        while True:
            open_tags = [node.tag for node in self.unfinished]
            if open_tags == [] and tag != "html":
                self.add_tag("html")
            elif open_tags == ["html"] and tag not in ["head", "body", "/html"]:
                if tag in self.HEAD_TAGS:
                    self.add_tag("head")
                else:
                    self.add_tag("body")
            elif open_tags == ["html", "head"] and tag not in ["/head"] + self.HEAD_TAGS:
                self.add_tag("/head")
            else:
                break

    def finish(self):
        if len(self.unfinished) == 0:
            self.add_tag("html")
        while len(self.unfinished) > 1:
            node = self.unfinished.pop() 
            parent = self.unfinished[-1] 
            parent.children.append(node)
        return self.unfinished.pop()
