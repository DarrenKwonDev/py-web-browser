import tkinter # https://docs.python.org/ko/3/library/tkinter.html
import tkinter.font
from utils.url_request import request
from parse.http_parse import HTMLParser, Text, Element, print_tree

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100
FONTS = {}

# font memorization
def get_font(size, weight, slant):
    key = (size, weight, slant)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight, slant=slant)
        FONTS[key] = font
    return FONTS[key]


BLOCK_ELEMENTS = [
    "html", "body", "article", "section", "nav", "aside",
    "h1", "h2", "h3", "h4", "h5", "h6", "hgroup", "header",
    "footer", "address", "p", "hr", "pre", "blockquote",
    "ol", "ul", "menu", "li", "dl", "dt", "dd", "figure",
    "figcaption", "main", "div", "table", "form", "fieldset",
    "legend", "details", "summary"
]

def layout_mode(node):
    if isinstance(node, Text):
        return "inline"
    elif node.children:
        for child in node.children:
            if isinstance(child, Text): continue
            if child.tag in BLOCK_ELEMENTS:
                return "block"
        return "inline"
    else:
        return "block"

class BlockLayout:
    def __init__(self, node, parent, previous):
        self.node = node # layout node에 대응하는 html node
        self.parent = parent # parentNode
        self.previous = previous # siblingNode 계산을 위해 넣어두기
        self.children = [] # childrenNode

        self.x = None # block이 놓일 좌표 및 폭, 높이
        self.y = None
        self.width = None
        self.height = None

    def layout(self):
        '''
        layout은 해당 요소의 size와 position을 계산하는 작업이다.
        '''

        # This code is tricky because it involves two trees. 
        # The node and child are part of the HTML tree; but self, previous, and next are part of the layout tree.
        previous = None
        for child in self.node.children:
            if layout_mode(child) == "inline":
                next = InlineLayout(child, self, previous)
            else:
                next = BlockLayout(child, self, previous)
            self.children.append(next)
            previous = next

        self.width = self.parent.width # 기본적으로 block 요소는 greedy해서 폭을 가질 수 있는 만큼 다 가진다 == 부모 폭을 따라간다.
        self.x = self.parent.x # each layout object starts at its parent’s left edge

        # The vertical position of a layout object depends on the position and height of their previous sibling. 
        # If there is no previous sibling, they start at the parent’s top edge:
        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y

        for child in self.children:
            child.layout()

        # should be tall enough to contain all of its children, so its height should be the sum of its children’s heights
        # height depends on the height of its children, its height must be computed after recursing to compute the heights of its children.
        self.height = sum([child.height for child in self.children])

    def paint(self, display_list):
        for child in self.children:
            child.paint(display_list)

    def __repr__(self):
        return "BlockLayout(x={}, y={}, width={}, height={}, node={})".format(
            self.x, self.y, self.width, self.height, self.node)

class InlineLayout:
    def __init__(self, node, parent, previous):
        self.node = node # layout node에 대응하는 html node
        self.parent = parent # parentNode
        self.previous = previous # siblingNode 계산을 위해 넣어두기
        self.children = [] # childrenNode

        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.display_list = None

    def layout(self):
        '''
        layout은 해당 요소의 size와 position을 계산하는 작업이다.
        '''
        self.width = self.parent.width
        self.x = self.parent.x

        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y

        self.display_list = []
        self.weight = "normal"
        self.style = "roman"
        self.size = 16

        self.cursor_x = self.x
        self.cursor_y = self.y
        self.line = []
        self.recurse(self.node)
        self.flush()

        self.height = self.cursor_y - self.y

    def recurse(self, node):
        if isinstance(node, Text):
            self.text(node)
        else:
            self.open_tag(node.tag)
            for child in node.children:
                self.recurse(child)
            self.close_tag(node.tag)

    def open_tag(self, tag):
        if tag == "i":
            self.style = "italic"
        elif tag == "b":
            self.weight = "bold"
        elif tag == "small":
            self.size -= 2
        elif tag == "big":
            self.size += 4
        elif tag == "br":
            self.flush()

    def close_tag(self, tag):
        if tag == "i":
            self.style = "roman"
        elif tag == "b":
            self.weight = "normal"
        elif tag == "small":
            self.size += 2
        elif tag == "big":
            self.size -= 4
        elif tag == "p":
            self.flush()
            self.cursor_y += VSTEP
        
    def text(self, node):
        font = get_font(self.size, self.weight, self.style)
        for word in node.text.split():
            word_width = font.measure(word)
            if self.cursor_x + word_width > self.width - HSTEP:
                self.flush()
            self.line.append((self.cursor_x, word, font))
            self.cursor_x += word_width + font.measure(" ")

    def flush(self):
        if not self.line: return
        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent
        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))
        self.cursor_x = self.x
        self.line = []
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent

    def paint(self, display_list):
        if isinstance(self.node, Element) and self.node.tag == "pre":
            x2, y2 = self.x + self.width, self.y + self.height
            rect = DrawRect(self.x, self.y, x2, y2, "gray") 
            display_list.append(rect)
        for x, y, word, font in self.display_list:
            display_list.append(DrawText(x, y, word, font)) # layout에서 계산된 명세를 DrawText로 그리는 명령어를 display_l

    def __repr__(self):
        return "InlineLayout(x={}, y={}, width={}, height={}, node={})".format(
            self.x, self.y, self.width, self.height, self.node)

