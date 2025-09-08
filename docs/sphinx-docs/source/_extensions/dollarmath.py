# This program is public domain
# Author: Paul Kienzle
r"""
Allow $math$ markup in text and docstrings, ignoring \$.

The $math$ markup should be separated from the surrounding text by spaces.  To
embed markup within a word, place backslash-space before and after.  For
convenience, the final $ can be followed by punctuation (period, comma or
semicolon).
"""

import re

_dollar = re.compile(r"(?:^|(?<=\s|[-(]))[$]([^\n]*?)(?<![\\])[$](?:$|(?=\s|[-.,;:?\\)]))")
_notdollar = re.compile(r"\\[$]")

def replace_dollar(content):
    content = _dollar.sub(r":math:`\1`",content)
    content = _notdollar.sub("$", content)
    return content

def rewrite_rst(app, docname, source):
    source[0] = replace_dollar(source[0])

def rewrite_autodoc(app, what, name, obj, options, lines):
    lines[:] = [replace_dollar(L) for L in lines]

def setup(app):
    app.connect('source-read', rewrite_rst)
    app.connect('autodoc-process-docstring', rewrite_autodoc)


def test_dollar():
    assert replace_dollar("no dollar")=="no dollar"
    assert replace_dollar("$only$")==":math:`only`"
    assert replace_dollar("$first$ is good")==":math:`first` is good"
    assert replace_dollar("so is $last$")=="so is :math:`last`"
    assert replace_dollar("and $mid$ too")=="and :math:`mid` too"
    assert replace_dollar("$first$, $mid$, $last$")==":math:`first`, :math:`mid`, :math:`last`"
    assert replace_dollar(r"dollar\$ escape")=="dollar$ escape"
    assert replace_dollar(r"dollar \$escape\$ too")=="dollar $escape$ too"
    assert replace_dollar(r"emb\ $ed$\ ed")==r"emb\ :math:`ed`\ ed"
    assert replace_dollar("$first$a")=="$first$a"
    assert replace_dollar("a$last$")=="a$last$"
    assert replace_dollar("a $mid$dle a")=="a $mid$dle a"

if __name__ == "__main__":
    test_dollar()
