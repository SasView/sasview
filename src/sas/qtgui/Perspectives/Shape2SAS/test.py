import re

text = "COMZ1 =COMX1+COMY1 + 50"
before_eq, after_eq = text.split('=')

# Find all occurrences of the name "Alice" that are preceded by a space or start of the string
Right = re.findall(r'(?<=)[a-zA-Z_]\w*\b', after_eq)
Left = re.findall(r'(?<=)[a-zA-Z_]\w*\b', before_eq)

print(Right)
print(Left)