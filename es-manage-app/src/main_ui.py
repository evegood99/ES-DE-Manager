# -*- coding: utf-8 -*-
'''
Created on 2019. 3. 

@author: youngjin
'''


import wx
import wx.adv
import wx.lib.agw.aui as aui
import platform
import sys
import tempfile, shutil, os
import time
import pathlib
import imageIco
# from instaItemObj import InstaPostsItem, InstaPost, InstaUser
import threading
import webbrowser
import wx.grid as gridlib
# import cPickle 
import copy
import chardet

# import selenium.webdriver as webdriver
# import urllib2, StringIO

# Fix for PyCharm hints warnings when using static methods

# Platforms
WINDOWS = (platform.system() == "Windows")
LINUX = (platform.system() == "Linux")
MAC = (platform.system() == "Darwin")

# Configuration
WIDTH = 2180
HEIGHT = 1080

OPTION_LINENUM = 2000
LIST_CTRL = None

# options = webdriver.ChromeOptions()    
# options.binary_location = r'..\bin\chrome.exe'
# options.add_argument('headless')    
# options.add_argument('disable-gpu')    
# filepath = os.path.realpath("chromedriver.exe")
# args = ["hide_console", ]
# driver = webdriver.Chrome(chrome_options=options, service_args=args)

# 암시적으로 최대 5초간 기다린다
# driver.implicitly_wait(5) 
# driver.get('https://www.instagram.com/explore/tags/a')  

TEMP_DIR = tempfile.gettempdir()
TEMP_PATH = os.path.join(TEMP_DIR, 'cyram_tempFile.db')
print(TEMP_PATH)
DATA_LIST = []
NMDB = None




def getPresentTime():
    timeForm = "%Y-%m-%d %H:%M:%S"
    localTime = time.localtime()
    return time.strftime(timeForm, localTime)


