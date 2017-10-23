"""
This module generates .iss file according to the local config of
the current application. Please make sure a file named "local_config.py"
exists in the current directory. Edit local_config.py according to your needs.
"""
from __future__ import print_function

import os
import sys
import string

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(root, 'sasview-install', 'Lib', 'site-packages'))
from sas.sasview import local_config

#REG_PROGRAM = """{app}\MYPROG.EXE"" ""%1"""
APPLICATION = str(local_config.__appname__ )+ '.exe'
AppName = str(local_config.__appname__ )
AppVerName = str(local_config.__appname__ )+'-'+ str(local_config.__version__)
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
INSTALLER_FILE = 'installer'

icon_path =  local_config.icon_path
media_path = local_config.media_path
test_path = local_config.test_path

def find_extension():
    """
    Describe the extensions that can be read by the current application
    """
    list_data = []
    list_app =[]
    try:

        #(ext, type, name, flags)
        from sas.sascalc.dataloader.loader import Loader
        wild_cards = Loader().get_wildcards()
        for item in wild_cards:
            #['All (*.*)|*.*']
            file_type, ext = string.split(item, "|*", 1)
            if ext.strip() not in ['.*', ''] and ext.strip() not in list_data:
                list_data.append((ext, 'string', file_type))
    except Exception:
        pass
    try:
        file_type, ext = string.split(local_config.APPLICATION_WLIST, "|*", 1)
        if ext.strip() not in ['.', ''] and ext.strip() not in list_app:
            list_app.append((ext, 'string', file_type))
    except Exception:
        pass
    try:
        for item in local_config.PLUGINS_WLIST:
            file_type, ext = string.split(item, "|*", 1)
            if ext.strip() not in ['.', ''] and ext.strip() not in list_app:
                list_app.append((ext, 'string', file_type))
    except Exception:
        pass
    return list_data, list_app
DATA_EXTENSION, APP_EXTENSION = find_extension()

def write_registry(data_extension=None, app_extension=None):
    """
    create file association for windows.
    Allow open file on double click
    """
    msg = ""
    if data_extension is not None and data_extension:
        openwithlist = "OpenWithList\%s" % str(APPLICATION)
        msg = "\n\n[Registry]\n"
        for (ext, type, _) in data_extension:
            list = os.path.join(ext, openwithlist)
            msg +=  """Root: HKCR;\tSubkey: "%s";\t""" % str(list)
            msg += """ Flags: %s""" % str('uninsdeletekey noerror')
            msg += "\n"
        #list the file on right-click
        msg += """Root: HKCR; Subkey: "applications\%s\shell\open\command";\t"""\
                              %  str(APPLICATION)
        msg += """ValueType: %s; """ % str('string')
        msg += """ValueName: "%s";\t""" %str('')
        msg += """ValueData: \"""{app}\%s""  ""%s1\"""; \t"""% (str(APPLICATION),
                                                          str('%'))
        msg += """ Flags: %s""" % str('uninsdeletevalue noerror')
        msg += "\n"
        user_list = "Software\Classes"
        for (ext, type, _) in data_extension:
            list = os.path.join(user_list, ext, openwithlist)
            msg +=  """Root: HKCU;\tSubkey: "%s";\t""" % str(list)
            msg += """ Flags: %s""" % str('uninsdeletekey noerror')
            msg += "\n"
        #list the file on right-click
        user_list = os.path.join("Software", "Classes", "applications")
        msg += """Root: HKCU; Subkey: "%s\%s\shell\open\command";\t"""\
                              %  (str(user_list), str(APPLICATION))
        msg += """ValueType: %s; """ % str('string')
        msg += """ValueName: "%s";\t""" %str('')
        msg += """ValueData: \"""{app}\%s""  ""%s1\"""; \t"""% (str(APPLICATION),
                                                          str('%'))
        msg += """ Flags: %s""" % str('uninsdeletevalue noerror')
        msg += "\n"
    if app_extension is not None and app_extension:
        for (ext, type, _) in app_extension:
            msg +=  """Root: HKCR;\tSubkey: "%s";\t""" % str(ext)
            msg += """ValueType: %s;\t""" % str(type)
            #file type empty set the current application as the default
            #reader for this file. change the value of file_type to another
            #string modify the default reader
            file_type = ''
            msg += """ValueName: "%s";\t""" % str('')
            msg += """ValueData: "{app}\%s";\t""" % str(APPLICATION)
            msg += """ Flags: %s""" % str('uninsdeletevalue  noerror')
            msg += "\n"
    msg += """Root: HKCR; Subkey: "{app}\%s";\t""" % str(APPLICATION)
    msg += """ValueType: %s; """ % str('string')
    msg += """ValueName: "%s";\t""" % str('')
    msg += """ValueData: "{app}\%s";\t""" % str("SasView File")
    msg += """ Flags: %s \t""" % str("uninsdeletekey  noerror")
    msg += "\n"

    #execute the file on double-click
    msg += """Root: HKCR; Subkey: "{app}\%s\shell\open\command";\t"""  %  str(APPLICATION)
    msg += """ValueType: %s; """ % str('string')
    msg += """ValueName: "%s";\t""" %str('')
    msg += """ValueData: \"""{app}\%s""  ""%s1\""";\t"""% (str(APPLICATION),
                                                          str('%'))
    msg += """ Flags: %s \t""" % str("uninsdeletevalue noerror")
    msg += "\n"
    #create default icon
    msg += """Root: HKCR; Subkey: "{app}\%s";\t""" % str(SetupIconFile)
    msg += """ValueType: %s; """ % str('string')
    msg += """ValueName: "%s";\t""" % str('')
    msg += """ValueData: "{app}\%s,0";\t""" % str(APPLICATION)
    msg += """ Flags: %s \t""" % str("uninsdeletevalue noerror")
    msg += "\n"


    #SASVIEWPATH
    msg += """Root: HKLM; Subkey: "%s";\t"""  %  str('SYSTEM\CurrentControlSet\Control\Session Manager\Environment')
    msg += """ValueType: %s; """ % str('expandsz')
    msg += """ValueName: "%s";\t""" % str('SASVIEWPATH')
    msg += """ValueData: "{app}";\t"""
    msg += """ Flags: %s""" % str('uninsdeletevalue noerror')
    msg += "\n"

    #PATH
    msg += """; Write to PATH (below) is disabled; need more tests\n"""
    msg += """;Root: HKCU; Subkey: "%s";\t"""  %  str('Environment')
    msg += """ValueType: %s; """ % str('expandsz')
    msg += """ValueName: "%s";\t""" % str('PATH')
    msg += """ValueData: "%s;{olddata}";\t""" % str('%SASVIEWPATH%')
    msg += """ Check: %s""" % str('NeedsAddPath()')
    msg += "\n"

    return msg

