def parse_url(url):
    scheme, url = url.split("://", 1)

    if ('/' in url):
        host, path = url.split('/', 1)
        path = '/' + path
    else:
        host = url
        path = '/'

    port = 80 if scheme == "http" else 443

    if ":" in host:
        host, port = host.split(":", 1)
        port = int(port)

    return scheme, host, port, path