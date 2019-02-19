import sublime

import time
from wcwidth import wcwidth
from functools import wraps
from contextlib import contextmanager


def panel_window(view):
    for w in sublime.windows():
        for panel in w.panels():
            v = w.find_output_panel(panel.replace("output.", ""))
            if v and v.id() == view.id():
                return w
    return None


def view_size(view):
    pixel_width, pixel_height = view.viewport_extent()
    pixel_per_line = view.line_height()
    pixel_per_char = view.em_width()

    if pixel_per_line == 0 or pixel_per_char == 0:
        return (0, 0)

    nb_columns = int(pixel_width / pixel_per_char) - 3
    if nb_columns < 1:
        nb_columns = 1

    nb_rows = int(pixel_height / pixel_per_line)
    if nb_rows < 1:
        nb_rows = 1

    return (nb_rows, nb_columns)


def highlight_key(view):
    """
    make region keys incremental and recyclable
    """
    value = view.settings().get("terminus.highlight_counter", 0)

    if value == 1e8:
        value = 0

    while value >= 1:
        regions = view.get_regions("terminus#{}".format(value))
        if regions and not regions[0].empty():
            break
        value -= 1
    value += 1
    view.settings().set("terminus.highlight_counter", value)
    return "terminus#{}".format(value)


def responsive(period=0.1, default=True):
    """
    make a function more responsive
    """
    def wrapper(f):
        t = [0]

        @wraps(f)
        def _(*args, **kwargs):
            now = time.time()
            if now - t[0] > period:
                t[0] = now
                return f(*args, **kwargs)
            else:
                return default

        return _

    return wrapper


@contextmanager
def intermission(period=0.1):
    """
    intermission of period seconds.
    """
    startt = time.time()
    yield
    deltat = time.time() - startt
    if deltat < period:
        time.sleep(period - deltat)


def rev_wcwidth(text, width):
    """
    Given a text, return the location such that the substring has width `width`.
    """
    if width == 0:
        return -1

    w = 0
    i = -1
    # loop over to check for double width chars
    for i, c in enumerate(text):
        w += wcwidth(c)
        if w >= width:
            break
    if w >= width:
        return i
    else:
        return i + width - w


def settings_on_change(settings, keys, clear=True):
    if not isinstance(keys, list):
        keys = [keys]
    _cached = {}
    for key in keys:
        _cached[key] = settings.get(key, None)

    def on_change_factory(key, on_change):
        def _():
            value = settings.get(key)
            if _cached[key] != value:
                try:
                    on_change(value)
                finally:
                    _cached[key] = value

        return _

    def _(on_change):
        for key in keys:
            if clear:
                settings.clear_on_change(key)

            settings.add_on_change(key, on_change_factory(key, on_change))

    return _