class DataFilteringBox(wx.Frame):
    def __init__(self, parent, id, title, targerField, tableName):
        ID_NEW = 1
        ID_ADDFILE = 2
        ID_DELETE = 3
        ID_CLEAR = 4
        wx.Frame.__init__(self, parent, id, title, size=(970, 600))
        titleIcon = imageIco.cloudIco.GetIcon()
        wx.Frame.SetIcon(self, titleIcon)

        self.targerField = targerField
        self.tableName = tableName
        self.newDataList = []
        self.checkButthon = None

        panel = wx.Panel(self, -1)
        totalGridsizer = wx.GridBagSizer(2, 2)
        subGridsizer_left = wx.GridBagSizer(2, 1)
        subGridsizer_right = wx.GridBagSizer(1, 1)

        pageNameBox = wx.StaticBox(panel, label='Input Filtering Words')
        pageNameBox_sizer = wx.StaticBoxSizer(pageNameBox, orient=wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.listbox = wx.ListBox(panel, -1, size=(350, 300), style=wx.LB_EXTENDED | wx.LB_SORT)
        hbox.Add(self.listbox, 1, wx.EXPAND | wx.ALL, 20)
        btnPanel = wx.Panel(panel, -1)
        vbox = wx.BoxSizer(wx.VERTICAL)
        new = wx.Button(btnPanel, ID_NEW, 'Add direct', size=(120, 30), style=wx.BU_LEFT)
        fileAdd = wx.Button(btnPanel, ID_ADDFILE, 'Add from File', size=(120, 30), style=wx.BU_LEFT)
        dlt = wx.Button(btnPanel, ID_DELETE, 'Delete', size=(120, 30), style=wx.BU_LEFT)
        clr = wx.Button(btnPanel, ID_CLEAR, 'Delete All', size=(120, 30), style=wx.BU_LEFT)
        self.Bind(wx.EVT_BUTTON, self.NewItem, id=ID_NEW)
        self.Bind(wx.EVT_BUTTON, self.addFile, id=ID_ADDFILE)
        self.Bind(wx.EVT_BUTTON, self.OnDelete, id=ID_DELETE)
        self.Bind(wx.EVT_BUTTON, self.OnClear, id=ID_CLEAR)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        vbox.Add((-1, 20))
        vbox.Add(new)
        vbox.Add(fileAdd, 0, wx.TOP, 5)
        vbox.Add(dlt, 0, wx.TOP, 5)
        vbox.Add(clr, 0, wx.TOP, 5)
        btnPanel.SetSizer(vbox)
        hbox.Add(btnPanel, 0.6, wx.EXPAND | wx.RIGHT, 20)
        pageNameBox_sizer.Add(hbox, flag=wx.EXPAND | wx.VERTICAL | wx.HORIZONTAL)

        dataDayLimitBox = wx.StaticBox(panel, label='Filtering Pattern')
        dataDayLimitBox_sizer = wx.StaticBoxSizer(dataDayLimitBox, orient=wx.VERTICAL)

        rangeDateDayLimitBox_Gridsizer = wx.GridBagSizer(5, 3)

        self.rb1 = wx.RadioButton(panel, label='Exclude', pos=(0, 0), style=wx.RB_GROUP)
        self.rb2 = wx.RadioButton(panel, label='Include', pos=(1, 0))

        rangeDateDayLimitBox_Gridsizer.Add(self.rb1, pos=(0, 0), span=(1, 10),
                                           flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, border=10)
        rangeDateDayLimitBox_Gridsizer.Add(self.rb2, pos=(1, 0), span=(1, 10),
                                           flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, border=10)
        dataDayLimitBox_sizer.Add(rangeDateDayLimitBox_Gridsizer,
                                  flag=wx.EXPAND | wx.HORIZONTAL | wx.TOP | wx.LEFT | wx.RIGHT, border=1)

        targetBox = wx.StaticBox(panel, label='Target field')
        targetBox_sizer = wx.StaticBoxSizer(targetBox, orient=wx.VERTICAL)
        self.tartgetCombo = wx.ComboBox(panel, value=targerField[0], choices=targerField, size=(240, -1),
                                        style=wx.CB_READONLY)
        targetBox_sizer.Add(self.tartgetCombo)

        confirmBox = wx.GridBagSizer(1, 10)
        ok_button = wx.Button(panel, label="Apply")
        confirmBox.Add(ok_button, pos=(0, 1), flag=wx.TOP | wx.RIGHT, border=1)
        ok_button.Bind(wx.EVT_BUTTON, self.set_ok)

        cancel_button2 = wx.Button(panel, label="Cancel")
        confirmBox.Add(cancel_button2, pos=(0, 2), flag=wx.TOP | wx.RIGHT, border=1)
        cancel_button2.Bind(wx.EVT_BUTTON, self.set_cancel)
        subGridsizer_left.Add(pageNameBox_sizer, pos=(0, 0), span=(1, 4), flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT,
                              border=10)
        subGridsizer_right.Add(dataDayLimitBox_sizer, pos=(0, 0), span=(1, 4),
                               flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, border=10)
        subGridsizer_right.Add(targetBox_sizer, pos=(1, 0), span=(1, 4), flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT,
                               border=10)
        totalGridsizer.Add(subGridsizer_left, pos=(0, 0))
        totalGridsizer.Add(subGridsizer_right, pos=(0, 1), span=(1, 4), flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT,
                           border=10)
        totalGridsizer.Add(confirmBox, pos=(2, 1), span=(1, 4), flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, border=10)
        panel.SetSizer(totalGridsizer)
        self.Centre()
        self.Show(True)

    def NewItem(self, event):
        text = wx.GetTextFromUser('Please input a word', 'Insert dialog')
        if text == '' or text == ' ' or text == '\t':
            return 0

        else:
            self.listbox.Append(text)
        #             OPT.multiPayProcess_timeSetting.append(text)

    def addFile(self, event):
        with wx.FileDialog(self, "Open Filtering words file", wildcard="csv files (*.csv)|*.csv",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind

            # Proceed loading the file chosen by the user
            pathname = fileDialog.GetPath()

            if pathlib.Path(pathname).is_file():
                import csv
                #                 dlg = wx.ProgressDialog("Load Data",
                #                                        "Reading Data...",
                #                                        maximum = 100,
                #                                        parent=self,
                #                                        style = wx.PD_APP_MODAL
                #
                #
                #                                         | wx.PD_ELAPSED_TIME
                #                                         | wx.PD_AUTO_HIDE
                #                                         #| wx.PD_ESTIMATED_TIME
                #         #                                 | wx.PD_REMAINING_TIME
                #                                         )
                #                 dlg.Pulse("Reading Data...")

                fp = open(pathname, 'rb')
                testRead = None
                line_n = 0
                for line in fp:
                    if testRead == None:
                        testRead = line
                    else:
                        testRead += line
                    line_n += 1
                    if line_n >= 10:
                        break
                chatDetResult = chardet.detect(testRead)
                fp.close()
                encodingResult = chatDetResult['encoding']
                if not encodingResult in ['utf-8', 'EUC-KR', 'cp949', 'ms949']:
                    encodingResult = 'utf-8'
                try:
                    fOpen = open(pathname, encoding=encodingResult)
                except:
                    encodingResult = 'ms949'
                    fOpen = open(pathname, encoding=encodingResult)
                #                 fOpen = open(pathname, encoding="utf-8")
                try:
                    print(fOpen.readline())
                    fOpen.seek(0)
                    fp = csv.reader(fOpen)
                except:
                    encodingResult = 'ms949'
                    fOpen = open(pathname, encoding=encodingResult)
                    fp = csv.reader(fOpen)
                tmpSet = set([])
                prList = self.listbox.GetItems()
                setPrList = set(prList)
                for line in fp:
                    for word in line:
                        if word == "" or word == " " or word == "\n" or word in setPrList:
                            continue
                        word = word.strip()
                        tmpSet.add(word)

                self.listbox.AppendItems(list(tmpSet))

    #                 dlg.Update(100, "End")
    #                 dlg.Destroy()

    def OnDelete(self, event):
        sel = self.listbox.GetSelections()
        if len(sel) != 0:
            sel.sort(reverse=True)
            for index in sel:
                self.listbox.Delete(index)

    #             self.tmp_multiPayProcess_timeSetting.pop(sel)
    #             OPT.multiPayProcess_timeSetting.pop(sel)

    def OnClear(self, event):
        self.listbox.Clear()

    #         self.tmp_multiPayProcess_timeSetting = []
    #         OPT.multiPayProcess_timeSetting = []

    def set_ok(self, event):

        filteringNameSet = set(self.listbox.GetItems())

        if self.rb1.GetValue():
            self.filteringPattern = "exclude"
        else:
            self.filteringPattern = "include"

        field = self.tartgetCombo.GetValue()

        selectIndex = self.targerField.index(field)
        self.newDataList = []

        dlg = wx.ProgressDialog("Load Data",
                                "Data Filtering...",
                                maximum=100,
                                parent=self,
                                style=wx.PD_APP_MODAL

                                      | wx.PD_ELAPSED_TIME
                                      | wx.PD_AUTO_HIDE
                                # | wx.PD_ESTIMATED_TIME
                                #                                 | wx.PD_REMAINING_TIME
                                )

        lineNum = -1
        selectIndexSet = set([])
        while True:
            dataList = NMDB.cursor.fetchmany(2000)
            if not dataList:
                break
            else:
                for line in dataList:
                    lineNum += 1
                    #                     print(lineNum*100/count)
                    target = line[selectIndex]
                    if target == None:
                        continue
                    for filteringName in filteringNameSet:
                        if filteringName in target:
                            selectIndexSet.add(lineNum)
                            self.newDataList.append(line)
                            #                             print(target, filteringName)
                            break


        dlg.Update(100, 'END')
        dlg.Destroy()

        self.Close()
        self.checkButthon = "apply"

    def set_cancel(self, event):
        self.checkButthon = "cancel"
        self.Close()

    def OnClose(self, event):
        self.checkButthon = "cancel"
        self.Destroy()


class ComboBox(wx.ComboBox):

    def __init__(self, parent, dataList):
        wx.ComboBox.__init__(self, parent)
        startMonthCombo = wx.ComboBox(self, choices=dataList, style=wx.CB_READONLY)
        startMonthCombo.Bind(wx.EVT_COMBOBOX, self.OnSelect)

    def OnSelect(self, e):
        print(e.GetSelection())


class GetButtonToolbar(wx.Panel):

    def __init__(self, parent):
        # ----------------------------------------------------------------------
        """Constructor"""
        wx.Panel.__init__(self, parent)
        btn_size = (55, 55)

        top_sizer = wx.BoxSizer(wx.VERTICAL)
        tb_sizer = wx.BoxSizer(wx.HORIZONTAL)

        #         imageIco.cloudIco.GetBitmap()
        bitmap = imageIco.getApi.GetBitmap()
        W, H = bitmap.Size
        image = wx.Bitmap.ConvertToImage(bitmap)
        reSizeBitmap = (W - 460, H - 460)
        image = image.Scale(reSizeBitmap[0], reSizeBitmap[1], wx.IMAGE_QUALITY_HIGH)
        bitmap = wx.Bitmap(image)
        self.getData_btn = wx.BitmapButton(self, size=btn_size, bitmap=bitmap)
        tb_sizer.Add(self.getData_btn, 0, wx.ALL, 5)

        bitmap = imageIco.load.GetBitmap()
        W, H = bitmap.Size
        image = wx.Bitmap.ConvertToImage(bitmap)
        reSizeBitmap = (W - 460, H - 460)
        image = image.Scale(reSizeBitmap[0], reSizeBitmap[1], wx.IMAGE_QUALITY_HIGH)
        bitmap = wx.Bitmap(image)
        self.fileLoad_btn = wx.BitmapButton(self, size=btn_size, bitmap=bitmap)
        tb_sizer.Add(self.fileLoad_btn, 0, wx.ALL, 5)

        bitmap = imageIco.save.GetBitmap()
        W, H = bitmap.Size
        image = wx.Bitmap.ConvertToImage(bitmap)
        reSizeBitmap = (W - 460, H - 460)
        image = image.Scale(reSizeBitmap[0], reSizeBitmap[1], wx.IMAGE_QUALITY_HIGH)
        bitmap = wx.Bitmap(image)
        self.fileSave_btn = wx.BitmapButton(self, size=btn_size, bitmap=bitmap)
        tb_sizer.Add(self.fileSave_btn, 0, wx.ALL, 5)
        # top_sizer.Add(tb_sizer)

        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        h_sizer.Add(wx.StaticLine(self), 1, wx.EXPAND)
        # top_sizer.Add(h_sizer, 1, wx.EXPAND)

        self.SetSizer(tb_sizer)



class MainPanel2(wx.Panel):
    """Constructor"""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        splitter = wx.SplitterWindow(self)
        self.leftPanel = wx.Panel(splitter)
        twitterDataBox = wx.StaticBox(self.leftPanel)
        twitterDataBox_sizer = wx.StaticBoxSizer(twitterDataBox, orient=wx.VERTICAL)

        self.selectedItemList = []

        self.list_ctrl = wx.ListCtrl(self.leftPanel, size=(-1, 100),
                                     style=wx.LC_REPORT
                                           | wx.BORDER_SUNKEN
                                     )
        size1 = 120
        size2 = 120
        self.list_ctrl.InsertColumn(0, 'NO.', width=60, format=wx.LIST_FORMAT_CENTER)
        self.list_ctrl.InsertColumn(1, 'FILE', width=240, format=wx.LIST_FORMAT_CENTER)
        self.list_ctrl.InsertColumn(2, 'NAME (ENG)', width=300, format=wx.LIST_FORMAT_CENTER)
        self.list_ctrl.InsertColumn(4, 'NAME (KOR)', width=300, format=wx.LIST_FORMAT_CENTER)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.itemDoubleClick)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.itemSelection)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.itemDeSelection)

        twitterDataBox_sizer.Add(self.list_ctrl, 1, wx.EXPAND)
        #         self.leftPanel.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelectMustHave, self.list_ctrl)

        self.leftPanel.SetSizer(twitterDataBox_sizer)
        #####################
        self.rightPanel = wx.Panel(splitter)
        resultBox = wx.StaticBox(self.rightPanel)
        self.resultBox_sizer = wx.StaticBoxSizer(resultBox, orient=wx.VERTICAL)
        noteBookStyle = aui.AUI_NB_TOP
        self.notebook = aui.AuiNotebook(self.rightPanel, agwStyle=noteBookStyle)
        #         self.notebook = aui.AuiNotebook(self.rightPanel)

        self.resultBox_sizer.Add(self.notebook, 1, wx.EXPAND)
        self.rightPanel.SetSizer(self.resultBox_sizer)
        #######################

        splitter.SplitVertically(self.leftPanel, self.rightPanel)
        splitter.SetMinimumPaneSize(900)
        mainSizer.Add(splitter, 1, wx.EXPAND)

        self.SetSizer(mainSizer)

        self.nullPanel1 = NullDataPanel(self)
        self.nullPanel2 = NullDataPanel(self)
        self.nullPanel3 = NullDataPanel(self)
        self.nullPanel4 = NullDataPanel(self)

        self.notebook.AddPage(self.nullPanel1, "INFO", True)
        self.notebook.AddPage(self.nullPanel2, "SCREEN")
        self.notebook.AddPage(self.nullPanel3, "BOX-ART")
        self.notebook.AddPage(self.nullPanel4, "VIDEO")

        self.notebook.SetSelection(0)    
    def itemDoubleClick(self, event):

        index = event.GetIndex()
        self.notebook.DeletePage(1)
        #         (queryOperator, presentTime, gt.tweets, gt.users, gt.hashTags, dateString) = self.DataList[index]

        noteBookStyle = aui.AUI_NB_BOTTOM
        self.notebook2 = aui.AuiNotebook(self.rightPanel, agwStyle=noteBookStyle)
        global DATA_LIST
        #         print(DATA_LIST[index])
        (tableName, queryStr, newsNum, isNLP) = DATA_LIST[index]

        self.gridPanelNews = GridPanelNews(self, tableName, queryStr, newsNum, self.list_ctrl)
        self.notebook2.AddPage(self.gridPanelNews, "News", True)

        if isNLP == 0:
            pass
        else:
            self.gridPanelWord = GridPanelWord(self, tableName)
            self.notebook2.AddPage(self.gridPanelWord, "Words", True)

        self.notebook.AddPage(self.notebook2, "Data", True)
        self.notebook.SetSelection(1)
        self.notebook2.SetSelection(0)

    def itemSelection(self, event):
        selectIndex = event.GetIndex()
        self.selectedItemList.append(selectIndex)

    def itemDeSelection(self, event):
        deSelectIndex = event.GetIndex()
        self.selectedItemList.remove(deSelectIndex)

    def renameItem(self, event):
        tmpList = list(self.selectedItemList)
        if len(tmpList) == 0:
            dial = wx.MessageDialog(None, 'Select one item..', 'Item Selection', wx.OK | wx.ICON_ERROR)
            dial.ShowModal()
            return 0
        mgDlg = RenameDialog(tmpList)
        mgDlg.ShowModal()

    def deleteItem(self, event):
        tmpList = list(self.selectedItemList)
        if len(tmpList) == 0:
            dial = wx.MessageDialog(None, 'Select at least one more items.', 'Item Selection', wx.OK | wx.ICON_ERROR)
            dial.ShowModal()
            return 0
        dial = wx.MessageDialog(None, 'Really delete selected items?', 'Delete Item', wx.YES_NO | wx.ICON_WARNING)
        result = dial.ShowModal()
        if result == wx.ID_YES:
            tmpList.sort(reverse=True)
            removeTableList = []
            for index in tmpList:
                tt = DATA_LIST.pop(index)
                self.list_ctrl.DeleteItem(index)
                tableName = tt[0]
                isNLP = tt[3]
                removeTableList.append(tableName)
                if isNLP:
                    removeTableList.append(tableName + "_words")
                    removeTableList.append(tableName + "_wordsContents")
                    removeTableList.append(tableName + "_wordsTfidf")

            self.selectedItemList = []


    #         NMDB.connection.execute("VACUUM")

    def mergeItem(self, event):
        global DATA_LIST
        tmpList = list(self.selectedItemList)
        if len(tmpList) <= 1:
            dial = wx.MessageDialog(None, 'Select at least two more items.', 'Item Selection', wx.OK | wx.ICON_ERROR)
            dial.ShowModal()
            return 0
        mgDlg = MergeDialog(self.list_ctrl, tmpList)
        mgDlg.ShowModal()

