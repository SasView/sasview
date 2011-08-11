"""
This module generates .ss file according to the local config of
the current application. Please make sure a file named "local_config.py"
exists in the current directory. Edit local_config.py according to your needs.
"""
import local_config
import os 
import string

REG_PROGRAM = """{app}\MYPROG.EXE"" ""%1"""
APPLICATION = str(local_config.__appname__ )+ '.exe'
AppName  = str(local_config.__appname__ ) # + '-'+ str(local_config.__version__)
AppVerName = str(local_config.__appname__ ) + '-'+ str(local_config.__version__)
Dev = ''
if AppVerName.lower().count('dev') > 0:
    Dev = '-Dev'
AppPublisher = local_config._copyright
AppPublisherURL = local_config._homepage
AppSupportURL = local_config._homepage
AppUpdatesURL = local_config._homepage
ChangesEnvironment = 'true'
DefaultDirName = os.path.join("{pf}" , AppName+Dev) 
DefaultGroupName = os.path.join(local_config.DefaultGroupName, AppVerName)
                                
OutputBaseFilename = local_config.OutputBaseFilename
SetupIconFile = local_config.SetupIconFile_win
LicenseFile = 'license.txt'
DisableProgramGroupPage = 'yes'
Compression = 'lzma'
SolidCompression = 'yes'
PrivilegesRequired = 'none'
INSTALLER_FILE = 'installer_new'
#find extension for windows file assocation
#extension list need to be modified for each application

def find_extension():
    """
    Describe the extensions that can be read by the current application
    """
    try:
        list = []
        #(ext, type, name, flags)
        from sans.dataloader.loader import Loader
        wild_cards = Loader().get_wildcards()
        for item in wild_cards:
            #['All (*.*)|*.*']
            file_type, ext = string.split(item, "|*", 1)
            if ext.strip() not in ['.*', ''] and ext.strip() not in list:
                list.append((ext, 'string', file_type))
    except:
        pass
    try:
        file_type, ext = string.split(local_config.APPLICATION_WLIST, "|*", 1)
        if ext.strip() not in ['.', ''] and ext.strip() not in list:
            list.append((ext, 'string', file_type))
    except:
        pass
    try:
        for item in local_config.PLUGINS_WLIST:
            file_type, ext = string.split(item, "|*", 1)
            if ext.strip() not in ['.', ''] and ext.strip() not in list:
                list.append((ext, 'string', file_type)) 
    except:
        pass
    return list
EXTENSION = find_extension()
    
def write_registry(extension=None):
    """
    create file association for windows.
    Allow open file on double click
    """
    msg = ""
    if extension is not None and extension:
        msg = "\n\n[Registry]\n"
        for (ext, type, _) in extension:
            msg +=  """Root: HKCR;\tSubkey: "%s";\t""" % str(ext)
            msg += """ValueType: %s;\t""" % str(type)
            #file type empty set the current application as the default 
            #reader for this file. change the value of file_type to another
            #string modify the default reader
            file_type = ''
            msg += """ValueName: "%s";\t""" % str('')
            msg += """ValueData: "{app}\%s";\t""" % str(APPLICATION)
            msg += """ Flags: %s""" % str('uninsdeletevalue')
            msg += "\n"
     
        #create default icon
        msg += """Root: HKCR; Subkey: "{app}\%s";\t""" % str(SetupIconFile)
        msg += """ValueType: %s; """ % str('string')
        msg += """ValueName: "%s";\t""" % str('') 
        msg += """ValueData: "{app}\%s,0"\n""" % str(APPLICATION)
        
        #execute the file on double-click
        msg += """Root: HKCR; Subkey: "{app}\%s\shell\open\command";\t"""  %  str(APPLICATION)
        msg += """ValueType: %s; """ % str('string')
        msg += """ValueName: "%s";\t""" %str('') 
        msg += """ValueData: \"""{app}\%s""  ""%s1\"""\n"""% (str(APPLICATION),
                                                              str('%'))
        
        #SANSVIEWPATH
        msg += """Root: HKLM; Subkey: "%s";\t"""  %  str('SYSTEM\CurrentControlSet\Control\Session Manager\Environment')
        msg += """ValueType: %s; """ % str('expandsz')
        msg += """ValueName: "%s";\t""" % str('SANSVIEWPATH') 
        msg += """ValueData: "{app}";\t"""
        msg += """ Flags: %s""" % str('uninsdeletevalue')
        msg += "\n"
        
        #PATH
        msg += """; Write to PATH (below) is disabled; need more work\n"""
        msg += """;Root: HKCU; Subkey: "%s";\t"""  %  str('Environment')
        msg += """ValueType: %s; """ % str('expandsz')
        msg += """ValueName: "%s";\t""" % str('PATH') 
        msg += """ValueData: "%s;{olddata}";\t""" % str('%SANSVIEWPATH%')
        msg += """ Check: %s""" % str('NeedsAddPath()')
        msg += "\n"
        
    return msg

