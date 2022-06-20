from utils.url_request import request

def show(body):
    in_angle = False
    for c in body:
        if c == "<":
            in_angle = True
        elif c == ">":
            in_angle = False
        elif not in_angle:
            print(c, end="") # angle 내부의 문자를 출력.

def load(url):
    _, body = request(url)
    show(body)

if __name__ == "__main__":
    import sys
    load(sys.argv[1])
