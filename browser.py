from utils.url_request import request
import tkinter # https://docs.python.org/ko/3/library/tkinter.html
import tkinter.font

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100

def lex(body):
    text = ""
    in_angle = False
    for c in body:
        if c == "<":
            in_angle = True
        elif c == ">":
            in_angle = False
        elif not in_angle:
            text += c
    return text

def layout(text):
    '''
    layout은 연산을 통해 브라우저에 그릴 display list를 만드는 일이다.
    '''
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    for c in text:
        display_list.append((cursor_x, cursor_y, c))
        cursor_x += HSTEP
        if cursor_x >= WIDTH - HSTEP:
            cursor_y += VSTEP
            cursor_x = HSTEP
    return display_list # (x, y, c)

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


    def load(self, url):
        _, body = request(url)
        text = lex(body)
        self.display_list = layout(text)
        self.draw()

    def draw(self):
        '''
        draw라는 것은, layout을 통해 나온 display list를 실제로 브라우저에 그리는 일이다.
        '''
        self.canvas.delete("all")
        for x, y, c in self.display_list:
            # draw를 빠르게 하기 위해서 스크롤 내에 존재하지 않는 char는 create_text를 하지 않도록 한다.
            # 이 최적화를 하느냐, 안 하느냐에 따라서 생각보다 스크롤 속도에 차이가 존재한다.
            if y > self.scroll + HEIGHT: continue
            if y + VSTEP < self.scroll: continue 
            self.canvas.create_text(x, y - self.scroll, text=c, font=self.bi_times)

    def scrolldown(self, e):
        self.scroll += SCROLL_STEP
        self.draw()


if __name__ == "__main__":
    import sys
    Browser().load(sys.argv[1]) # browser를 켭니다.
    tkinter.mainloop() # event loop for updated browser canvas triggered.
