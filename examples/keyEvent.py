#!/usr/bin/python
# -*- coding: utf-8 -*-

import wx

class Example(wx.Frame):
           
    def __init__(self, *args, **kw):
        super(Example, self).__init__(*args, **kw) 
        
        self.InitUI()
                
    def InitUI(self):

        pnl = wx.Panel(self)
        pnl.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        pnl.SetFocus()

        self.SetSize((250, 180))
        self.SetTitle('Key event')
        self.Centre()
        self.Show(True)  

    def OnKeyDown(self, e):
        
        key = e.GetKeyCode()
        
        if key == wx.WXK_ESCAPE:
            
            ret  = wx.MessageBox('Are you sure to quit?', 'Question', 
                wx.YES_NO | wx.NO_DEFAULT, self)
                
            if ret == wx.YES:
                self.Close()               
        
def main():
    
    ex = wx.App()
    Example(None)
    ex.MainLoop()    


if __name__ == '__main__':
    main() 