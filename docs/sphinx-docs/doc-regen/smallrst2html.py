r"""
Convert a restructured text document to html.

Inline math markup can uses the *math* directive, or it can use latex
style *\$expression\$*.  Math can be rendered using simple html and
unicode, or with mathjax.
"""

import re
from contextlib import contextmanager

# CRUFT: locale.getlocale() fails on some versions of OS X
# See https://bugs.python.org/issue18378
import locale
if hasattr(locale, '_parse_localename'):
    try:
        locale._parse_localename('UTF-8')
    except ValueError:
        _old_parse_localename = locale._parse_localename
        def _parse_localename(localename):
            code = locale.normalize(localename)
            if code == 'UTF-8':
                return None, code
            else:
                return _old_parse_localename(localename)
        locale._parse_localename = _parse_localename

from docutils.core import publish_parts
from docutils.writers.html4css1 import HTMLTranslator
from docutils.nodes import SkipNode

# pylint: disable=unused-import
try:
    from typing import Tuple
except ImportError:
    pass
# pylint: enable=unused-import

def rst2html(rst, part="whole", math_output="mathjax"):
    r"""
    Convert restructured text into simple html.

    Valid *math_output* formats for formulas include:
    - html
    - mathml
    - mathjax
    See `<http://docutils.sourceforge.net/docs/user/config.html#math-output>`_
    for details.

    The following *part* choices are available:
    - whole: the entire html document
    - html_body: document division with title and contents and footer
    - body: contents only

    There are other parts, but they don't make sense alone:

        subtitle, version, encoding, html_prolog, header, meta,
        html_title, title, stylesheet, html_subtitle, html_body,
        body, head, body_suffix, fragment, docinfo, html_head,
        head_prefix, body_prefix, footer, body_pre_docinfo, whole
    """
    # Ick! mathjax doesn't work properly with math-output, and the
    # others don't work properly with math_output!
    if math_output == "mathjax":
        # TODO: this is copied from docs/conf.py; there should be only one
        mathjax_path = "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.1/MathJax.js?config=TeX-MML-AM_CHTML"
        settings = {"math_output": math_output + " " + mathjax_path}
    else:
        settings = {"math-output": math_output}

    # TODO: support stylesheets
    #html_root = "/full/path/to/_static/"
    #sheets = [html_root+s for s in ["basic.css","classic.css"]]
    #settings["embed_styesheet"] = True
    #settings["stylesheet_path"] = sheets

    # math2html and mathml do not support \frac12
    rst = replace_compact_fraction(rst)

    # mathml, html do not support \tfrac
    if math_output in ("mathml", "html"):
        rst = rst.replace(r'\tfrac', r'\frac')

    rst = replace_dollar(rst)
    with suppress_html_errors():
        parts = publish_parts(source=rst, writer_name='html',
                              settings_overrides=settings)
    return parts[part]

@contextmanager
def suppress_html_errors():
    r"""
    Context manager for keeping error reports out of the generated HTML.

    Within the context, system message nodes in the docutils parse tree
    will be ignored.  After the context, the usual behaviour will be restored.
    """
    visit_system_message = HTMLTranslator.visit_system_message
    HTMLTranslator.visit_system_message = _skip_node
    yield None
    HTMLTranslator.visit_system_message = visit_system_message

def _skip_node(self, node):
    raise SkipNode

_compact_fraction = re.compile(r"(\\[cdt]?frac)([0-9])([0-9])")
def replace_compact_fraction(content):
    r"""
    Convert \frac12 to \frac{1}{2} for broken latex parsers
    """
    return _compact_fraction.sub(r"\1{\2}{\3}", content)


_dollar = re.compile(r"(?:^|(?<=\s|[-(]))[$]([^\n]*?)(?<![\\])[$](?:$|(?=\s|[-.,;:?\\)]))")
_notdollar = re.compile(r"\\[$]")
def replace_dollar(content):
    r"""
    Convert dollar signs to inline math markup in rst.
    """
    content = _dollar.sub(r":math:`\1`", content)
    content = _notdollar.sub("$", content)
    return content



def load_rst_as_html(filename):
    # type: (str) -> str
    """Load rst from file and convert to html"""
    from os.path import expanduser
    with open(expanduser(filename)) as fid:
        rst = fid.read()
    html = rst2html(rst)
    return html

def write_html(html, filename):
    from os.path import normpath, basename, join, abspath
    TARGET_LOCAL = basename(normpath(filename)).replace('.rst', '.html')
    RELATIVE_DIRECTION = "../build/html/user/models/"
    TARGET_PATH  = abspath(join(RELATIVE_DIRECTION, TARGET_LOCAL))
    print(TARGET_PATH)
    with open(TARGET_PATH, 'w') as fid:
        fid.write(html)

def main():
    # type: () -> None
    """Command line interface to rst or html viewer."""
    import sys
    html = load_rst_as_html(sys.argv[1])
    write_html(html, sys.argv[1])


if __name__ == "__main__":
    main()
