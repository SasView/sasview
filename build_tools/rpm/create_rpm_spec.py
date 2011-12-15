import sys
sys.path.append("..")
import get_version

def replaceToken(line, key, value): #pylint: disable-msg=R0201
    """ Replace a token in the template file 
        @param line: line of text to inspect
        @param key: token to look for
        @param value: string value to replace the token with
        @return: new string value
    """
    lenkey = len(key)
    newline = line
   
    while newline.count(key)>0:
        index = newline.index(key)
        newline = newline[:index]+value+newline[index+lenkey:]
    
    return newline


input=open("sansview.spec.template",'r')
output=open("sansview.spec",'w')

buf = input.read()
lines = buf.split('\n')
for l in lines:
    new_line = replaceToken(l, "[VERSION]", get_version.__version__)
    new_line = replaceToken(new_line, "[REVISION]", get_version.__revision__)
    output.write(new_line+'\n')
    
input.close()
output.close()
    


