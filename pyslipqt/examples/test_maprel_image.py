#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Test PySlipQt map-relative images.

Usage: test_maprel_image.py [-h] [-t (OSM|GMT)]
"""


import wx
import pyslipqt


######
# Various constants
######

DefaultAppSize = (600, 400)

MinTileLevel = 0
InitViewLevel = 2
InitViewPosition = (158.0, -20.0)

arrow = 'graphics/arrow_right.png'

ImageMapData = [(158, -17, arrow, {'offset_x': 0, 'offset_y': 0}),
                (158, -18, arrow, {'offset_x': 0, 'offset_y': 0}),
                (158, -19, arrow, {'offset_x': 0, 'offset_y': 0}),
                (158, -20, arrow, {'offset_x': 0, 'offset_y': 0}),
                (158, -21, arrow, {'offset_x': 0, 'offset_y': 0}),
                (158, -22, arrow, {'offset_x': 0, 'offset_y': 0}),
                (158, -23, arrow, {'offset_x': 0, 'offset_y': 0})
               ]

PolygonMapData = [(((158,-17),(158,-23)),
                      {'width': 1, 'colour': 'black', 'filled': False})
                 ]

################################################################################
# The main application frame
################################################################################

class TestFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, size=DefaultAppSize,
                          title=('PySlipQt %s - map-relative image test'
                                 % pyslipqt.__version__))
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

        # add test layers
        self.poly_layer = self.pyslipqt.AddPolygonLayer(PolygonMapData)
        self.image_layer = self.pyslipqt.AddImageLayer(ImageMapData,
                                                     map_rel=True,
                                                     placement='ce',
                                                     name='<image_map_layer>')

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

