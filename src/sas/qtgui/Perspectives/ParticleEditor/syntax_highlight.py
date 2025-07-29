"""


Modified from: art1415926535/PyQt5-syntax-highlighting on github

It's not great, should all really be implemented as a finite state machine with a stack

"""

from PySide6.QtCore import QRegularExpression, QRegularExpressionMatchIterator
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat


def format(color, style=''):
    """
    Return a QTextCharFormat with the given attributes.
    """
    _color = QColor()
    if type(color) is not str:
        _color.setRgb(color[0], color[1], color[2])
    else:
        _color.setNamedColor(color)

    _format = QTextCharFormat()
    _format.setForeground(_color)
    if 'bold' in style:
        _format.setFontWeight(QFont.Bold)
    if 'italic' in style:
        _format.setFontItalic(True)

    return _format


# Syntax styles that can be shared by all languages

STYLES = {
    'keyword': format([200, 120, 50], 'bold'),
    'operator': format([150, 150, 150]),
    'brace': format('darkGray'),
    'defclass': format([220, 220, 255], 'bold'),
    'string': format([20, 110, 100]),
    'string2': format([30, 120, 110]),
    'comment': format([128, 128, 128]),
    'self': format([150, 85, 140], 'italic'),
    'numbers': format([100, 150, 190]),
    'special': format([90, 80, 200], 'bold')
}


class PythonHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for the Python language.
    """
    # Python keywords


    keywords = [
        'and', 'assert', 'break', 'class', 'continue', 'def',
        'del', 'elif', 'else', 'except', 'exec', 'finally',
        'for', 'from', 'global', 'if', 'import', 'in',
        'is', 'lambda', 'not', 'or', 'pass', 'print',
        'raise', 'return', 'try', 'while', 'yield',
        'None', 'True', 'False',
    ]

    special = [
        'sld', 'solvent_sld', 'magnetism'
    ]

    # Python operators
    operators = [
        '=',
        # Comparison
        '==', '!=', '<', '<=', '>', '>=',
        # Arithmetic
        r'\+', '-', r'\*', '/', '//', r'\%', r'\*\*',
        # In-place
        r'\+=', '-=', r'\*=', '/=', r'\%=',
        # Bitwise
        r'\^', r'\|', r'\&', r'\~', '>>', '<<',
    ]

    # Python braces
    braces = [
        r'\{', r'\}', r'\(', r'\)', r'\[', r'\]',
    ]

    def __init__(self, document):
        QSyntaxHighlighter.__init__(self, document)

        # Multi-line strings (expression, flag, style)
        # FIXME: The triple-quotes in these two lines will mess up the
        # syntax highlighting from this point onward
        self.tri_single = (QRegularExpression("'''"), 1, STYLES['string2'])
        self.tri_double = (QRegularExpression('"""'), 2, STYLES['string2'])

        rules = []

        # Keyword, operator, and brace rules
        rules += [(r'\b%s\b' % w, 0, STYLES['keyword'])
                  for w in PythonHighlighter.keywords]
        rules += [(r'%s' % o, 0, STYLES['operator'])
                  for o in PythonHighlighter.operators]
        rules += [(r'%s' % b, 0, STYLES['brace'])
                  for b in PythonHighlighter.braces]

        # All other rules
        rules += [
            # 'self'
            (r'\bself\b', 0, STYLES['self']),

            # Double-quoted string, possibly containing escape sequences
            (r'[rf]?"[^"\\]*(\\.[^"\\]*)*"', 0, STYLES['string']),
            # Single-quoted string, possibly containing escape sequences
            (r"[rf]?'[^'\\]*(\\.[^'\\]*)*'", 0, STYLES['string']),

            # From '#' until a newline
            (r'#[^\n]*', 0, STYLES['comment']),

            # Numeric literals
            (r'\b[+-]?[0-9]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', 0, STYLES['numbers']),
        ]

        rules += [(r'\b%s\b' % w, 0, STYLES['special'])
                    for w in PythonHighlighter.special]

        # Build a QRegExp for each pattern
        self.rules = [(QRegularExpression(pat), index, fmt)
                      for (pat, index, fmt) in rules]


    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text.
        """

        # Go through each of the rules and each of the matches setting the highlighting
        for expression, nth, format in self.rules:
            matchIterator = QRegularExpressionMatchIterator(expression.globalMatch(text))
            while matchIterator.hasNext():
                match = matchIterator.next()
                index = match.capturedStart()
                length = match.capturedLength()
                self.setFormat(index, length, format)

        # def and class
        #
        # # 'def' followed by an identifier
        # (r'\bdef\b\s*(\w+)', 1, STYLES['defclass']),
        # # 'class' followed by an identifier
        # (r'\bclass\b\s*(\w+)', 1, STYLES['defclass']),

        # Multiblock comments

        # Find all the tripple quotes

        doubleMatchIterator = QRegularExpressionMatchIterator(self.tri_double[0].globalMatch(text))
        singleMatchIterator = QRegularExpressionMatchIterator(self.tri_single[0].globalMatch(text))

        doubleMatches = []
        while doubleMatchIterator.hasNext():
            doubleMatches.append((
                self.tri_double[1],
                doubleMatchIterator.next(),
                self.tri_double[2]))

        singleMatches = []
        while singleMatchIterator.hasNext():
            singleMatches.append((
                self.tri_single[1],
                singleMatchIterator.next(),
                self.tri_single[2]))

        allMatches = sorted(
            singleMatches + doubleMatches,
            key=lambda x: x[1].capturedStart())

        # Step through the matches

        state = self.previousBlockState()
        start_index = 0

        for in_state, match, style in allMatches:

            if state == in_state:
                # Comment end

                state = -1
                index = match.capturedStart()
                length = match.capturedLength()
                end_index = index + length

                self.setFormat(start_index, end_index, style)

                start_index = end_index

            elif state == -1:
                # Comment start

                state = in_state
                start_index = match.capturedStart()


        # format rest of block
        end_index = len(text)
        if state != -1:
            if len(allMatches) > 0:
                self.setFormat(start_index, end_index, allMatches[-1][2])
            else:
                if state == self.tri_single[1]:
                    self.setFormat(0, end_index, self.tri_single[2])
                elif state == self.tri_double[1]:
                    self.setFormat(0, end_index, self.tri_double[2])

        # set block state
        self.setCurrentBlockState(state)

