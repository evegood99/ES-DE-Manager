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
import wx.lib.sized_controls as sc
from wx.lib.pdfviewer import pdfViewer, pdfButtonPanel
# import selenium.webdriver as webdriver
# import urllib2, StringIO

# Fix for PyCharm hints warnings when using static methods

# Platforms
WINDOWS = (platform.system() == "Windows")
LINUX = (platform.system() == "Linux")
MAC = (platform.system() == "Darwin")

# Configuration
WIDTH = 2160
HEIGHT = 1200

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


class AddSystem(wx.Frame):
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
        self.getData_btn = wx.Button(self, label="Add System", size=(110, 55))

        # self.getData_btn = wx.BitmapButton(self, size=btn_size, bitmap=bitmap)
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
        self.leftPanel = GridPanelGames(splitter, None, 'aaa', 10, None)

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
        splitter.SetMinimumPaneSize(1010)
        # splitter.SetMin
        mainSizer.Add(splitter, 1, wx.EXPAND)

        self.SetSizer(mainSizer)

        self.nullPanel1 = NullDataPanel(self)
        self.nullPanel2 = PDFViewPanel(self)
        self.nullPanel2.viewer.LoadFile(r"E:\Emul\Full_Roms_cache\1\18455_manuals_jp.pdf")
        self.nullPanel2.viewer.SetZoom(-1)
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
        self.list_ctrl.InsertColumn(0, 'NAME', width=140, format=wx.LIST_FORMAT_CENTER)
        self.list_ctrl.InsertColumn(1, 'SYSTEM', width=80, format=wx.LIST_FORMAT_CENTER)
        self.list_ctrl.InsertColumn(2, 'PLATFORM', width=100, format=wx.LIST_FORMAT_CENTER)
        self.list_ctrl.InsertColumn(4, '# GAME', width=80, format=wx.LIST_FORMAT_CENTER)
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
        splitter.SetMinimumPaneSize(420)
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


class PDFViewPanel(sc.SizedPanel):
        def __init__(self, parent):
            super(PDFViewPanel, self).__init__(parent)
            self.buttonpanel = pdfButtonPanel(self, wx.NewId(),
                                    wx.DefaultPosition, wx.DefaultSize, 0)
            self.buttonpanel.SetSizerProps(expand=True)
            self.viewer = pdfViewer(self, wx.NewId(), wx.DefaultPosition,
                                    wx.DefaultSize,
                                    wx.HSCROLL|wx.VSCROLL|wx.SUNKEN_BORDER)
            self.viewer.UsePrintDirect = False
            self.viewer.SetSizerProps(expand=True, proportion=1)

            # introduce buttonpanel and viewer to each other
            self.buttonpanel.viewer = self.viewer
            self.viewer.buttonpanel = self.buttonpanel    


class NullDataPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        wx.StaticText(self, -1, "Please Click Data Item", (40, 40))


