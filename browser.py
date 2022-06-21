import tkinter # https://docs.python.org/ko/3/library/tkinter.html
import tkinter.font
from utils.url_request import request
from parse.http_parse import HTMLParser, Text, print_tree

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

class Layout:
    '''
    layout은 연산을 통해 브라우저에 그릴 display_list를 만드는 일이다.
    '''
    def __init__(self, tree):
        '''
        lexer를 통과해 얻은 token을 기반으로 display_list를 만들자.
        display_list는 브라우저 상 어떤 위치에 어떻게 그릴 것인지를 담은 리스트이다.
        '''
        self.display_list = []

        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.size = 16

        self.line = []
        self.recurse(tree)

    def recurse(self, tree):
        if isinstance(tree, Text):
            self.text(tree)
        else:
            self.open_tag(tree.tag)
            for child in tree.children:
                self.recurse(child)
            self.close_tag(tree.tag)

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
        '''
        text token을 좌표 및 폰트와 함께 line에 추가한다.
        '''
        font = get_font(self.size, self.weight, self.style)
        # 영어와 같은 표음 문자는 출력과 word-break가 word 단위로 이루어져야 함
        for word in node.text.split():
            word_width = font.measure(word)
            right_end = self.cursor_x + word_width 
            if right_end > WIDTH - HSTEP: # 그리려는 단어가 브라우저의 끝을 넘어가면 flush해야 함.
                self.flush() # line에 word가 다 채워졌으면 flush를 시행한다.
            self.line.append((self.cursor_x, word, font))
            self.cursor_x += word_width + font.measure(" ") # 단어 단위로 그려야 하므로 다음 단어를 그릴 때 단어 뿐만 아니라 공백의 길이도 포함해야 함. 

    def flush(self):
        '''
        line 내에 있는 word를 vertical align하고, display_list에 추가한다.
        '''
        if not self.line: return # 비어 있으면 early return
        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics]) # line에 담겨있는 font 중 가장 큰 값을 가져온다.
        baseline = self.cursor_y + 1.25 * max_ascent
        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))
        self.cursor_x = HSTEP
        self.line = []
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent

class Browser():
    def __init__(self) -> None:
        self.window = tkinter.Tk() # Talks to your operating system to create a window
        self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT)
        self.canvas.pack()

        self.scroll = 0
        self.window.bind("<Down>", self.scrolldown)
        self.bi_times = tkinter.font.Font(
            family="Times",
            size=16,
            weight="bold",
            slant="italic",
        )
        self.display_list = []

    def load(self, url):
        _, body = request(url)
        self.nodes = HTMLParser(body).parse() # 기존 lexing 제거, html parser로 DOM tree를 만든다.

        print("treecheck")
        print_tree(self.nodes) # DOM tree print

        self.display_list = Layout(self.nodes).display_list
        self.draw()

    def draw(self):
        '''
        draw는, layout 연산을 통해 나온 display_list를 실제로 브라우저에 그리는 일이다.
        '''
        self.canvas.delete("all")
        for x, y, word, font in self.display_list:
            # draw를 빠르게 하기 위해서 스크롤 내에 존재하지 않는 char는 create_text를 하지 않도록 한다.
            # 이 최적화를 하느냐, 안 하느냐에 따라서 생각보다 스크롤 속도에 차이가 존재한다.
            if y > self.scroll + HEIGHT: continue
            if y + font.metrics("linespace") < self.scroll: continue
            self.canvas.create_text(x, y - self.scroll, text=word, font=font, anchor="nw")

    def scrolldown(self, e):
        self.scroll += SCROLL_STEP
        self.draw()


if __name__ == "__main__":
    import sys
    Browser().load(sys.argv[1]) # browser를 켭니다.
    tkinter.mainloop() # event loop for updated browser canvas triggered.