def write_language(language=['english'], msfile="compiler:Default.isl"):  
    """
    define the language of the application
    """ 
    msg = ''
    if language:
        msg = "\n\n[Languages]\n"
        for lang in language:
            msg += """Name: "%s";\tMessagesFile: "%s"\n""" % (str(lang), 
                                                           str(msfile))
    return msg 

def write_tasks():
    """
    create desktop icon
    """
    msg = """\n\n[Tasks]\n"""
    msg += """Name: "desktopicon";\tDescription: "{cm:CreateDesktopIcon}";\t"""
    msg += """GroupDescription: "{cm:AdditionalIcons}";\tFlags: unchecked\n"""
    return msg

def write_file():
    """
    copy some data files
    """
    msg = "\n\n[Files]\n"
    msg += """Source: "dist\%s";\t""" % str(APPLICATION)
    msg += """DestDir: "{app}";\tFlags: ignoreversion\n"""
    msg += """Source: "dist\*";\tDestDir: "{app}";\t"""
    msg += """Flags: ignoreversion recursesubdirs createallsubdirs\n"""
    msg += """Source: "images\*";\tDestDir: "{app}\%s";\t""" % str("images")
    msg += """Flags: ignoreversion recursesubdirs createallsubdirs\n"""
    msg += """Source: "test\*";\tDestDir: "{app}\%s";\t""" % str("test")
    msg += """Flags: ignoreversion recursesubdirs createallsubdirs\n"""
    msg += """;\tNOTE: Don't use "Flags: ignoreversion" on any shared system files"""
    return msg

def write_icon():
    """
    Create application icon
    """
    msg = """\n\n[Icons]\n"""
    msg += """Name: "{group}\%s";\t""" % str(AppName)
    msg += """Filename: "{app}\%s";\t"""  % str(APPLICATION)
    msg += """WorkingDir: "{app}" \n"""
    msg += """Name: "{group}\{cm:UninstallProgram, %s}";\t""" % str(AppName)
    msg += """ Filename: "{uninstallexe}" \n"""
    msg += """Name: "{commondesktop}\%s";\t""" % str(AppVerName)
    msg += """Filename: "{app}\%s";\t""" % str(APPLICATION)
    msg += """Tasks: desktopicon; WorkingDir: "{app}" \n"""
    return msg

def write_run():
    """
    execute some file
    """
    msg = """\n\n[Run]\n"""
    msg += """Filename: "{app}\%s";\t""" % str(APPLICATION)
    msg += """Description: "{cm:LaunchProgram, %s}";\t""" %str(AppName) 
    msg += """Flags: nowait postinstall skipifsilent\n"""
    return msg

