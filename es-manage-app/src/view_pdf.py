# import wx
# import wx.lib.sized_controls as sc

# from wx.lib.pdfviewer import pdfViewer, pdfButtonPanel

# class PDFViewer(sc.SizedFrame):
#     def __init__(self, parent, **kwds):
#         super(PDFViewer, self).__init__(parent, **kwds)

#         paneCont = self.GetContentsPane()
#         self.buttonpanel = pdfButtonPanel(paneCont, wx.NewId(),
#                                 wx.DefaultPosition, wx.DefaultSize, 0)
#         self.buttonpanel.SetSizerProps(expand=True)
#         self.viewer = pdfViewer(paneCont, wx.NewId(), wx.DefaultPosition,
#                                 wx.DefaultSize,
#                                 wx.HSCROLL|wx.VSCROLL|wx.SUNKEN_BORDER)
#         self.viewer.UsePrintDirect = False
#         self.viewer.SetSizerProps(expand=True, proportion=1)

#         # introduce buttonpanel and viewer to each other
#         self.buttonpanel.viewer = self.viewer
#         self.viewer.buttonpanel = self.buttonpanel


# if __name__ == '__main__':
#     import wx.lib.mixins.inspection as WIT
#     app = WIT.InspectableApp(redirect=False)


#     pdfV = PDFViewer(None, size=(850, 800))
#     # pdfV.viewer.UsePrintDirect = False
#     pdfV.viewer.LoadFile(r"E:\Emul\Full_Roms_cache\1\18455_manuals_jp.pdf")
#     pdfV.viewer.SetZoom(-1)
#     pdfV.Show()

#     app.MainLoop()


import wx
import wx.lib.sized_controls as sc

from wx.lib.pdfviewer import pdfViewer, pdfButtonPanel

class PDFPanel(sc.SizedPanel):
    def __init__(self, parent):
        super(PDFPanel, self).__init__(parent)
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



class PDFViewer(wx.Frame):
    def __init__(self, parent, **kwds):
        super(PDFViewer, self).__init__(parent, **kwds)
        

        paneCont = sc.SizedPanel(self)
        self.buttonpanel = pdfButtonPanel(paneCont, wx.NewId(),
                                wx.DefaultPosition, wx.DefaultSize, 0)
        self.buttonpanel.SetSizerProps(expand=True)
        self.viewer = pdfViewer(paneCont, wx.NewId(), wx.DefaultPosition,
                                wx.DefaultSize,
                                wx.HSCROLL|wx.VSCROLL|wx.SUNKEN_BORDER)
        self.viewer.UsePrintDirect = False
        self.viewer.SetSizerProps(expand=True, proportion=1)

        # introduce buttonpanel and viewer to each other
        self.buttonpanel.viewer = self.viewer
        self.viewer.buttonpanel = self.buttonpanel


if __name__ == '__main__':
    import wx.lib.mixins.inspection as WIT
    app = WIT.InspectableApp(redirect=False)


    pdfV = PDFViewer(None, size=(850, 800))
    # pdfV.viewer.UsePrintDirect = False
    pdfV.viewer.LoadFile(r"E:\Emul\Full_Roms_cache\1\18455_manuals_jp.pdf")
    pdfV.viewer.SetZoom(-1)
    pdfV.Show()

    app.MainLoop()
