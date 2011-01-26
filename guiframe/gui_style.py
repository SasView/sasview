
"""
Provide the style for guiframe
"""

class GUIFRAME:
    MANAGER_ON = 1
    FLOATING_PANEL = 2
    FIXED_PANEL = 3
    PLOTTIN_ON = 4
    DATALOADER_ON = 5
    SINGLE_APPLICATION = 6
    MULTIPLE_APPLICATIONS = 7
    
    DEFAULT_STYLE = 8

if __name__ == "__main__":
  
    print GUIFRAME.DEFAULT_STYLE
    print GUIFRAME.FLOATING_PANEL
 
    value = GUIFRAME.MANAGER_ON|GUIFRAME.DATALOADER_ON
    print value
    print value in [1,2]
    print value in [5,2]
    print value in [GUIFRAME.MANAGER_ON,GUIFRAME.DATALOADER_ON]
