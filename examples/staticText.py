#!/usr/bin/python
# -*- coding: utf-8 -*-

import wx


class Example(wx.Frame):
           
    def __init__(self, *args, **kw):
        super(Example, self).__init__(*args, **kw) 
        
        self.InitUI()
        
    def InitUI(self):   

        txt1 = '''I'm giving up the ghost of love
in the shadows cast on devotion
She is the one that I adore
creed of my silent suffocation
Break this bittersweet spell on me
lost in the arms of destiny'''

        txt2 = '''There is something in the way
You're always somewhere else
Feelings have deserted me
To a point of no return
I don't believe in God
But I pray for you'''

        pnl = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        st1 = wx.StaticText(pnl, label=txt1, style=wx.ALIGN_CENTRE)
        st2 = wx.StaticText(pnl, label=txt2, style=wx.ALIGN_CENTRE)
        
        vbox.Add(st1, flag=wx.ALL, border=5)
        vbox.Add(st2, flag=wx.ALL, border=5)
        pnl.SetSizer(vbox)
        
        self.SetSize((250, 260))
        self.SetTitle('Bittersweet')
        self.Centre()
        self.Show(True)          
                        
def main():
    
    ex = wx.App()
    Example(None)
    ex.MainLoop()    

if __name__ == '__main__':
    main()  