def write_languages(languages=('english',), msfile="compiler:Default.isl"):
    """
    define the language of the application
    """
    msg = ''
    if languages:
        msg = "\n\n[Languages]\n"
        for lang in languages:
            msg += """Name: "%s";\tMessagesFile: "%s"\n""" % (str(lang), str(msfile))
    return msg

def write_tasks():
    """
    create desktop icon
    """
    msg = """\n\n[Tasks]\n"""
    msg += """Name: "desktopicon";\tDescription: "{cm:CreateDesktopIcon}";\t"""
    msg += """GroupDescription: "{cm:AdditionalIcons}";\tFlags: unchecked\n"""
    msg += """Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}";\t"""
    msg += """GroupDescription: "{cm:AdditionalIcons}";\n"""
    return msg

dist_path = "dist"
def write_file():
    """
    copy some data files
    """
    msg = "\n\n[Files]\n"
    msg += """Source: "%s\%s";\t""" % (dist_path, str(APPLICATION))
    msg += """DestDir: "{app}";\tFlags: ignoreversion\n"""
    msg += """Source: "dist\*";\tDestDir: "{app}";\t"""
    msg += """Flags: ignoreversion recursesubdirs createallsubdirs\n"""
    msg += """Source: "dist\plugin_models\*";\tDestDir: "{userdesktop}\..\.sasview\plugin_models";\t"""
    msg += """Flags: recursesubdirs createallsubdirs\n"""
    msg += """Source: "dist\compiled_models\*";\tDestDir: "{userdesktop}\..\.sasmodels\compiled_models";\t"""
    msg += """Flags: recursesubdirs createallsubdirs\n"""
    msg += """Source: "dist\config\custom_config.py";\tDestDir: "{userdesktop}\..\.sasview\config";\t"""
    msg += """Flags: recursesubdirs createallsubdirs\n"""
    #msg += """Source: "dist\default_categories.json";    DestDir: "{userdesktop}\..\.sasview";\t"""
    #msg += """DestName: "categories.json";\n"""
    msg += """;\tNOTE: Don't use "Flags: ignoreversion" on any shared system files"""
    return msg