def write_code():
    """
    Code that checks the existing path and snaviewpath 
    in the environmental viriables/PATH
    """
    msg = """\n\n[Code]\n"""
    msg += """function NeedsAddPath(): boolean;\n""" 
    msg += """var\n""" 
    msg += """  oldpath: string;\n"""
    msg += """  newpath: string;\n""" 
    msg += """  pathArr:    TArrayOfString;\n""" 
    msg += """  i:        Integer;\n""" 
    msg += """begin\n""" 
    msg += """  RegQueryStringValue(HKEY_CURRENT_USER,'Environment',"""
    msg += """'PATH', oldpath)\n"""
    msg += """  oldpath := oldpath + ';';\n"""
    msg += """  newpath := '%SANSVIEWPATH%';\n"""
    msg += """  i := 0;\n"""
    msg += """  while (Pos(';', oldpath) > 0) do begin\n"""
    msg += """    SetArrayLength(pathArr, i+1);\n"""
    msg += """    pathArr[i] := Copy(oldpath, 0, Pos(';', oldpath)-1);\n"""
    msg += """    oldpath := Copy(oldpath, Pos(';', oldpath)+1,"""
    msg += """ Length(oldpath));\n"""
    msg += """    i := i + 1;\n"""
    msg += """    // Check if current directory matches app dir\n"""
    msg += """    if newpath = pathArr[i-1] \n"""
    msg += """    then begin\n"""
    msg += """      Result := False;\n"""
    msg += """      exit;\n"""
    msg += """    end;\n"""
    msg += """  end;\n"""
    msg += """  Result := True;\n"""
    msg += """end;\n"""
    msg += """\n"""
    
    
    
    
    return msg


if __name__ == "__main__":
    TEMPLATE = "\n; Script generated by the Inno Setup Script Wizard\n"
    TEMPLATE += "\n; and local_config.py located in this directory.\n "
    TEMPLATE += "; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!"
    TEMPLATE += "\n[Setup]\n\n" 
    TEMPLATE += "ChangesAssociations=%s\n" %str('yes')
    TEMPLATE += "AppName=%s\n" % str(AppName)
    TEMPLATE += "AppVerName=%s\n" % str(AppVerName)
    TEMPLATE += "AppPublisher=%s\n" % str(AppPublisher)
    TEMPLATE += "AppPublisherURL=%s\n" % str(AppPublisherURL)
    TEMPLATE += "AppSupportURL=%s\n" % str(AppSupportURL)
    TEMPLATE += "AppUpdatesURL=%s \n" % str(AppUpdatesURL)
    TEMPLATE += "ChangesEnvironment=%s \n" % str(ChangesEnvironment)
    TEMPLATE += "DefaultDirName=%s\n" % str(DefaultDirName)
    TEMPLATE += "DefaultGroupName=%s\n" % str(DefaultGroupName)
    TEMPLATE += "DisableProgramGroupPage=%s\n" % str(DisableProgramGroupPage)
    TEMPLATE += "LicenseFile=%s\n" % str(LicenseFile)
    TEMPLATE += "OutputBaseFilename=%s\n" % str(OutputBaseFilename)
    TEMPLATE += "SetupIconFile=%s\n" % str(SetupIconFile)
    TEMPLATE += "Compression=%s\n" % str(Compression)
    TEMPLATE += "SolidCompression=%s\n" % str(SolidCompression)
    TEMPLATE += "PrivilegesRequired=%s\n" % str(PrivilegesRequired)
   
    TEMPLATE += write_registry(extension=EXTENSION)
    TEMPLATE += write_language()
    TEMPLATE += write_tasks()
    TEMPLATE += write_file()
    TEMPLATE += write_icon()
    TEMPLATE += write_run()
    TEMPLATE += write_code()
    path = '%s.iss' % str(INSTALLER_FILE)
    f = open(path,'w') 
    f.write(TEMPLATE)
    f.close()
    print "Generate Inno setup installer script complete"
    print "A new file %s.iss should be created.Please refresh your directory" % str(INSTALLER_FILE)