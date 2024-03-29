import base64
import cherrypy
import io
import matplotlib.pyplot as plt
import numpy as np
import os
import re
from scipy import special


def sharlie(n):
    return special.erfinv((n - 1) / n) * np.sqrt(2)


def statistics(x):
    """return mean, sample std"""
    return x.mean(), np.sqrt(np.sum((x - x.mean()) ** 2) / (len(x) - 1))


def metric(x):
    """return normalized deviation"""
    mean, sko = statistics(x)
    return np.abs(x - mean) / sko


def borders(x):
    """return borders for good values"""
    sh = sharlie(len(x))
    s = np.sqrt(np.sum((x - x.mean()) ** 2) / (len(x) - 1))
    m = x.mean()
    return m - sh * s, m + sh * s


def find_bad(x):
    """return good and bad values in dataset"""
    test = metric(x)
    mask = test > sharlie(len(x))
    bad = x[mask]
    x = x[~mask]
    return x, bad


def plt_to_base64(x, ok, bad, size=5):
    """draw plot graph"""
    border = borders(ok) if len(ok) > 0 else None
    iterator_ok = np.arange(len(x))[np.isin(x, ok)]
    iterator_bad = np.arange(len(x))[np.isin(x, bad)]
    plt.figure(figsize=(size, size))
    plt.grid(True)
    plt.title("Обработка выборки")
    plt.xlabel("#")
    plt.ylabel("Значение")
    if border is not None:
        plt.hlines(border, 0, len(x) - 1, color="r", linestyles="dashed")
    plt.scatter(iterator_ok, ok, label="Хорошие значения")
    plt.scatter(iterator_bad, bad, label="Промахи")
    plt.legend()
    b = io.BytesIO()
    plt.savefig(b, format="png")
    b.seek(0)
    return base64.b64encode(b.read()).decode()


def calc(x):
    history = []
    x = np.array(x)
    bad = [0]  # do-while loop
    ok = x.copy()
    while len(bad) != 0 and len(ok) > 1:
        mean, sko = statistics(ok)
        sh = sharlie(len(ok))
        ok, bad = find_bad(ok)
        history.append({"ok": ok.tolist(), "bad": bad.tolist(), "plot": plt_to_base64(x, ok, bad), "mean": mean, "sko": sko, "sharlie": sh})
    return history


def get_page():
    with open("index.html", 'r', encoding='utf8') as f:
        return f.read()


page = None
if os.environ.get('DEVELOPMENT') is None:
    page = get_page()


class Root(object):
    @cherrypy.expose
    def index(self):
        return get_page() if page is None else page

    @cherrypy.expose
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def calc(self):
        data = list(map(float, " ".join(re.findall('[0-9.]*', cherrypy.request.json["data"].replace(",", "."))).split()))
        return calc(data)


if __name__ == '__main__':
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': 8080,
        'tools.proxy.on': True,
    })
    cherrypy.quickstart(Root())