class MainPanel(wx.Panel):
    """Constructor"""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        splitter = wx.SplitterWindow(self)
        self.leftPanel = wx.Panel(splitter)
        twitterDataBox = wx.StaticBox(self.leftPanel)
        twitterDataBox_sizer = wx.StaticBoxSizer(twitterDataBox, orient=wx.VERTICAL)

        self.selectedItemList = []
        self.list_ctrl = wx.ListCtrl(self.leftPanel, size=(-1, 100),
                                     style=wx.LC_REPORT
                                           | wx.BORDER_SUNKEN
                                     )
        size1 = 120
        size2 = 120
        self.list_ctrl.InsertColumn(0, 'NAME', width=size1, format=wx.LIST_FORMAT_CENTER)
        self.list_ctrl.InsertColumn(1, 'SYSTEM', width=size2, format=wx.LIST_FORMAT_CENTER)
        self.list_ctrl.InsertColumn(2, 'PLATFORM', width=size1, format=wx.LIST_FORMAT_CENTER)
        self.list_ctrl.InsertColumn(4, '# OF GAMES', width=size1, format=wx.LIST_FORMAT_CENTER)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.itemDoubleClick)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.itemSelection)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.itemDeSelection)

        toolbar = GetButtonToolbar(self.leftPanel)
        toolbar.getData_btn.Bind(wx.EVT_BUTTON, self.openDataCollectorBox)
        toolbar.fileLoad_btn.Bind(wx.EVT_BUTTON, self.openFileLoadBox)
        toolbar.fileSave_btn.Bind(wx.EVT_BUTTON, self.openFileSaveBox)

        #         toolbar.getData_btn.Bind(wx.EVT_BUTTON, self.openDataCollectorBox)
        #         toolbar.info_btn.Bind(wx.EVT_BUTTON, self.openAccessTokenBox)

        twitterDataBox_sizer.Add(toolbar, 0, wx.EXPAND)

        twitterDataBox_sizer.Add(self.list_ctrl, 1, wx.EXPAND)
        #         self.leftPanel.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelectMustHave, self.list_ctrl)

        btnSizer2 = wx.BoxSizer(wx.HORIZONTAL)

        btn0 = wx.Button(self.leftPanel, label="Add game", size=(110, 35))
        btn0.Bind(wx.EVT_BUTTON, self.renameItem)
        btn1 = wx.Button(self.leftPanel, label="Re-Scan", size=(110, 35))
        btn1.Bind(wx.EVT_BUTTON, self.mergeItem)
        btn2 = wx.Button(self.leftPanel, label="Delete", size=(110, 35))
        btn2.Bind(wx.EVT_BUTTON, self.deleteItem)
        btn4 = wx.Button(self.leftPanel, label="Make Game List", size=(160, 35))
        btn4.Bind(wx.EVT_BUTTON, self.insertItemToNetMiner)
        btnSizer2.Add(btn1)
        btnSizer2.Add(btn0)
        btnSizer2.Add(btn2)
        btnSizer2.Add((10, 10), 1, wx.EXPAND)
        btnSizer2.Add(btn4)
        twitterDataBox_sizer.Add(btnSizer2)
        # twitterDataBox_sizer.Add(btn4)

        self.leftPanel.SetSizer(twitterDataBox_sizer)
        #####################
        self.rightPanel = MainPanel2(splitter)
        # resultBox = wx.StaticBox(self.rightPanel)
        # self.resultBox_sizer = wx.StaticBoxSizer(resultBox, orient=wx.VERTICAL)
        # noteBookStyle = aui.AUI_NB_TOP
        # self.notebook = aui.AuiNotebook(self.rightPanel, agwStyle=noteBookStyle)
        # #         self.notebook = aui.AuiNotebook(self.rightPanel)

        # self.resultBox_sizer.Add(self.notebook, 1, wx.EXPAND)
        # self.rightPanel.SetSizer(self.resultBox_sizer)
        # #######################

        splitter.SplitVertically(self.leftPanel, self.rightPanel)
        splitter.SetMinimumPaneSize(520)
        mainSizer.Add(splitter, 1, wx.EXPAND)

        self.SetSizer(mainSizer)

        # self.pageCounter = 0
        # self.statusPage = set([])

        # dataCollectionPanel = DataCollectionPanel(self, self.list_ctrl)
        # #         self.gridPanel = GridPanel(self)
        # self.nullPanel = NullDataPanel(self)
        # self.notebook.AddPage(dataCollectionPanel, "Data Collector", True)
        # self.notebook.AddPage(self.nullPanel, "Data", True)
        # self.notebook.SetSelection(0)

    def openDataCollectorBox(self, event):

        self.notebook.SetSelection(0)

    def openFileSaveBox(self, event):
        with wx.FileDialog(self, "Save NME News Data file", wildcard="NME News Data files (*.nmen)|*.nmen",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind

            # save the current contents in the file
            pathname = fileDialog.GetPath()
            try:
                dlg = wx.ProgressDialog("Save Data",
                                        "Save Data...",
                                        maximum=100,
                                        parent=self,
                                        style=wx.PD_APP_MODAL

                                              | wx.PD_ELAPSED_TIME
                                              | wx.PD_AUTO_HIDE
                                        # | wx.PD_ESTIMATED_TIME
                                        #                                 | wx.PD_REMAINING_TIME
                                        )

                dlg.Pulse("Save Data... ")
                try:
                    pass
                except:
                    pass
                shutil.copy2(TEMP_PATH, pathname)
                dlg.Update(100, "End")
                dlg.Destroy()
            except IOError:
                wx.LogError("Cannot save current data in file '%s'." % pathname)

    def openFileLoadBox(self, event):
        global NMDB
        global DATA_LIST
        with wx.FileDialog(self, "Open NME News Data file", wildcard="NME News Data files (*.nmen)|*.nmen",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind

            # Proceed loading the file chosen by the user

    def itemDoubleClick(self, event):

        index = event.GetIndex()
        self.notebook.DeletePage(1)
        #         (queryOperator, presentTime, gt.tweets, gt.users, gt.hashTags, dateString) = self.DataList[index]

        noteBookStyle = aui.AUI_NB_BOTTOM
        self.notebook2 = aui.AuiNotebook(self.rightPanel, agwStyle=noteBookStyle)
        global DATA_LIST
        #         print(DATA_LIST[index])
        (tableName, queryStr, newsNum, isNLP) = DATA_LIST[index]

        self.gridPanelNews = GridPanelNews(self, tableName, queryStr, newsNum, self.list_ctrl)
        self.notebook2.AddPage(self.gridPanelNews, "News", True)

        if isNLP == 0:
            pass
        else:
            self.gridPanelWord = GridPanelWord(self, tableName)
            self.notebook2.AddPage(self.gridPanelWord, "Words", True)

        self.notebook.AddPage(self.notebook2, "Data", True)
        self.notebook.SetSelection(1)
        self.notebook2.SetSelection(0)

    def itemSelection(self, event):
        selectIndex = event.GetIndex()
        self.selectedItemList.append(selectIndex)

    def itemDeSelection(self, event):
        deSelectIndex = event.GetIndex()
        self.selectedItemList.remove(deSelectIndex)

    def renameItem(self, event):
        tmpList = list(self.selectedItemList)
        if len(tmpList) == 0:
            dial = wx.MessageDialog(None, 'Select one item..', 'Item Selection', wx.OK | wx.ICON_ERROR)
            dial.ShowModal()
            return 0
        mgDlg = RenameDialog(tmpList)
        mgDlg.ShowModal()

    def deleteItem(self, event):
        tmpList = list(self.selectedItemList)
        if len(tmpList) == 0:
            dial = wx.MessageDialog(None, 'Select at least one more items.', 'Item Selection', wx.OK | wx.ICON_ERROR)
            dial.ShowModal()
            return 0
        dial = wx.MessageDialog(None, 'Really delete selected items?', 'Delete Item', wx.YES_NO | wx.ICON_WARNING)
        result = dial.ShowModal()
        if result == wx.ID_YES:
            tmpList.sort(reverse=True)
            removeTableList = []
            for index in tmpList:
                tt = DATA_LIST.pop(index)
                self.list_ctrl.DeleteItem(index)
                tableName = tt[0]
                isNLP = tt[3]
                removeTableList.append(tableName)
                if isNLP:
                    removeTableList.append(tableName + "_words")
                    removeTableList.append(tableName + "_wordsContents")
                    removeTableList.append(tableName + "_wordsTfidf")

            self.selectedItemList = []


    #         NMDB.connection.execute("VACUUM")

    def mergeItem(self, event):
        global DATA_LIST
        tmpList = list(self.selectedItemList)
        if len(tmpList) <= 1:
            dial = wx.MessageDialog(None, 'Select at least two more items.', 'Item Selection', wx.OK | wx.ICON_ERROR)
            dial.ShowModal()
            return 0
        mgDlg = MergeDialog(self.list_ctrl, tmpList)
        mgDlg.ShowModal()

    def runNLP(self, event):
        tmpList = list(self.selectedItemList)
        if len(tmpList) == 0:
            dial = wx.MessageDialog(None, 'Select at least one more items.', 'Item Selection', wx.OK | wx.ICON_ERROR)
            dial.ShowModal()
            return 0

    def insertItemToNetMiner(self, event):
        tmpList = list(self.selectedItemList)
        if len(tmpList) == 0:
            dial = wx.MessageDialog(None, 'Select at least one more items.', 'Item Selection', wx.OK | wx.ICON_ERROR)
            dial.ShowModal()
            return 0

        for index in tmpList:
            (tableName, queryStr, newsNum, isNLP) = DATA_LIST[index]
            if isNLP == 0:
                dial = wx.MessageDialog(None, 'You must preprocess this item [' + str(
                    index + 1) + " : " + queryStr + "(" + str(newsNum) + ")]", 'Preprocessing', wx.OK | wx.ICON_ERROR)
                dial.ShowModal()
                return 0

        dlg = wx.ProgressDialog("processing",
                                "preparing...",
                                maximum=100,
                                parent=self,
                                style=wx.PD_APP_MODAL
                                      | wx.PD_ELAPSED_TIME
                                      | wx.PD_AUTO_HIDE
                                # | wx.PD_ESTIMATED_TIME
                                #                                 | wx.PD_REMAINING_TIME
                                )

        insertNM = InsertDataToNetMiner(DATA_LIST, tmpList, dlg, NMDB)
        insertNM.run()
        #         workThread = threading.Thread(target=insertNM.run)
        #         workThread.start()
        #         threads.append(workThread)
        #         for t in threads:
        #             t.join()
        dlg.Update(100, "End")
        dlg.Destroy()
        dlg.Close()

        #         insertNM = InsertNetMiner.InsertTwitterDataToNetMiner(self.DataList, tmpList, dlg)
        #         insertNM.run()
        wx.MessageBox('Process is completed', 'Info', wx.OK | wx.ICON_INFORMATION)


class RenameDialog(wx.Dialog):

    def __init__(self, selectionList):
        super(RenameDialog, self).__init__(None, title="Rename Data Item")

        self.InitUI()

    def InitUI(self):
        pnl = wx.Panel(self)


    def OnOk(self, e):
        global NMDB



    def OnClose(self, e):
        self.Destroy()


class MergeDialog(wx.Dialog):

    def __init__(self, listCtrl, selectionList):
        super(MergeDialog, self).__init__(None, title="Merge News Data")
        self.list_ctrl = listCtrl
        self.selectionList = selectionList

        self.InitUI()
        self.SetSize(50,50)

    def InitUI(self):

        pnl = wx.Panel(self)



class NullDataPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        wx.StaticText(self, -1, "Please Click Data Item", (40, 40))


class GridPanelNews(wx.Panel):
    def __init__(self, parent, tableName, titleQuery, newsNum, list_ctrl):
        wx.Panel.__init__(self, parent)
        self.myGrid = gridlib.Grid(self)
        #         attr = gridlib.GridCellAttr()
        #         attr.SetReadOnly(True)
        self.list_ctrl = list_ctrl
        self.beforSortTup = None
        self.reData = None
        self.applyQuery = ""



class GridPanelWord(wx.Panel):
    def __init__(self, parent, tableName):
        wx.Panel.__init__(self, parent)
        self.myGrid = gridlib.Grid(self)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.myGrid, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Centre()
        self.Show(True)




class DataCollectionPanel(wx.Panel):
    """Constructor"""

    #     def __init__(self, parent):
    #         wx.Panel.__init__(self, parent)
    def __init__(self, parent, list_ctrl):
        wx.Panel.__init__(self, parent)
        self.infoDict = {}
        self.frame = parent
        self.list_ctrl = list_ctrl
        self.searhcKeyUrl = {}
        #         wx.Frame.__init__(self, parent, id, title, size=(670, 400))

        totalGridsizer = wx.GridBagSizer(1, 1)

        sourceBox = wx.StaticBox(self, label='News Source')
        sourceBox_sizer = wx.StaticBoxSizer(sourceBox, orient=wx.VERTICAL)
        sourceBox_Gridsizer = wx.GridBagSizer(3, 6)
        self.source_KHAN = wx.CheckBox(self, label="경향신문")
        self.source_DONGA = wx.CheckBox(self, label="동아일보")
        self.source_CHOSUN = wx.CheckBox(self, label="조선일보")
        self.source_JOONGANG = wx.CheckBox(self, label="중앙일보")
        self.source_HANI = wx.CheckBox(self, label="한겨레")
        self.source_HANKOOK = wx.CheckBox(self, label="한국일보")
        self.source_KBS = wx.CheckBox(self, label="KBS")
        self.source_MBC = wx.CheckBox(self, label="MBC")
        self.source_SBS = wx.CheckBox(self, label="SBS")
        # justinkim 수정 중
        self.source_KHAN.SetValue(0)
        self.source_DONGA.SetValue(1)
        self.source_CHOSUN.SetValue(0)
        self.source_JOONGANG.SetValue(0)
        self.source_HANI.SetValue(0)
        self.source_HANKOOK.SetValue(0)
        self.source_KBS.SetValue(0)
        self.source_MBC.SetValue(0)
        self.source_SBS.SetValue(0)

        sourceBox_Gridsizer.Add(self.source_KHAN, pos=(0, 0), span=(0, 1), flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT,
                                border=8)
        sourceBox_Gridsizer.Add(self.source_DONGA, pos=(0, 1), span=(0, 1),
                                flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, border=8)
        sourceBox_Gridsizer.Add(self.source_CHOSUN, pos=(0, 2), span=(0, 1),
                                flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, border=8)
        sourceBox_Gridsizer.Add(self.source_JOONGANG, pos=(0, 3), span=(0, 1),
                                flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, border=8)
        sourceBox_Gridsizer.Add(self.source_HANI, pos=(0, 4), span=(0, 1), flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT,
                                border=8)
        sourceBox_Gridsizer.Add(self.source_HANKOOK, pos=(1, 0), span=(0, 1),
                                flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, border=8)
        sourceBox_Gridsizer.Add(self.source_KBS, pos=(1, 1), span=(0, 1), flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT,
                                border=8)
        sourceBox_Gridsizer.Add(self.source_MBC, pos=(1, 2), span=(0, 1), flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT,
                                border=8)
        sourceBox_Gridsizer.Add(self.source_SBS, pos=(1, 3), span=(0, 1), flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT,
                                border=8)
        sourceBox_sizer.Add(sourceBox_Gridsizer, flag=wx.EXPAND | wx.HORIZONTAL | wx.TOP | wx.LEFT | wx.RIGHT, border=8)

        confirmBox = wx.GridBagSizer(1, 1)
        totalGridsizer.Add(sourceBox_sizer, pos=(0, 0), span=(1, 2), flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT,
                           border=20)
        totalGridsizer.Add(confirmBox, pos=(3, 0), span=(1, 2), flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, border=10)
        self.SetSizer(totalGridsizer)
        self.Centre()
        self.Show(True)


    def openHelp(self, event):
        print('open help')

    def set_ok(self, event):
        #
        print('ok')

    def set_buttonProcessing(self, event):

        print('set')

class SaveBox(wx.Dialog):

    def __init__(self, queryName, queryData, list_ctrl):
        super(SaveBox, self).__init__(None, title="Save Data")
        self.queryName = queryName
        self.queryData = queryData
        self.list_ctrl = list_ctrl
        self.InitUI()
        self.SetSize(50,50)

    def InitUI(self):
        global OPTION_LINENUM
        pnl = wx.Panel(self)

    def OnOk(self, e):
        pass
    
    def OnClose(self, e):
        self.Close(True)


class OptionBox(wx.Dialog):

    def __init__(self):
        super(OptionBox, self).__init__(None, title="Preference")
        self.InitUI()
        self.SetSize(50,50)

    def InitUI(self):
        global OPTION_LINENUM
        pnl = wx.Panel(self)

    def OnOk(self, e):
        global OPTION_LINENUM

    def OnClose(self, e):
        self.Close(True)


class MainFrame(wx.Frame):

    def __init__(self):
        size = (WIDTH, HEIGHT)
        wx.Frame.__init__(self, parent=None, id=wx.ID_ANY,
                          title='News Data Collector', size=size)
        self.browser = None

        # Must ignore X11 errors like 'BadWindow' and others by
        # installing X11 error handlers. This must be done after
        # wx was intialized.

        self.setup_icon()
        self.create_menu()
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        # Set wx.WANTS_CHARS style for the keyboard to work.
        # This style also needs to be set for all parent controls.
        self.mainPanel = MainPanel(self)

        self.Show()

    def setup_icon(self):

        titleIcon = wx.Icon("Icon_ext_collect.ico")
        self.SetIcon(titleIcon)

        # titleIcon = imageIco.ndc_icon.GetIcon()
        # wx.Frame.SetIcon(self,titleIcon)
        #
        # icon_file = os.path.join(os.path.abspath(os.path.dirname(__file__)),
        #                          "resources", "wxpython.png")
        # # wx.IconFromBitmap is not available on Linux in wxPython 3.0/4.0
        # if os.path.exists(icon_file) and hasattr(wx, "IconFromBitmap"):
        #     icon = wx.IconFromBitmap(wx.Bitmap(icon_file, wx.BITMAP_TYPE_PNG))
        #     self.SetIcon(icon)

    def create_menu(self):
        filemenu = wx.Menu()
        filemenu.Append(100, "&Open Recent File")
        filemenu.Append(2, '&Preference')
        filemenu.Append(3, "&Exit")
        menubar = wx.MenuBar()
        menubar.Append(filemenu, "&File")

        helpMenu = wx.Menu()
        #         helpMenu.Append(100, '&Options')
        helpMenu.Append(200, '&About')
        #         manualMenu = wx.Menu()

        helpMenu.Append(300, '&Open Manual')

        self.Bind(wx.EVT_MENU, self.OpenOption, id=2)
        self.Bind(wx.EVT_MENU, self.OnClose, id=3)
        self.Bind(wx.EVT_MENU, self.OnAboutBox, id=200)
        self.Bind(wx.EVT_MENU, self.OpenManual, id=300)
        menubar.Append(helpMenu, '&Help')
        self.SetMenuBar(menubar)

    def OpenOption(self, event):
        optBox = OptionBox()
        optBox.ShowModal()

    def OpenManual(self, event):
        filepath = 'file://' + os.path.realpath("manual.htm")
        webbrowser.open(filepath)



    def OnAboutBox(self, e):

        description = """
        Users can get help on how to use this extension in Help > Open Manual. If you encounter any problems, please contact us netminer@cyram.com and www.netminer.com with the followings.
        
        1. Product ID(CYNMXXXX)
        2. NetMiner and Extension version
        3. Problem symptom with situation where it occurs.
        4. (If necessary) NetMiner file(.nmf)
        """

        licence = """InHouse"""

        info = wx.adv.AboutDialogInfo()

        #         info.SetIcon(wx.Icon('hunter.png', wx.BITMAP_TYPE_PNG))
        info.SetName('[Extension] News Data Collector')
        info.SetVersion('1.0.1')
        info.SetDescription(description)
        info.SetCopyright('(C) Cyram Inc. 2022-2023. All rights reserved.')
        # info.SetWebSite('http://www.cyram.com')
        #         info.SetLicence(licence)

        wx.adv.AboutBox(info)



    def OnClose(self, event):
        global NMDB
        print("[wxpython.py] OnClose called")
        self.Destroy()
        if NMDB != None:
            NMDB.connection.close()
            NMDB = None
        return


class FocusHandler(object):
    def OnGotFocus(self, browser, **_):
        # Temporary fix for focus issues on Linux (Issue #284).
        if LINUX:
            print("[wxpython.py] FocusHandler.OnGotFocus:"
                  " keyboard focus fix (Issue #284)")
            browser.SetFocus(True)


def main():
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(True)
    except:
        pass
    ex = wx.App()
    frame = MainFrame()
    frame.Show()
    ex.MainLoop()

if __name__ == '__main__':
    main()
