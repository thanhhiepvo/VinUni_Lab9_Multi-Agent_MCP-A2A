import urllib.request, urllib.parse, re, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch_links(q):
    req = urllib.request.Request(
        f"https://lite.duckduckgo.com/lite/",
        data=f"q={urllib.parse.quote(q)}".encode('utf-8'),
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    try:
        html = urllib.request.urlopen(req, context=ctx).read().decode('utf-8')
        links = re.findall(r'href="(https://vnexpress\.net/[^"]+)"', html)
        return links
    except Exception as e:
        return []

all_links = fetch_links("site:vnexpress.net diễn viên Lệ Hằng ma túy")
for l in all_links:
    print(l)
