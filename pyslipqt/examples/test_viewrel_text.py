#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Test PySlipQt view-relative text.

Usage: test_maprel_image.py [-h] [-t (OSM|GMT)]
"""


import wx
import pyslipqt


######
# Various demo constants
######

DefaultAppSize = (600, 400)

MinTileLevel = 0
InitViewLevel = 2
InitViewPosition = (133.87, -23.7)      # Alice Springs

TextViewData = [(  0,   0, 'cc', {'placement':'cc','fontsize':50,'textcolour':'#ff000020'}),
                (  0,  10, 'cn', {'placement':'cn','fontsize':45,'textcolour':'#00ff0020'}),
                (-10,  10, 'ne', {'placement':'ne','fontsize':40,'textcolour':'#0000ff20'}),
                (-10,   0, 'ce', {'placement':'ce','fontsize':35,'textcolour':'#ff000080'}),
                (-10, -10, 'se', {'placement':'se','fontsize':30,'textcolour':'#00ff0080'}),
                (  0, -10, 'cs', {'placement':'cs','fontsize':25,'textcolour':'#0000ff80'}),
                ( 10, -10, 'sw', {'placement':'sw','fontsize':20,'textcolour':'#ff0000ff'}),
                ( 10,   0, 'cw', {'placement':'cw','fontsize':15,'textcolour':'#00ff00ff'}),
                ( 10,  10, 'nw', {'placement':'nw','fontsize':10,'textcolour':'#0000ffff'}),
               ]


################################################################################
# The main application frame
################################################################################

class TestFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, size=DefaultAppSize,
                          title='PySlipQt view-relative text test')
        self.SetMinSize(DefaultAppSize)
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.panel.SetBackgroundColour(wx.WHITE)
        self.panel.ClearBackground()

        # create the tile source object
        self.tile_src = Tiles.Tiles()

        # build the GUI
        box = wx.BoxSizer(wx.HORIZONTAL)
        self.panel.SetSizer(box)
        self.pyslipqt = pyslipqt.PySlipQt(self.panel, tile_src=self.tile_src)
        box.Add(self.pyslipqt, proportion=1, border=1, flag=wx.EXPAND)
        self.panel.SetSizerAndFit(box)
        self.panel.Layout()
        self.Centre()
        self.Show(True)

        # set initial view position
        self.pyslipqt.GotoLevelAndPosition(InitViewLevel, InitViewPosition)

        # add test test layer
        self.text_layer = self.pyslipqt.AddTextLayer(TextViewData,
                                                     map_rel=False,
                                                     name='<text_view_layer>',
                                                     offset_x=20, offset_y=20,
                                                     fontsize=20, colour='red')

################################################################################

if __name__ == '__main__':
    import sys
    import getopt
    import traceback

    # print some usage information
    def usage(msg=None):
        if msg:
            print(msg+'\n')
        print(__doc__)        # module docstring used

    # our own handler for uncaught exceptions
    def excepthook(type, value, tb):
        msg = '\n' + '=' * 80
        msg += '\nUncaught exception:\n'
        msg += ''.join(traceback.format_exception(type, value, tb))
        msg += '=' * 80 + '\n'
        print msg
        sys.exit(1)

    # plug our handler into the python system
    sys.excepthook = excepthook

    # decide which tiles to use, default is GMT
    argv = sys.argv[1:]

    try:
        (opts, args) = getopt.getopt(argv, 'ht:', ['help', 'tiles='])
    except getopt.error:
        usage()
        sys.exit(1)

    tile_source = 'GMT'
    for (opt, param) in opts:
        if opt in ['-h', '--help']:
            usage()
            sys.exit(0)
        elif opt in ('-t', '--tiles'):
            tile_source = param
    tile_source = tile_source.lower()

    # set up the appropriate tile source
    if tile_source == 'gmt':
        import pyslipqt.gmt_local_tiles as Tiles
    elif tile_source == 'osm':
        import pyslipqt.osm_tiles as Tiles
    else:
        usage('Bad tile source: %s' % tile_source)
        sys.exit(3)

    # start wxPython app
    app = wx.App()
    TestFrame().Show()
    app.MainLoop()