class GridPanelGames(wx.Panel):
    def __init__(self, parent, tableName, titleQuery, newsNum, list_ctrl):
        wx.Panel.__init__(self, parent)
        self.myGrid = gridlib.Grid(self)
        #         attr = gridlib.GridCellAttr()
        #         attr.SetReadOnly(True)
        self.list_ctrl = list_ctrl
        self.beforSortTup = None
        self.reData = None
        self.applyQuery = ""

        optionBox = wx.StaticBox(self, label='Query Option')
        optionBox_sizer = wx.StaticBoxSizer(optionBox, orient=wx.VERTICAL)
        optionBox_Gridsizer = wx.GridBagSizer(1, 2)
        self.queryStr = wx.TextCtrl(self, value="", size=(450, -1))
        optionBox_Gridsizer.Add(wx.StaticText(self, label="Query : "), pos=(0, 0))
        optionBox_Gridsizer.Add(self.queryStr, pos=(0, 1))
        self.apply_button = wx.Button(self, label="Apply", size=(60, 23))
        optionBox_Gridsizer.Add(self.apply_button, pos=(0, 3), flag=wx.TOP | wx.RIGHT, border=1)
        # self.apply_button.Bind(wx.EVT_BUTTON, self.queryButtonClick)

        self.filtrting_button = wx.Button(self, label="Filtering", size=(90, 23))
        optionBox_Gridsizer.Add(self.filtrting_button, pos=(0, 4), flag=wx.TOP | wx.RIGHT, border=1)
        # self.filtrting_button.Bind(wx.EVT_BUTTON, self.filtrting_button_click)
        self.dbox = None

        self.queryResultStr = wx.StaticText(self, label="", style=wx.TE_RICH)
        optionBox_Gridsizer.Add(self.queryResultStr, pos=(1, 0))

        self.save_button = wx.Button(self, label="Save", size=(60, 23))
        #         self.save_button.Disable()
        optionBox_Gridsizer.Add(self.save_button, pos=(1, 3), flag=wx.TOP | wx.RIGHT, border=1)
        # self.save_button.Bind(wx.EVT_BUTTON, self.querySaveClick)

        optionBox_sizer.Add(optionBox_Gridsizer, flag=wx.EXPAND | wx.HORIZONTAL | wx.TOP | wx.LEFT | wx.RIGHT, border=2)

        global OPTION_LINENUM
        if newsNum > OPTION_LINENUM:
            newsNum = OPTION_LINENUM
        self.newsNum = newsNum
        self.titleQuery = titleQuery
        self.photo = None
        self.tableName = tableName
        self.myGrid.CreateGrid(newsNum, 3)
        self.myGrid.SetColLabelValue(0, "FILE")
        self.myGrid.SetColLabelValue(1, "NAME (EN)")
        self.myGrid.SetColLabelValue(2, "NAME (KR)")
        self.myGrid.SetColSize(1, 500)
        d_size = 300
        self.myGrid.SetColSize(0, d_size)
        self.myGrid.SetColSize(1, d_size)
        self.myGrid.SetColSize(2, d_size)

        self.myGrid.SetCellValue(0, 0, "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        self.myGrid.SetCellValue(1, 0, str(1212121212121231231232))

        self.myGrid.Bind(gridlib.EVT_GRID_LABEL_LEFT_CLICK, self.showPopupMenu)
        self.myGrid.Bind(gridlib.EVT_GRID_CELL_LEFT_DCLICK, self.cellDoubleClick)

        # global NMDB
        # dataList = NMDB.getAllRowData(tableName, rowNum=OPTION_LINENUM)
        # rowNum = 0
        # for line in dataList[:self.newsNum]:
        #     self.myGrid.SetCellValue(rowNum, 0, line[0])
        #     self.myGrid.SetCellValue(rowNum, 1, line[1][:500])
        #     self.myGrid.SetCellValue(rowNum, 2, str(line[2]))
        #     self.myGrid.SetCellValue(rowNum, 3, line[3])
        #     self.myGrid.SetCellValue(rowNum, 4, str(line[4]))
        #     self.myGrid.SetCellValue(rowNum, 5, str(line[5]))
        #     self.myGrid.SetCellValue(rowNum, 6, line[6])
        #     self.myGrid.SetCellValue(rowNum, 7, line[7])
        #     rowNum += 1

        self.myGrid.EnableEditing(False)
        self.myGrid.GetGridWindow().Bind(wx.EVT_MOTION, self.onMouseOver)
        #         myGrid.ChangedValue = False

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(optionBox_sizer)
        sizer.Add(self.myGrid, 1, flag=wx.EXPAND | wx.HORIZONTAL | wx.TOP | wx.LEFT | wx.RIGHT, border=2)

        self.SetSizer(sizer)
        self.Centre()
        self.Show(True)


    def cellDoubleClick(self, event):
        index = event.GetRow()
        print(index)
        url = self.myGrid.GetCellValue(index, 6)
        webbrowser.open(url)

    def onMouseOver(self, event):
        try:
            x, y = self.myGrid.CalcUnscrolledPosition(event.GetX(), event.GetY())
            coords = self.myGrid.XYToCell(x, y)
            col = coords[1]
            row = coords[0]
            msg = self.myGrid.GetCellValue(row, col)
            event.GetEventObject().SetToolTip(msg)
        except:
            pass

    def showPopupMenu(self, event):
        menu = wx.Menu()
        # Show how to put an icon in the menu
        self.sortCol = event.GetCol()
        item1 = wx.MenuItem(menu, -1, "Sorting(Ascending)")
        menu.Append(item1)
        menu.Bind(wx.EVT_MENU, self.onPopupItemSelectedAscending, item1)
        item2 = wx.MenuItem(menu, -1, "Sorting(Descending)")
        menu.Append(item2)
        menu.Bind(wx.EVT_MENU, self.onPopupItemSelectedDescending, item2)

        #         menu.Append(self.popupID2, "Two")
        #         menu.Append(self.popupID3, "Three")

        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(menu)
        menu.Destroy()

    def onPopupSorting(self, isReverseOrder):
        global OPTION_LINENUM
        self.myGrid.EnableEditing(True)
        selectedColNum = self.sortCol
        if isReverseOrder:
            sortOrder = "DESC"
        else:
            sortOrder = "ASC"
        global NMDB
        selectedColDict = {-1: "title", 0: "title", 1: "content", 2: "writer", 3: "date", 4: "category", 5: "section",
                           6: "url", 7: "source"}
        try:
            selectCol = selectedColDict[selectedColNum]
        except:
            selectCol = "title"
        tmpDataList = NMDB.getAllRowDataOrdered(self.tableName, selectCol, sortOrder, beforeSortTup=self.beforSortTup)
        self.beforSortTup = (selectCol, sortOrder)

        return tmpDataList

    def setCell(self, tmpDataList):
        rowNum = 0
        global OPTION_LINENUM
        if self.newsNum < OPTION_LINENUM:
            viewLine = self.newsNum
        else:
            viewLine = OPTION_LINENUM
        for line in tmpDataList[:viewLine]:
            self.myGrid.SetCellValue(rowNum, 0, line[0])
            self.myGrid.SetCellValue(rowNum, 1, line[1][:500])
            self.myGrid.SetCellValue(rowNum, 2, str(line[2]))
            self.myGrid.SetCellValue(rowNum, 3, line[3])
            self.myGrid.SetCellValue(rowNum, 4, str(line[4]))
            self.myGrid.SetCellValue(rowNum, 5, str(line[5]))
            self.myGrid.SetCellValue(rowNum, 6, line[6])
            self.myGrid.SetCellValue(rowNum, 7, line[7])
            rowNum += 1

        self.myGrid.EnableEditing(False)

    def onPopupItemSelectedAscending(self, event):
        tmpDataList = self.onPopupSorting(False)
        self.setCell(tmpDataList)

    #         print selectedColNum

    def onPopupItemSelectedDescending(self, event):
        tmpDataList = self.onPopupSorting(True)
        self.setCell(tmpDataList)





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
        m_d_size = (340, 190)
        self.SetSize(m_d_size)

    def InitUI(self):
        global OPTION_LINENUM
        pnl = wx.Panel(self)
        wx.StaticBox(pnl, label='Options', pos=(5, 5),
                     size=(310, 70))
        wx.StaticText(pnl, label="Maximum rows to display : ", pos=(15, 30))
        self.spinCtrl = wx.SpinCtrl(pnl, value=str(OPTION_LINENUM), pos=(195, 29),
                                    size=(90, -1), min=1, max=999999999)

        btn_ok = wx.Button(pnl, label='OK', pos=(100, 90),
                           size=(60, -1))
        btn_ok.Bind(wx.EVT_BUTTON, self.OnOk)
        btn_close = wx.Button(pnl, label='Cancel', pos=(180, 90),
                              size=(60, -1))
        btn_close.Bind(wx.EVT_BUTTON, self.OnClose)

    def OnOk(self, e):
        global OPTION_LINENUM
        OPTION_LINENUM = int(self.spinCtrl.GetValue())
        self.Destroy()

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
