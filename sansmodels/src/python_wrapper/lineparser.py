#!/usr/bin/env python
""" WrapperGenerator class to generate model code automatically.
"""

import os, sys,re
def split_list(separator, mylist, n=0):
    """
        @return a list of string without white space of separator
        @param separator: the string to remove
    """
    list=[]
    for item in mylist:
        if re.search( separator,item)!=None:
            if n >0:
                word =re.split(separator,item,int(n))
            else:
                word =re.split( separator,item)
            for new_item in word: 
                if new_item.lstrip().rstrip() !='':
                    list.append(new_item.lstrip().rstrip())
    return list
def split_text(separator, string1, n=0):
    """
        @return a list of string without white space of separator
        @param separator: the string to remove
    """
    list=[]
    if re.search( separator,string1)!=None:
        if n >0:
            word =re.split(separator,string1,int(n))
        else:
            word =re.split(separator,string1)
        for item in word: 
            if item.lstrip().rstrip() !='':
                list.append(item.lstrip().rstrip())
    return list
def look_for_tag( string1,begin, end=None ):
    """
        @note: this method  remove the begin and end tags given by the user
        from the string .
        @param begin: the initial tag
        @param end: the final tag
        @param string: the string to check
        @return: begin_flag==True if begin was found,
         end_flag==if end was found else return false, false
         
    """
    begin_flag= False
    end_flag= False
    if  re.search( begin,string1)!=None:
        begin_flag= True
    if end !=None:
        if  re.search(end,string1)!=None:
            end_flag= True
    return begin_flag, end_flag


  
def readhelper(lines, key, key2, key3 , file):
  
    temp=""
    # flag to found key
    find_fixed= False
    find_key2=False
    find_key3=False
    listtofill=[]
    for line in lines:
        if line.count(key.lstrip().rstrip())>0 :#[FIXED]= .....
            try:
                find_fixed= True
                index = line.index(key)
                toks  = line[index:].split("=",1 )
                temp  = toks[1].lstrip().rstrip()
                find_key2, find_key3=look_for_tag( string1=temp,
                                                   begin=key2, end=key3 )
                if find_key2 and find_key3:
                    temp1=[]
                    temp2=[]
                    temp3=[]
                    temp4=[]
                    temp1=split_text(separator=key2, string1=temp)
                    temp2=split_list(separator=key3, mylist=temp1)
                    temp3=split_list(separator=';', mylist=temp2)
                    temp4=split_list(separator=',', mylist=temp3)
                    listtofill= temp3 + temp4
                    return listtofill
                    
                    
                elif find_key2 and not find_key3:
                    ## [key]= key2(<text>)
                    ##        ....
                    ##        key3(<text>)
                    temp1=[]
                    temp2=[]
                    temp3=[]
                    temp4=[]
                    ## remove key2= <text>
                    temp1=split_text(separator=key2, string1=temp)
                    
                    ## split ";" first
                    temp3=split_list(separator=';', mylist=temp1)
                    temp4=split_list(separator=',', mylist=temp3)
            
                    if len(temp3 + temp4)==0:
                        # [FIXED]=  only one param
                        listtofill+= temp1
                    listtofill += temp3+temp4 
               
                elif not find_key2 and not find_key3 :
                    ## [key]= param done looking
                    temp3=[]
                    temp4=[]
                    if look_for_tag( string1=temp,begin=";")[0]:
                        ## split ";" first
                        temp3=split_text(separator=';',string1=temp)
                        temp4=split_list(separator=',', mylist=temp3)
                    else:
                        ## slip "," first
                        temp3=split_text(separator=',',string1=temp)
                        temp4=split_list(separator=';', mylist=temp3)
                    if len(temp3+ temp4)==0:
                        ## [FIXED]=  only one param
                        if temp.lstrip().rstrip()!="":
                            listtofill= [temp.lstrip().rstrip()]
                        
                    listtofill += temp3+temp4
                    return listtofill
            except:
                raise ValueError, "Could not parse file %s" % file
        
        elif find_fixed :
            if not find_key2:
                raise ValueError, "Could not parse file %s" % file
            if find_key3:
                temp1=[]
                temp2=[]
                temp3=[]
                temp4=[]
                temp5=[]
               
                temp1=split_text(separator=key3, string1=line)
                temp2=split_list(separator='//',mylist=temp1)
                temp5=split_list(separator="\*",mylist=temp1)
                
                if len(temp5)>0:
                    temp3=split_list(separator=';',mylist=temp5)
                    temp4=split_list(separator=',', mylist=temp5)
                elif len(temp2)>0:
                    temp3=split_list(separator=';',mylist=temp2)
                    temp4=split_list(separator=',', mylist=temp2)
                else:
                    temp3=split_list(separator=';',mylist=temp1)
                    temp4=split_list(separator=',', mylist=temp1)
                
                if len(temp3 + temp4)==0:# [FIXED]=  only one param
                    listtofill += temp1
                listtofill+=temp3+temp4 #   
                break
            
            else:
                temp2=split_text(separator='//', string1=line)
                temp5=split_text(separator="\*", string1=line)
                if len(temp5)>0:
                    temp3=split_list(separator=';', mylist=temp5)
                    temp4=split_list(separator=',', mylist=temp5)
                elif len(temp2)>0:
                    temp3=split_list(separator=';', mylist=temp2)
                    temp4=split_list(separator=',', mylist=temp2)
                else:
                    if look_for_tag( string1=line,begin=";")[0]:# split ";" first
                        temp3=split_text(separator=';', string1=line)
                        temp4=split_list(separator=',', mylist=temp3)
                    else:
                        temp3=split_text(separator=',', string1=line)# slip "," first
                        temp4=split_list(separator=';', mylist=temp3)
                if len(temp3+ temp4)==0:# [FIXED]=  only one param
                    if line.lstrip().rstrip()!="":
                        listtofill=[line.lstrip().rstrip()]
                listtofill+=temp3+temp4 #
                break
    return listtofill
   
# main
if __name__ == '__main__':
    
    # Read file
    name= "sphere.h"
    f = open("..\include\core_shell.h",'r')
    buf = f.read()
  
    lines = buf.split('\n')
  
    ## Catch Fixed parameters
    key = "[FIXED]"
    #open item in this case Fixed
    text='text'
    key2="<%s>"%text.lower()
    # close an item in this case fixed
    text='TexT'
    key3="</%s>"%text.lower()
    listto=[]
   
    listto= readhelper(lines, key, key2,key3, file=name)
    print "fixed parameters\n ",listto
    print 
    
   
    key0="[ORIENTATION_PARAMS]"
   
    listto=[]
    listto= readhelper(lines,key0, key2,key3, file=name)
    print "orientation parameters\n ",listto
    print 
    f.close()
# End of file        