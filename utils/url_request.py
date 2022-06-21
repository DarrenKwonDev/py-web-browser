import socket
import ssl

from utils.parse_url import parse_url

def request(url: str):
    scheme, host, port, path = parse_url(url)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)

    s.connect((host, port))

    if scheme == "https":
        ctx = ssl.create_default_context()
        s = ctx.wrap_socket(s, server_hostname=host)

    sent_bytes_size = s.send(
        "GET {} HTTP/1.0\r\n".format(path).encode("utf8") + 
        "Host: {}\r\n\r\n".format(host).encode("utf8"))
    print("sent_bytes_size", sent_bytes_size)

    response = s.makefile("r", encoding="utf8", newline="\r\n")
    statusline = response.readline() # 헤더 한 줄 읽어와야 함. 다른 header들과 포맷이 다르다. 'HTTP/1.0 200 OK\r\n'
    version, status, explanation = statusline.split(" ", 2) 
    assert status == "200", "{}: {}".format(status, explanation)

    headers = {}
    while True:
        line = response.readline() # 'Accept-Ranges: bytes\r\n' 꼴의 header들을 한 줄씩 읽어나감.
        if line == "\r\n": break # header의 끝은 항상 공백(\r\n)으로 끝나기 때문에.
        header, value = line.split(":", 1)
        headers[header.lower()] = value.strip()

    assert "transfer-encoding" not in headers # allows the data to be “chunked”
    assert "content-encoding" not in headers # lets the server compress web pages before sending them

    body = response.read() # 앞서 header 다 읽었고, \r\n 공백 하단은 body겠지?

    s.close()

    return headers, body