def write_icon():
    """
    Create application icon
    """
    msg = """\n\n[Icons]\n"""
    msg += """Name: "{group}\%s";\t""" % str(AppName)
    msg += """Filename: "{app}\%s";\t"""  % str(APPLICATION)
    msg += """WorkingDir: "{app}"; IconFilename: "{app}\images\\ball.ico" \n"""
    msg += """Name: "{group}\{cm:UninstallProgram, %s}";\t""" % str(AppName)
    msg += """ Filename: "{uninstallexe}" \n"""
    msg += """Name: "{commondesktop}\%s";\t""" % str(AppVerName)
    msg += """Filename: "{app}\%s";\t""" % str(APPLICATION)
    msg += """Tasks: desktopicon; WorkingDir: "{app}" ; IconFilename: "{app}\images\\ball.ico" \n"""
    msg += """Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\%s";\t""" % str(AppVerName)
    msg += """Filename: "{app}\%s";\t""" % str(APPLICATION)
    msg += """Tasks: quicklaunchicon; WorkingDir: "{app}"; IconFilename: "{app}\images\\ball.ico" \n"""
    return msg

def write_run():
    """
    execute some file
    """
    msg = """\n\n[Run]\n"""
    msg += """Filename: "{app}\%s";\t""" % str(APPLICATION)
    msg += """Description: "{cm:LaunchProgram, %s}";\t""" %str(AppName)
    msg += """Flags: nowait postinstall skipifsilent\n"""
    msg += """; Install the Microsoft C++ DLL redistributable package if it is """
    msg += """provided and the DLLs are not present on the target system.\n"""
    msg += """; Note that the redistributable package is included if the app was """
    msg += """built using Python 2.6 or 2.7, but not with 2.5.\n"""
    msg += """; Parameter options:\n"""
    msg += """; - for silent install use: "/q"\n"""
    msg += """; - for silent install with progress bar use: "/qb"\n"""
    msg += """; - for silent install with progress bar but disallow """
    msg += """cancellation of operation use: "/qb!"\n"""
    msg += """; Note that we do not use the postinstall flag as this would """
    msg += """display a checkbox and thus require the user to decide what to do.\n"""
    msg += """;Filename: "{app}\\vcredist_x86.exe"; Parameters: "/qb!"; """
    msg += """WorkingDir: "{tmp}"; StatusMsg: "Installing Microsoft Visual """
    msg += """C++ 2008 Redistributable Package ..."; Check: InstallVC90CRT(); """
    msg += """Flags: skipifdoesntexist waituntilterminated\n"""
    return msg

def write_dirs():
    """
    Define Dir permission
    """
    msg = """\n\n[Dirs]\n"""
    msg += """Name: "{app}\%s";\t""" % str('')
    msg += """Permissions: everyone-modify\t"""
    msg += """\n"""
    return msg

def write_code():
    """
    Code that checks the existing path and snaviewpath
    in the environmental viriables/PATH
    """
    msg = """\n\n[Code]\n"""
    msg += """function InstallVC90CRT(): Boolean;\n"""
    msg += """begin\n"""
    msg += """    Result := not DirExists('C:\WINDOWS\WinSxS\\x86_Microsoft.VC90."""
    msg += """CRT_1fc8b3b9a1e18e3b_9.0.21022.8_x-ww_d08d0375');\n"""
    msg += """end;\n\n"""
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
    msg += """  newpath := '%SASVIEWPATH%';\n"""
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

def write_uninstalldelete():
    """
    Define uninstalldelete
    """
    msg = """\n[UninstallDelete]\n"""
    msg += """; Delete directories and files that are dynamically created by """
    msg += """the application (i.e. at runtime).\n"""
    msg += """Type: filesandordirs; Name: "{app}\.matplotlib"\n"""
    msg += """Type: files; Name: "{app}\*.*"\n"""
    msg += """; The following is a workaround for the case where the """
    msg += """application is installed and uninstalled but the\n"""
    msg += """;{app} directory is not deleted because it has user files.  """
    msg += """Then the application is installed into the\n"""
    msg += """; existing directory, user files are deleted, and the """
    msg += """application is un-installed again.  Without the\n"""
    msg += """; directive below, {app} will not be deleted because Inno Setup """
    msg += """did not create it during the previous\n"""
    msg += """; installation.\n"""
    msg += """Type: dirifempty; Name: "{app}"\n"""
    msg += """\n"""
    return msg

def generate_installer():
    """
    """
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
    TEMPLATE += "UsePreviousAppDir=no\n"

    TEMPLATE += write_registry(data_extension=DATA_EXTENSION,
                                app_extension=APP_EXTENSION)
    TEMPLATE += write_languages()
    TEMPLATE += write_tasks()
    TEMPLATE += write_file()
    TEMPLATE += write_icon()
    TEMPLATE += write_run()
    TEMPLATE += write_dirs()
    TEMPLATE += write_code()
    TEMPLATE += write_uninstalldelete()
    path = '%s.iss' % str(INSTALLER_FILE)
    f = open(path,'w')
    f.write(TEMPLATE)
    f.close()
    print("Generate Inno setup installer script complete")
    print("A new file %s.iss should be created.Please refresh your directory" % str(INSTALLER_FILE))

if __name__ == "__main__":
    generate_installer()
