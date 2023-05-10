from PySide6 import QtWidgets
import syntax_highlight

app = QtWidgets.QApplication([])
editor = QtWidgets.QPlainTextEdit()
editor.setStyleSheet("""QPlainTextEdit{
	font-family:'Consolas'; 
	color: #ccc; 
	background-color: #2b2b2b;}""")
highlight = syntax_highlight.PythonHighlighter(editor.document())
editor.show()

# Load syntax.py into the editor for demo purposes
infile = open('syntax_highlight.py', 'r')
editor.setPlainText(infile.read())

app.exec_()