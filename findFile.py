'''
Created on Apr 18, 2018

@author: raysm
'''
import os
import wx
import re

from filebrowsebutton import DirBrowseButtonWithHistory
from filebrowsebutton import FileBrowseButtonWithHistory
from properties import Properties
import atexit
from docutils.nodes import line


class FindFile(wx.Frame):
    """
    properties key names:
    """
    PK_DIR_START = 'dirNameStart'
    PK_DIR_HISTORY = 'dirNameHistory'       # Directories separated by ";"
    PK_FILE_NAME = 'fileName'
    PK_EXT_NAME = 'extensionName'
    PK_NOT_EXT = 'notExtensionName'
    PK_INCL_SUB_DIR = 'inclSubDir'
    PK_SEARCH_PATTERN = 'searchPattern'
    PK_REX_SEARCH_PATTERN = 'rexSearchPattern'
    PK_DISPLAY_DIR_LIST = 'display_dir_list'
    PK_DISPLAY_DIRS = 'display_dirs'
    PK_DISPLAY_FILE_LIST = 'display_file_list'
    PK_DISPLAY_FILES = 'display_files'
    PK_KEEP_PREVIOUS_FOUND = 'keep_previous_found'
        
    """
    Data types for property conversion
    """
    DT_UNKNOWN = 0
    DT_BOOLEAN = 1
    DT_STRING = 2
    DT_INT = 3
    DT_FLOAT = 4
    
    def __init__(self, *args, propFile=None, **kwargs):
        super(FindFile, self).__init__(*args, **kwargs) 
        if propFile is None:
            propFile = "FindFile.properties"
        self.propFile = propFile
        self.properties = Properties()
        if self.propFile is not None and os.path.exists(self.propFile):
            self.properties.load(open(self.propFile))   
        self.InitUI()

    def propSave(self, propFile=None):
        self.propertiesUpdate(end=True)
        if (self.properties is not None and propFile is not None):
            print("Saving properties in %s" % os.path.abspath(propFile))
            out = open(propFile, 'w')
            out_header = "findFile.properties"
            self.properties.store(out, out_header)
            out.close()
        
    def InitUI(self):    

        menubar = wx.MenuBar()
        fileMenu = wx.Menu()
        fitem = fileMenu.Append(wx.ID_EXIT, 'Quit', 'Quit application')
        menubar.Append(fileMenu, '&File')
        self.SetMenuBar(menubar)
        
        self.Bind(wx.EVT_MENU, self.OnQuit, fitem)
        self.SetSize((600, 500))
        self.SetTitle('FindFile')
        panel = wx.Panel(self)
        
        file_dir_box = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(file_dir_box)
        self.startDirectory = None
        self.dirName  = self.getProperty(FindFile.PK_DIR_START)
        initialValue = self.dirName
        if self.dirName is None:
            self.dirName = "."
            initialValue = ""
        dir_history  = self.getProperty(FindFile.PK_DIR_HISTORY)
        self.dirHistoryList = []
        if dir_history is not None:
            self.dirHistoryList = dir_history.split(';')
                 
        dir_name_box = wx.BoxSizer(wx.HORIZONTAL)
        self.dirNameBrowse = DirBrowseButtonWithHistory(panel,
                    labelText = 'Directory:',
                    history = self.dirHistoryList,
                    size = (500, wx.DefaultSize.height),
                    startDirectory = self.dirName,
                    initialValue = initialValue,
                    changeCallback=self.OnDirChange)
        self.OnDirChange(None)      # Force full update
        
        isInclSubDir = self.getProperty(FindFile.PK_INCL_SUB_DIR, datatype=FindFile.DT_BOOLEAN)
        if isInclSubDir is None:
            isInclSubDir = False
        self.isInclSubDir = isInclSubDir
        self.isInclSubDirCkbox = wx.CheckBox(panel, label="Incl Sub")
        self.isInclSubDirCkbox.SetValue(self.isInclSubDir)        # Don't know why the constructor shows no value=
        self.isInclSubDirCkbox.Bind(wx.EVT_CHECKBOX, self.OnInclSubChange)
        
        dir_name_box.Add(self.dirNameBrowse)
        dir_name_box.Add(self.isInclSubDirCkbox, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 5)
        
        file_dir_box.Add(dir_name_box, 0,  wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 5)
 
        self.fileName = self.getProperty(FindFile.PK_FILE_NAME)
        initial_file_name = self.fileName
        
        self.fileExtList = []                      # Array of file extensions (without ".")
        self.extName = self.getProperty(FindFile.PK_EXT_NAME)
        initial_ext_name = self.extName
        
        if self.fileName is None:
            initial_file_name = ""
        if self.extName is None:
            initial_ext_name = ""
                
        file_box = wx.BoxSizer(wx.HORIZONTAL)
        self.fileNameBrowse = FileBrowseButtonWithHistory(panel,
                    labelText='File:',
                    size = (300, wx.DefaultSize.height),
                    startDirectory = self.dirName,
                    initialValue = initial_file_name)
        file_box.Add(self.fileNameBrowse)
        file_ext_label = wx.StaticText(panel, -1, label="Extensions:")
        self.fileExtCtl = wx.TextCtrl(panel, value=initial_ext_name, style=wx.TE_PROCESS_ENTER)
        self.OnExtChange(None)      # Setup list
        self.fileExtCtl.Bind(wx.EVT_TEXT_ENTER, self.OnExtChange)
        file_box.Add(file_ext_label, 0,  wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 5)
        file_box.Add(self.fileExtCtl, 0,  wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 5)
        
        
        isNotExt = self.getProperty(FindFile.PK_NOT_EXT, datatype=FindFile.DT_BOOLEAN)
        if isNotExt is None:
            isNotExt = False
        self.isNotExtCkbox = wx.CheckBox(panel, label="Except")
        self.isNotExtCkbox.SetValue(isNotExt)   # Don't know why the constructor shows no value=
        self.OnNotExtChange(None)           # Set via change function
        self.isNotExtCkbox.Bind(wx.EVT_CHECKBOX, self.OnNotExtChange)
        file_box.Add(self.isNotExtCkbox, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 5)
        
        
        file_dir_box.Add(file_box, 0,  wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 5)

        """
        Text Pattern Selection
        """ 
        pattern_box = wx.BoxSizer(wx.HORIZONTAL)
        pattern_label = wx.StaticText(panel, -1, label="Pattern:")

        searchPattern = self.getProperty(FindFile.PK_SEARCH_PATTERN)
        if not searchPattern is None:
            self.searchPattern = searchPattern
        else:
            searchPattern = ""
        self.searchPatternCtl = wx.TextCtrl(panel, size=(300, wx.DefaultSize.height),
                                    value=searchPattern, style=wx.TE_PROCESS_ENTER)
        self.searchPatternCtl.Bind(wx.EVT_TEXT_ENTER, self.OnPatternChange)
        
        pattern_box.Add(pattern_label, 0,  wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 5)
        pattern_box.Add(self.searchPatternCtl, 0,  wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 5)
        
        isRexPattern = self.getProperty(FindFile.PK_REX_SEARCH_PATTERN, datatype=FindFile.DT_BOOLEAN)
        if isRexPattern is None:
            isRexPattern = False
        self.patternRexCkbox = wx.CheckBox(panel, label="RegEx")
        self.patternRexCkbox.SetValue(isRexPattern)
        self.OnRexChange(None)
        self.patternRexCkbox.Bind(wx.EVT_CHECKBOX, self.OnRexChange)
        pattern_box.Add(self.patternRexCkbox, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 5)
        file_dir_box.Add(pattern_box, 0,  wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 5)

        """
        Display controls
        """
        display_controlling_box = wx.BoxSizer(wx.VERTICAL)
        display_controlling_box_label = wx.StaticText(panel, -1, label="Display Control", style=wx.ALIGN_CENTER)
        display_controlling_box.Add(display_controlling_box_label, 0,  wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 5)
        display_control_box = wx.BoxSizer(wx.HORIZONTAL)
        display_controlling_box.Add(display_control_box, 0,  wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 5)
        file_dir_box.Add(display_controlling_box, 0,  wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 5)
        
        """
        Display selections
        """
        isDisplayDirList = self.getProperty(FindFile.PK_DISPLAY_DIR_LIST, datatype=FindFile.DT_BOOLEAN)
        if isDisplayDirList is None:
            isDisplayDirList = False
        self.isDisplayDirListCkbox = wx.CheckBox(panel, label="DirList")
        self.isDisplayDirListCkbox.SetValue(isDisplayDirList)   # Don't know why the constructor shows no value=
        self.OnDisplayDirListChange(None)           # Set via change function
        self.isDisplayDirListCkbox.Bind(wx.EVT_CHECKBOX, self.OnDisplayDirListChange)
        display_control_box.Add(self.isDisplayDirListCkbox)
        
        isDisplayDirs = self.getProperty(FindFile.PK_DISPLAY_DIRS, datatype=FindFile.DT_BOOLEAN)
        if isDisplayDirs is None:
            isDisplayDirs = False
        self.isDisplayDirsCkbox = wx.CheckBox(panel, label="Dirs")
        self.isDisplayDirsCkbox.SetValue(isDisplayDirs)   # Don't know why the constructor shows no value=
        self.OnDisplayDirsChange(None)           # Set via change function
        self.isDisplayDirsCkbox.Bind(wx.EVT_CHECKBOX, self.OnDisplayDirsChange)
        display_control_box.Add(self.isDisplayDirsCkbox)
        
        isDisplayFileList = self.getProperty(FindFile.PK_DISPLAY_FILE_LIST, datatype=FindFile.DT_BOOLEAN)
        if isDisplayFileList is None:
            isDisplayFileList = False
        self.isDisplayFileListCkbox = wx.CheckBox(panel, label="FileList")
        self.isDisplayFileListCkbox.SetValue(isDisplayFileList)   # Don't know why the constructor shows no value=
        self.OnDisplayFileListChange(None)           # Set via change function
        self.isDisplayFileListCkbox.Bind(wx.EVT_CHECKBOX, self.OnDisplayFileListChange)
        display_control_box.Add(self.isDisplayFileListCkbox)
        
        isDisplayFiles = self.getProperty(FindFile.PK_DISPLAY_FILES, datatype=FindFile.DT_BOOLEAN)
        if isDisplayFiles is None:
            isDisplayFiles = False
        self.isDisplayFilesCkbox = wx.CheckBox(panel, label="Files")
        self.isDisplayFilesCkbox.SetValue(isDisplayFiles)   # Don't know why the constructor shows no value=
        self.OnDisplayFilesChange(None)           # Set via change function
        self.isDisplayFilesCkbox.Bind(wx.EVT_CHECKBOX, self.OnDisplayFilesChange)
        display_control_box.Add(self.isDisplayFilesCkbox)

        """
        Search Control
        """
        search_box = wx.BoxSizer(wx.HORIZONTAL)
        self.searchBtn = wx.Button(panel, -1, "Search")
        self.searchBtn.Bind(wx.EVT_BUTTON, self.OnSearch)
        search_box.Add(self.searchBtn, 0,  wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 5)
        
        isKeepPreviousFound = self.getProperty(FindFile.PK_KEEP_PREVIOUS_FOUND, datatype=FindFile.DT_BOOLEAN)
        if isKeepPreviousFound is None:
            isKeepPreviousFound = False
        self.isKeepPreviousFoundCkbox = wx.CheckBox(panel, label="Keep Previous")
        self.isKeepPreviousFoundCkbox.SetValue(isKeepPreviousFound)   # Don't know why the constructor shows no value=
        self.OnKeepPreviousFoundChange(None)           # Set via change function
        self.isKeepPreviousFoundCkbox.Bind(wx.EVT_CHECKBOX, self.OnKeepPreviousFoundChange)
        search_box.Add(self.isKeepPreviousFoundCkbox, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 5)
        
        
        
        file_dir_box.Add(search_box, 0,  wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 5)
        

        """
        Found Items Display Area
        """
        display_region_box = wx.BoxSizer(wx.VERTICAL)
        display_region_label = wx.StaticText(panel, -1, label="Found", style=wx.ALIGN_CENTER)
        display_region_box.Add(display_region_label, 0,  wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 5)
        self.displayFoundCtrl = wx.TextCtrl(panel,
                    style=wx.TE_READONLY|wx.TE_MULTILINE|wx.TE_DONTWRAP|wx.TE_RICH,
                    size = (wx.DefaultSize.width, 500)
                    )
        
        display_region_box.Add(self.displayFoundCtrl, 0,  wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 5)
        file_dir_box.Add(display_region_box, 0,  wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 5)
        
        self.Centre()
        self.Show(True)
        atexit.register(self.propSave, propFile=self.propFile)   # Save at pgm end

    
    def search(self):
        """
        Search for Directories, Files, Text Patterns based on current selections.
        
        Start Search
            1. Record major settings
            2. Collect specified directories
            3. Collect specified files
            4. Check for valid settings, e.g. valid regular expression
            5. Traverse files for pattern, if specified
        """
        self.propertiesUpdate();      # Enforce updating and recording latest values
        self.foundTextStyle = self.displayFoundCtrl.GetDefaultStyle()

        if not self.isKeepPreviousFound:
            self.displayFoundCtrl.Clear()   # Clear previous found display
                    
        fileName = self.fileName = self.fileNameBrowse.GetValue()
        self.setProperty(FindFile.PK_FILE_NAME, self.fileName)
        dirName = self.dirName
        isInclSubDir = self.isInclSubDir
        fileExtList = self.fileExtList
        searchPattern = self.searchPattern
        isRexPattern = self.isRexPattern
        """ TBD - validate and compile regular expression """
        """
        Compile list of files, even if only one:
            1. if file name absent, blank or is not absolute, collect all directories
               else use the file's directory.
            2. if file name has no extension and extension list is not empty,
               collect files with each extension in each directory
        """
        dir_list = []       # Directories of interest
        if fileName is None or fileName == '':
            fileName = None                     # Treat all the same
            dir_list.append(dirName)
        elif os.path.isabs(fileName):
            fileName = os.path.basename(fileName)
            dir_list.append(os.path.dirname(fileName))
        
        if dirName is not None and isInclSubDir:
            for root, dirs, files in os.walk(dirName):
                for dir in dirs:
                    dir_list.append(os.path.join(root, dir))
        if self.isDisplayDirList:
            prefix = "\n     "
            self.displayFoundCtrl.AppendText("\ndirs:%s%s\n" % (prefix, prefix.join(dir_list)))


        file_list = []                      # List of full file names        
        search_file_list = []
        search_file_names = []             # base name without ext
        search_file_exts = []              # extensions including "."
        if fileName is not None:
            file_base, file_ext = os.path.splitext(fileName)
            search_file_names = [file_base]
            search_file_exts = [file_ext]
        else:
            for search_file_ext in self.fileExtList:
                if not search_file_ext.startswith("."):
                    search_file_ext = "." + search_file_ext     # add leading "."
                search_file_exts.append(search_file_ext)
                
        for dir in dir_list:
            for rt, dirs, fls in os.walk(dir):      # Just get first one
                root = rt
                files = fls
                break
                
            for file in files:
                file_name, file_ext = os.path.splitext(file)
                match_name = False
                match_ext = False
                if len(search_file_list) == 0:
                    match_name = True       # All files
                else:
                    for s_file_name in search_file_names:
                        if file_name == s_file_name:
                            match_name = True
                            break
                if len(search_file_exts) == 0:
                    match_ext = True
                else:
                    for s_file_ext in search_file_exts:
                        if s_file_ext == file_ext:
                            match_ext = True
                            break
                if match_name and match_ext:
                    file_list.append(os.path.join(root, file))
        if self.isDisplayFileList:
            prefix = "\n     "
            self.displayFoundCtrl.AppendText("\nfiles:%s%s\n" % (prefix, prefix.join(file_list)))

        if self.searchPattern is not None:

            """ Pattern length is changed for regular expression """
            pat_found_len = len(self.searchPattern)
            if self.isRexPattern:
                re_pat = re.compile(self.searchPattern)
            prev_file = None        # last displayed file
            prev_dir = None         # last displayed directory
            for file in file_list:
                dir = os.path.dirname(file)
                with open(file, mode='rt') as fin:
                    """ TBD multi line  patterns """
                    for line in fin:
                        found_i = end_i = -1        # also Used as found flag
                        if self.isRexPattern:
                            match = re.search(re_pat, line)
                            if match is not None:
                                (found_i, end_i) = match.span()
                                pat_found_len = end_i - found_i
                                
                                
                        else:
                            found_i = line.find(self.searchPattern)
                            if found_i >= 0:
                                end_i = found_i + pat_found_len
                        if found_i >= 0:
                            if self.isDisplayDirs:
                                if prev_dir is None or dir != prev_dir:
                                    self.displayFoundTextDir("\n" +dir + "\n")
                                    prev_dir = dir
                            if self.isDisplayFiles:
                                if prev_file is None or file != prev_file:
                                    prev_file = file
                                    self.displayFoundTextFile(os.path.basename(file) + "\n")
                                
                            self.displayFoundText(line[0:found_i])  # before match
                            self.displayFoundTextMatch(line[found_i:end_i])  # match
                            self.displayFoundText(line[end_i:])  # after macth
                                
 
    def displayFoundText(self, text):
        """
        Present in the current (default) style
        """
        ###saved_style = self.displayFoundCtrl.GetDefaultStyle()
        saved_style = self.displayFoundCtrl.GetDefaultStyle()
        new_style = self.displayFoundCtrl.GetDefaultStyle()
        new_style.SetTextColour(wx.BLACK)                   # Don't know why this is needed???
        self.displayFoundCtrl.SetDefaultStyle(new_style)    # Return to current style
        self.displayFoundCtrl.AppendText(text)
        self.displayFoundCtrl.SetDefaultStyle(saved_style)    # Return to current style
                                
 
    def displayFoundTextDir(self, text):
        """
        Display in directory style
        """
        saved_style = self.displayFoundCtrl.GetDefaultStyle()
        new_style = self.displayFoundCtrl.GetDefaultStyle()
        new_style.SetTextColour(wx.BLUE)
        self.displayFoundCtrl.SetDefaultStyle(new_style)
        self.displayFoundCtrl.AppendText(text)
        self.displayFoundCtrl.SetDefaultStyle(saved_style)    # Return to current style
                                 
 
    def displayFoundTextFile(self, text):
        """
        Display in directory style
        """
        saved_style = self.displayFoundCtrl.GetDefaultStyle()
        new_style = self.displayFoundCtrl.GetDefaultStyle()
        new_style.SetTextColour(wx.GREEN)
        self.displayFoundCtrl.SetDefaultStyle(new_style)
        self.displayFoundCtrl.AppendText(text)
        self.displayFoundCtrl.SetDefaultStyle(saved_style)    # Return to current style
                                 
 
    def displayFoundTextMatch(self, text):
        """
        Display in directory style
        """
        saved_style = self.displayFoundCtrl.GetDefaultStyle()
        new_style = self.displayFoundCtrl.GetDefaultStyle()
        new_style.SetTextColour(wx.RED)
        self.displayFoundCtrl.SetDefaultStyle(new_style)
        self.displayFoundCtrl.AppendText(text)
        
        self.displayFoundCtrl.SetDefaultStyle(saved_style)    # Return to current style
       
        
        
        
           
    def OnExtChange(self, e):
        new_ext = self.fileExtCtl.GetLineText(0)
        self.extName = new_ext
        self.setProperty(FindFile.PK_EXT_NAME, new_ext)
        self.fileExtList = new_ext.split(";")
    
    
    def OnNotExtChange(self, e):
        self.isNotExt = self.isNotExtCkbox.IsChecked()
        self.setProperty(FindFile.PK_NOT_EXT, self.isNotExt)
    
    
    def OnInclSubChange(self, e):
        self.isInclSubDir = self.isInclSubDirCkbox.GetValue()
        self.setProperty(FindFile.PK_INCL_SUB_DIR, self.isInclSubDir)

    def OnDirChange(self, e):
        if hasattr(self, "fileNameBrowse"):
            self.dirName = self.dirNameBrowse.GetValue()
            self.dirHistoryList = self.dirNameBrowse.GetHistory()
            self.setProperty(FindFile.PK_DIR_HISTORY, ";".join(self.dirHistoryList))
            self.dirNameBrowse.startDirectory = self.dirName
            self.fileNameBrowse.startDirectory = self.dirName
            self.setProperty(FindFile.PK_DIR_START, self.dirName)
            self.fileNameBrowse.SetValue("", callBack=0)
        ### print("OnDirChange: self.dirName = %s %s" % (self.dirName, self.dirNameBrowse.GetValue()))

    def OnPatternChange(self, e):
        self.searchPattern = self.searchPatternCtl.GetValue()
        self.setProperty(FindFile.PK_SEARCH_PATTERN, self.searchPattern)

    def OnRexChange(self, e):
        self.isRexPattern = self.patternRexCkbox.IsChecked()
        self.setProperty(FindFile.PK_REX_SEARCH_PATTERN, self.isRexPattern)
        

    def OnFileChange(self, e):
        file_path = self.fileNameBrowse.GetValue()
        if not os.path.isabs(file_path):
            ###print("file_path %s is not absolute - disregard" % file_path)
            return
        
        self.dirName = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        self.fileNameBrowse.SetValue(file_name, callBack=0)
        self.dirNameBrowse.startDirectory = self.dirName
        self.setProperty(FindFile.PK_DIR_START, self.dirName)
        self.dirNameBrowse.SetValue(self.dirName, callBack=0)
        self.fileNameBrowse.startDirectory = self.dirName
        print("OnFileChange: self.dirName = %s %s" % (self.dirName, self.dirNameBrowse.GetValue()))
    
    
    def OnDisplayDirListChange(self, e):
        self.isDisplayDirList = self.isDisplayDirListCkbox.IsChecked()
        self.setProperty(FindFile.PK_DISPLAY_DIR_LIST, self.isDisplayDirList)
    
    
    def OnDisplayDirsChange(self, e):
        self.isDisplayDirs = self.isDisplayDirsCkbox.IsChecked()
        self.setProperty(FindFile.PK_DISPLAY_DIRS, self.isDisplayDirs)
    
    
    def OnDisplayFileListChange(self, e):
        self.isDisplayFileList = self.isDisplayFileListCkbox.IsChecked()
        self.setProperty(FindFile.PK_DISPLAY_FILE_LIST, self.isDisplayFileList)
   
    
    def OnDisplayFilesChange(self, e):
        self.isDisplayFiles = self.isDisplayFilesCkbox.IsChecked()
        self.setProperty(FindFile.PK_DISPLAY_FILES, self.isDisplayFiles)

   
    
    def OnKeepPreviousFoundChange(self, e):
        self.isKeepPreviousFound = self.isKeepPreviousFoundCkbox.IsChecked()
        self.setProperty(FindFile.PK_KEEP_PREVIOUS_FOUND, self.isKeepPreviousFound)
        
    
    def OnSearch(self, e):
        self.search()
        
    
    def getProperty(self, key, datatype=DT_STRING):
        val = self.properties.getProperty(key)
        if val is None:
            return val
        if val == '' and datatype != FindFile.DT_STRING:
            return None     # If not string treat as not present
        
        if datatype == FindFile.DT_BOOLEAN:
            if val.lower() == 'false':
                val = False
            else:
                val = True
        elif datatype == FindFile.DT_INT:
            val = int(val)
        elif datatype == FindFile.DT_FLOAT:
            val = float(val)
            
        return val

    
    def setProperty(self, key, value):
        """
        Determine type and convert appropriately
        """
        if type(value) is bool:
            if value:
                value = 'True'
            else:
                value = 'False'
        elif type(value) is int:
            value = str(value)
        elif type(value) is float:
            value = str(value)
            
        self.properties.setProperty(key, value)


    def propertiesUpdate(self, end=False):
        if not end:
            self.OnDirChange(None)
            self.OnFileChange(None)
            self.OnInclSubChange(None)
            self.OnExtChange(None)
            self.OnPatternChange(None)
            self.OnRexChange(None)
            self.OnDisplayDirListChange(None)
            self.OnDisplayDirsChange(None)
            self.OnDisplayFileListChange(None)
            self.OnDisplayFilesChange(None)
            self.OnNotExtChange(None)
            self.OnKeepPreviousFoundChange(None)

            
                        
    def OnQuit(self, e):
        self.Close()
        
def main():
    import os
    import sys
    ex = wx.App()
    progname = os.path.basename(sys.argv[0])
    base = progname.split(".")[0]
    prop_file = base + ".properties"
    print("properties file: %s" % os.path.abspath(prop_file))
    FindFile(None, propFile=prop_file)
    ex.MainLoop()    


if __name__ == '__main__':
    main()