class DocumentLayout:
    '''
    The browser walks the HTML tree to produce the layout tree, 
    then computes the size and position for each layout object, 
    and finally draws each layout object to the screen.
    '''
    def __init__(self, node):
        self.node = node
        self.parent = None
        self.previous = None
        self.children = []

    def layout(self):
        '''
        layout은 해당 요소의 size와 position을 계산하는 작업이다.
        '''
        child = BlockLayout(self.node, self, None)
        self.children.append(child)

        self.width = WIDTH - 2 * HSTEP
        self.x = HSTEP
        self.y = VSTEP
        child.layout()
        self.height = child.height + 2 * VSTEP

    def paint(self, display_list):
        self.children[0].paint(display_list)

    def __repr__(self):
        return "DocumentLayout()"

class DrawText:
    def __init__(self, x1, y1, text, font):
        self.top = y1
        self.left = x1
        self.text = text
        self.font = font

        self.bottom = y1 + font.metrics("linespace")

    def execute(self, scroll, canvas):
        canvas.create_text(
            self.left, self.top - scroll,
            text=self.text,
            font=self.font,
            anchor='nw',
        )

    def __repr__(self):
        return "DrawText(top={} left={} bottom={} text={} font={})".format(
            self.top, self.left, self.bottom, self.text, self.font)


class DrawRect:
    def __init__(self, x1, y1, x2, y2, color):
        self.top = y1
        self.left = x1
        self.bottom = y2
        self.right = x2
        self.color = color

    def execute(self, scroll, canvas):
        canvas.create_rectangle(
            self.left, self.top - scroll,
            self.right, self.bottom - scroll,
            width=0,
            fill=self.color,
        )

    def __repr__(self):
        return "DrawRect(top={} left={} bottom={} right={} color={})".format(
            self.top, self.left, self.bottom, self.right, self.color)
class Browser():
    def __init__(self) -> None:
        self.window = tkinter.Tk() # Talks to your operating system to create a window
        self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT)
        self.canvas.pack()

        self.scroll = 0
        self.window.bind("<Down>", self.scrolldown)
        self.display_list = [] # display_list는 무엇을 어떻게 그리라는 명령어의 리스트.

    def load(self, url):
        _, body = request(url)
        self.nodes = HTMLParser(body).parse() # 기존 lexing 제거, html parser로 DOM tree를 만든다.
        self.document = DocumentLayout(self.nodes)
        self.document.layout()

        self.display_list = []
        self.document.paint(self.display_list)
        self.draw()

    def draw(self):
        '''
        draw는, layout 연산을 통해 나온 display_list를 실제로 브라우저에 그리는 일이다.
        '''
        self.canvas.delete("all")

        for cmd in self.display_list:
            # 빠르게 스크롤이 동작하기 위해서 스크롤 내에 존재하지 않는 char는 create_text를 하지 않도록 한다.
            # 이 최적화를 하느냐, 안 하느냐에 따라서 생각보다 스크롤 속도에 차이가 존재한다.
            if cmd.top > self.scroll + HEIGHT: continue
            if cmd.bottom < self.scroll: continue
            cmd.execute(self.scroll, self.canvas)

    def scrolldown(self, e):
        max_y = self.document.height - HEIGHT
        self.scroll = min(self.scroll + SCROLL_STEP, max_y)
        self.draw()


if __name__ == "__main__":
    import sys
    Browser().load(sys.argv[1]) # browser를 켭니다.
    tkinter.mainloop() # event loop for updated browser canvas triggered.
