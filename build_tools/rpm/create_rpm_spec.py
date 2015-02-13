import sys
sys.path.append("..")
import get_version

revision = get_version.__revision__

# If the revision we got from get_version is None, it's because it's
# release. Otherwise, use the input revision if provided
if len(sys.argv)>1 and revision is not None:
    try:
        revision = int(sys.argv[1].strip())
    except:
        print "Could not process bad revision number: %s" % str(sys.argv)

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

input=open("sasview.spec.template",'r')
output=open("sasview.spec",'w')

buf = input.read()
lines = buf.split('\n')
for l in lines:
    new_line = replaceToken(l, "[VERSION]", get_version.__version__)
    new_line = replaceToken(new_line, "[REVISION]", str(revision))
    output.write(new_line+'\n')
    
input.close()
output.close()
    


