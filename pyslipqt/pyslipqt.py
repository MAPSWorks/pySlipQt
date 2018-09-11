"""
A "slip map" widget for PyQt5.

Some semantics:
    map   the whole map
    view  is the view of the map through the widget
          (view may be smaller than map, or larger)
"""

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QLabel, QSizePolicy
from PyQt5.QtGui import QPainter, QColor


# if we don't have log.py, don't crash
try:
    import log
    log = log.Log('pyslipqt.log')
except AttributeError:
    # means log already set up
    pass
except ImportError as e:
    # if we don't have log.py, don't crash
    # fake all log(), log.debug(), ... calls
    def logit(*args, **kwargs):
        pass
    log = logit
    log.debug = logit
    log.info = logit
    log.warn = logit
    log.error = logit
    log.critical = logit


# version number of the widget
__version__ = '0.1.0'


class PySlipQt(QLabel):

    # widget default background colour
    Background_R = 192
    Background_G = 192
    Background_B = 192
    Background = f'rgb({Background_R}, {Background_G}, {Background_B})'

    def __init__(self, parent, tile_src, start_level, **kwargs):
        """Initialize the pySlipQt widget.

        parent       the GUI parent widget
        tile_src     a Tiles object, source of tiles
        start_level  level to initially display
        kwargs       keyword args passed through to the underlying QLabel
        """

        super().__init__(parent, **kwargs)    # inherit all parent object setup

        # set default widget background colour
        self.setStyleSheet(f'background-color: {PySlipQt.Background};')

        # remember the tile source object
        self.tile_src = tile_src

        # the tile coordinates
        self.level = start_level

        # view and map limits
        self.view_width = 0     # width/height of the view
        self.view_height = 0    # changes when the widget changes size

        self.map_width = 0      # width/height of the virtual map (not wrapped)
        self.map_height = 0     # in pixels (changes when zoom level changes)

        # set tile and levels stuff
        self.max_level = max(tile_src.levels)   # max level displayed
        self.min_level = min(tile_src.levels)   # min level displayed
        self.tile_width = tile_src.tile_size_x  # width of tile in pixels
        self.tile_height = tile_src.tile_size_y # height of tile in pixels
        self.num_tiles_x = tile_src.num_tiles_x # number of unwrapped tiles in X direction
        self.num_tiles_y = tile_src.num_tiles_y # number of unwrapped tiles in Y direction
        self.wrap_x = tile_src.wrap_x           # True if tiles wrap in X direction
        self.wrap_y = tile_src.wrap_y           # True if tiles wrap in Y direction

        # define position and tile coords of the "key" tile
        self.key_tile_left = 0      # tile coordinates of key tile
        self.key_tile_top = 0
        self.key_tile_xoffset = 0   # view coordinates of key tile wrt view
        self.key_tile_yoffset = 0

        self.left_mbutton_down = False
        self.mid_mbutton_down = False
        self.right_mbutton_down = False

        self.start_drag_x = None
        self.start_drag_y = None

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(self.tile_width, self.tile_height)

        tile_src.setCallback(self.update)

        # do a "resize" after this function, does recalc_wrap_limits()
        QTimer.singleShot(10, self.resizeEvent)

#        # set background colour of widget
#        self.setAutoFillBackground(True)
#        p = self.palette()
#        p.setColor(self.backgroundRole(), PySlipQt.Background)
#        self.setPalette(p)

#        self.setMouseTracking(True)

    def mousePressEvent(self, event):
        b = event.button()
        if b == Qt.NoButton:
            log('mousePressEvent: button=Qt.NoButton')
        elif b == Qt.LeftButton:
            log('mousePressEvent: button=Qt.LeftButton')
            self.left_mbutton_down = True
        elif b == Qt.MidButton:
            log('mousePressEvent: button=Qt.MidButton')
            self.mid_mbutton_down = True
        elif b == Qt.RightButton:
            log('mousePressEvent: button=Qt.RightButton')
            self.right_mbutton_down = True
        else:
            log('mousePressEvent: unknown button')
         
    def mouseReleaseEvent(self, event):
        b = event.button()
        if b == Qt.NoButton:
            log('mouseReleaseEvent: button=Qt.NoButton')
        elif b == Qt.LeftButton:
            log('mouseReleaseEvent: button=Qt.LeftButton')
            self.left_mbutton_down = False
            self.start_drag_x = None    # end drag, if any
            self.start_drag_y = None
        elif b == Qt.MidButton:
            log('mouseReleaseEvent: button=Qt.MidButton')
            self.mid_mbutton_down = False
        elif b == Qt.RightButton:
            log('mouseReleaseEvent: button=Qt.RightButton')
            self.right_mbutton_down = False
        else:
            log('mouseReleaseEvent: unknown button')
 
    def mouseDoubleClickEvent(self, event):
        b = event.button()
        if b == Qt.NoButton:
            log('mouseDoubleClickEvent: button=Qt.NoButton')
        elif b == Qt.LeftButton:
            log('mouseDoubleClickEvent: button=Qt.LeftButton')
        elif b == Qt.MidButton:
            log('mouseDoubleClickEvent: button=Qt.MidButton')
        elif b == Qt.RightButton:
            log('mouseDoubleClickEvent: button=Qt.RightButton')
        else:
            log('mouseDoubleClickEvent: unknown button')
 
    def mouseMoveEvent(self, event):
        """Handle a mouse move event."""

        x = event.x()
        y = event.y()

        if self.left_mbutton_down:
            if self.start_drag_x:       # if we are already dragging
                delta_x = self.start_drag_x - x
                delta_y = self.start_drag_y - y
                log(f'mouseMoveEvent: delta_x={delta_x}, delta_y={delta_y}')
                self.normalize_view_drag(delta_x, delta_y)  # normalize the "key" tile
                self.update()                               # force a repaint

            self.start_drag_x = x
            self.start_drag_y = y

    def normalize_view_drag(self, delta_x=None, delta_y=None):
        """After drag, set "key" tile correctly.

        delta_x  the X amount dragged (pixels), None if not dragged in X
        delta_y  the Y amount dragged (pixels), None if not dragged in Y
        """

        if self.wrap_x:
            # wrapping in X direction, move 'key' tile
            self.key_tile_xoffset -= delta_x
            while self.key_tile_xoffset > 0:
                # 'key' tile too far right
                self.key_tile_left -= 1
                self.key_tile_xoffset -= self.tile_width
            self.key_tile_left %= self.num_tiles_x
    
            while self.key_tile_xoffset <= -self.tile_width:
                # 'key' tile too far left
                self.key_tile_left += 1
                self.key_tile_xoffset += self.tile_width
            self.key_tile_left = (self.key_tile_left + self.num_tiles_x) % self.num_tiles_x
        else:
            log(f'DRAG: before, self.key_tile_left={self.key_tile_left}, self.key_tile_xoffset={self.key_tile_xoffset}')
            # if view > map, don't drag, ensure centred
            if self.map_width < self.view_width:
                self.key_tile_xoffset = (self.view_width - self.map_width) // 2
            else:
                # remember old 'key' tile left value
                old_left = self.key_tile_left

                # map > view, allow drag, but don't go past the edge
                self.key_tile_xoffset -= delta_x

                while self.key_tile_xoffset > 0:
                    # 'key' tile too far right
                    self.key_tile_left -= 1
                    self.key_tile_xoffset -= self.tile_width
                self.key_tile_left %= self.num_tiles_x
        
                while self.key_tile_xoffset <= -self.tile_width:
                    # 'key' tile too far left
                    self.key_tile_left += 1
                    self.key_tile_xoffset += self.tile_width
                self.key_tile_left = (self.key_tile_left + self.num_tiles_x) % self.num_tiles_x

                if delta_x < 0:
                    # was dragged to the right, don't allow left edge to show
                    log(f'DRAG RIGHT: self.key_tile_left={self.key_tile_left}, self.key_tile_xoffset={self.key_tile_xoffset}')
                    if self.key_tile_left > old_left:
                        self.key_tile_left = 0
                        self.key_tile_xoffset = 0
                    log(f'AFTER RIGHT: self.key_tile_left={self.key_tile_left}, self.key_tile_xoffset={self.key_tile_xoffset}')
                else:
                    log(f'DRAG LR: .key_tile_left={self.key_tile_left}, .key_tile_xoffset={self.key_tile_xoffset}')
                    # if dragged too far, reset key tile data
                    if self.key_tile_left > self.max_key_left:
                        self.key_tile_left = self.max_key_left
                        self.key_tile_xoffset = self.max_key_xoffset
                    elif self.key_tile_left == self.max_key_left:
                        if self.key_tile_xoffset < self.max_key_xoffset:
                            self.key_tile_xoffset = self.max_key_xoffset

        if self.wrap_y:
            # wrapping in Y direction, move 'key' tile
            self.key_tile_yoffset -= delta_y
        else:
            # if view > map, don't drag, ensure centred
            if self.map_height < self.view_height:
                self.key_tile_yoffset = (self.view_height - self.map_height) // 2
            else:
                # remember old 'key' tile left value
                old_top = self.key_tile_top

                # map > view, allow drag, but don't go past the edge
                self.key_tile_yoffset -= delta_y

                while self.key_tile_yoffset > 0:
                    # 'key' tile too far right
                    self.key_tile_top -= 1
                    self.key_tile_yoffset -= self.tile_height
                self.key_tile_top %= self.num_tiles_y
        
                while self.key_tile_yoffset <= -self.tile_height:
                    # 'key' tile too far left
                    self.key_tile_top += 1
                    self.key_tile_yoffset += self.tile_height
                self.key_tile_top = (self.key_tile_top + self.num_tiles_y) % self.num_tiles_y

                if delta_y < 0:
                    # was dragged to the top, don't allow bottom edge to show
                    if self.key_tile_top > old_top:
                        self.key_tile_top = 0
                        self.key_tile_yoffset = 0
                else:
                    log(f'DRAG UD: .key_tile_top={self.key_tile_top}, .key_tile_yoffset={self.key_tile_yoffset}')
                    # if dragged too far, reset key tile data
                    if self.key_tile_top > self.max_key_top:
                        self.key_tile_top = self.max_key_top
                        self.key_tile_yoffset = self.max_key_yoffset
                    elif self.key_tile_top == self.max_key_top:
                        if self.key_tile_yoffset < self.max_key_yoffset:
                            self.key_tile_yoffset = self.max_key_yoffset

    def keyPressEvent(self, event):
        """Capture a keyboard event."""

        log(f'key press event={event.key()}')

    def keyReleaseEvent(self, event):

        log(f'key release event={event.key()}')

    def wheelEvent(self, event):
        """Handle a mouse wheel rotation."""

        log(f"wheelEvent: {'UP' if event.angleDelta().y() < 0 else 'DOWN'}")

        if event.angleDelta().y() < 0:
            new_level = self.level + 1
        else:
            new_level = self.level - 1
        self.use_level(new_level)

    def use_level(self, level):
        """Use new map level.

        level  the new level to use

        This code will try to maintain the centre of the view at the same
        GEO coordinates, if possible.  The "key" tile is updated.

        Returns True if level change is OK, else False.
        """

        return self.zoom_level(level)

    def resizeEvent(self, event=None):
        """Widget resized, recompute some state."""

        # new widget size
        self.view_width = self.width()
        self.view_height = self.height()

        log(f'resizeEvent: event={event}, width={self.view_width}, height={self.view_height}')

        # recalculate the "top left" tile stuff
        self.recalc_wrap_limits()

        self.normalize_view_drag(0, 0)

    def recalc_wrap_limits(self):
        """Recalculate the maximum "key" tile information.
        
        Called if widget changes level or resized.
        .map_width, .map_height, .view_width and .view_height have been set.
        """

        # figure out the maximum 'key' tile coordinates
        tiles_in_view = self.view_width // self.tile_width
        left_margin = self.view_width - tiles_in_view*self.tile_width
        self.max_key_xoffset = -(self.tile_width - left_margin)
        self.max_key_left = self.num_tiles_x - tiles_in_view - 1

        tiles_in_view = self.view_height // self.tile_height
        margin = self.view_height - tiles_in_view*self.tile_height
        self.max_key_yoffset = -(self.tile_height - margin)
        self.max_key_top = self.num_tiles_y - tiles_in_view - 1

    def paintEvent(self, event):
        """Draw the base map and then the layers on top."""

        log(f'paintEvent: self.key_tile_left={self.key_tile_left}, self.key_tile_xoffset={self.key_tile_xoffset}')
        log(f'self.view_width={self.view_width}, self.view_height={self.view_height}')
        log(f'tile_width={self.tile_width}, tile_height={self.tile_height}')

        ######
        # The "key" tile position is maintained by other code, we just
        # assume it's set.  Figure out how to draw tiles, set up 'row_list' and
        # 'col_list' which are list of tile coords to draw (row and colums).
        ######

        col_list = []
        x_coord = self.key_tile_left
        x_pix_start = self.key_tile_xoffset
        while x_pix_start < self.view_width:
            log(f'loop: x_pix_start={x_pix_start}, self.view_width={self.view_width}')
            col_list.append(x_coord)
            if not self.wrap_x and x_coord >= self.num_tiles_x-1:
                break
            x_coord = (x_coord + 1) % self.num_tiles_x
            x_pix_start += self.tile_height

        row_list = []
        y_coord = self.key_tile_top
        y_pix_start = self.key_tile_yoffset
        while y_pix_start < self.view_height:
            row_list.append(y_coord)
            if not self.wrap_y and y_coord >= self.num_tiles_y-1:
                break
            y_coord = (y_coord + 1) % self.num_tiles_y
            y_pix_start += self.tile_height

        log(f'col_list={col_list}, row_list={row_list}')

        ######
        # Ready to update the view
        ######

        # prepare the canvas
        painter = QPainter()
        painter.begin(self)

        # paste all background tiles onto the view
        x_pix = self.key_tile_xoffset
        for x in col_list:
            y_pix = self.key_tile_yoffset
            for y in row_list:
                QPainter.drawPixmap(painter, x_pix, y_pix,
                                    self.tile_src.GetTile(x, y))
                log(f'drawing tile ({x}, {y}) at {x_pix}, {y_pix}')
                log(f'tile extends right to {x_pix+self.tile_width}')
                log(f'tile extends down to {y_pix+self.tile_height}')

                y_pix += self.tile_height
            x_pix += self.tile_width

        # now draw the layers of each type

        log('paintEvent: end')
        painter.end()

    def tile_frac_to_parts(self, t_frac, length):
        """Split a tile coordinate into integer and fractional parts.

        frac  a fractional tile coordinate
        length  size of tile width or height

        Return (int, frac) parts of 't_frac'.
        """

        int_part = int(t_frac)
        frac_part = int((t_frac - int_part) * length)

        return (int_part, frac_part)

    def tile_parts_to_frac(self, t_coord, t_offset, length):
        """Convert a tile coord plus offset to a fractional tile value.

        t_coord   the tile integer coordinate
        t_offset  the pixel further offset
        length    the width orr height of the tile

        Returns a fractional tile coordinate.
        """

        log(f'tile_parts_to_frac: t_coord={t_coord}, t_offset={t_offset}, length={length}')
        log(f'tile_parts_to_frac: returning t_coord + t_offset/length={t_coord + t_offset/length}')
        return t_coord + t_offset/length

    def zoom_tile(self, c_tile, scale):
        """Zoom into centre tile at given scale.

        c_tile  tuple (x_frac, y_frac) of fractional tile coords for point
        scale   2.0 if zooming in, 0.5 if zooming out

        Returns a tuple (zx_frac, zy_frac) of fractional coordinates of the
        point after the zoom.
        """

        # unpack the centre tile coords
        (x_frac, y_frac) = c_tile
        log(f'zoom_tile: x_frac={x_frac}, y_frac={y_frac}')

        # convert tile fractional coords to tile # + offset
        (tile_left, tile_xoff) = self.tile_frac_to_parts(x_frac, self.tile_width)
        (tile_top, tile_yoff) = self.tile_frac_to_parts(y_frac, self.tile_height)
        log(f'zoom_tile: tile_left={tile_left}, tile_xoff={tile_xoff}')

        if scale > 1:
            # assume scale is 2
            # a simple doubling of fractional coordinates
            if tile_xoff < self.tile_width // 2:
                tile_left = tile_left * 2
                tile_xoff = tile_xoff * 2
                log(f'zoom_tile: left half double, tile_left={tile_left}, tile_xoff={tile_xoff}')
            else:
                tile_left = tile_left*2 + 1
                tile_xoff = tile_xoff*2 - self.tile_width
                log(f'zoom_tile: right half double, tile_left={tile_left}, tile_xoff={tile_xoff}')
    
            if tile_yoff < self.tile_height // 2:
                tile_top = tile_top * 2
                tile_yoff = tile_yoff * 2
            else:
                tile_top = tile_top*2 + 1
                tile_yoff = tile_yoff*2 % self.tile_height
        else:
            # assume scale is 0.5
            # a simple halving of fractional coordinates
            log(f'BEFORE: tile_left={tile_left}, tile_xoff={tile_xoff}')
            tile_left = tile_left // 2
            if tile_left % 2 == 0:
                # point in left half of 2x2
                tile_xoff = tile_xoff // 2
            else:
                # point in right half of 2x2
                tile_xoff = (tile_xoff + self.tile_width) // 2

            tile_top = tile_top // 2
            if tile_top % 2 == 0:
                # point in top half of 2x2
                tile_yoff = tile_yoff // 2
            else:
                # point in bottom half of 2x2
                tile_yoff = (tile_yoff + self.tile_height) // 2
            log(f'AFTER: tile_left={tile_left}, tile_xoff={tile_xoff}')
    
        zx_frac = self.tile_parts_to_frac(tile_left, tile_xoff, self.tile_width)
        zy_frac = self.tile_parts_to_frac(tile_top, tile_yoff, self.tile_height)

        log(f'zoom_tile: returning ({zx_frac}, {zy_frac})')

        return (zx_frac, zy_frac)

    def tile_to_key(self, z_point, x, y):
        """Get new 'key' tile data given a zoom point and a view point.

        z_point  the tile coordinates of the zoom point (zx_tile, zy_tile)
        x, y     the view coordinates of the zoom point

        Returns (key_tile_left, key_tile_xoffset, key_tile.top, key_tile_yoffset)
        which define the new 'key' tile values after a zoom.
        """

        # split out X and Y fractional coordinates
        (zx_tile, zy_tile) = z_point

        # get tile fractions from the view point to the view edges
        x_off = x / self.tile_width
        y_off = y / self.tile_height

        # get the fractional coordinates of the left and top edges
        left_coord = zx_tile - x_off/self.tile_width
        top_coord = zy_tile - y_off/self.tile_height

        # get 'key' tile coordinates
        (l_int, l_frac) = self.tile_frac_to_parts(left_coord, self.tile_width)
        key_tile_left = l_int
        key_tile_xoffset = -l_frac # * self.tile_width
        log(f'tile_to_key: l_int={l_int}, l_frac={l_frac}, key_tile_left={key_tile_left}, key_tile_xoffset={key_tile_xoffset}')

        (r_int, r_frac) = self.tile_frac_to_parts(top_coord, self.tile_height)
        key_tile_top = r_int
        key_tile_yoffset = -r_frac # * self.tile_height

        return (key_tile_left, key_tile_xoffset, key_tile_top, key_tile_yoffset)

    def view_to_tile(self, x=None, y=None):
        """Convert view coordinates to the fractional tile coordinates.

        x, y  view point coordinates in pixels (view centre is default)

        Returns a tuple (tile_x, tile_y) of fraction tile coordinates of
        the given point in the view.

            map bounds
           +---------------------------------
           |    view bounds     |
           |   +----------------+--------
           |   |     centre tile|
           |   |     +------------------+
           |   |     |          |       |
           |   |     |          | tile_y|
           |   |     |          v       |
           |---+-----+--------->o       |
           |   |     | tile_x    \      |
           |   |     |         position |
           |         |                  |
                     |                  |
                     +------------------+

        This method is the reverse of self.tile_to_view().
        """

        # handle the default - centre of the view
        if x is None:
            x = self.view_width // 2
        if y is None:
            y = self.view_height // 2

        log(f'view_to_tile: .view_width={self.view_width}, .key_tile_left={self.key_tile_left}, .key_tile_xoffset={self.key_tile_xoffset}')
        log(f'view_to_tile: .view_height={self.view_height}, .key_tile_top={self.key_tile_top}, .key_tile_yoffset={self.key_tile_yoffset}')
        log(f'view_to_tile: x={x}, y={y}')

        # work out X tile coordinate
        dx = x - self.key_tile_xoffset     # pixels from key tile left to point
        log(f'view_to_tile: dx={dx} - self.key_tile_xoffset={self.key_tile_xoffset}')
        (dx_whole, dx_off) = divmod(dx, self.tile_width)   # (a // b, a % b)
        log(f'view_to_tile: dx_whole=dx // self.tile_width={dx_whole}')
        log(f'view_to_tile: dx_off=dx % self.tile_width={dx_off}')
        tile_x = self.key_tile_left + dx_whole + dx_off/self.tile_width
        log(f'view_to_tile: tile_x=self.key_tile_left + dx_whole + dx_off/self.tile_width={tile_x}')

        # work out Y tile coordinate
        d_y = y - self.key_tile_yoffset     # pixels from key tile top to point
        dy_whole = d_y // self.tile_height  # number of complete tiles to point
        dy_off = d_y % self.tile_height     # left over piyels
        tile_y = self.key_tile_top + dy_whole + dy_off/self.tile_height

        log(f'view_to_tile: returning {(tile_x, tile_y)}')

        return (tile_x, tile_y)

################################################################################
# Below are the "external" API methods.
################################################################################

    def dump_key_data(self):
        """Debug function to return string describing 'key' tile data."""

        return (f'\t.key_tile_left={self.key_tile_left}\n'
                f'\t.key_tile_top={self.key_tile_top}\n'
                f'\t.key_tile_xoffset={self.key_tile_xoffset}\n'
                f'\t.key_tile_yoffset={self.key_tile_yoffset}\n'
                f'\t.view_width={self.view_width}\n'
                f'\t.view_height={self.view_height}\n'
                f'\t.map_width={self.map_width}\n'
                f'\t.map_height={self.map_height}\n'
               )

    def zoom_level(self, level, x=None, y=None):
        """Zoom to a map level.

        level  map level to zoom to
        x, y   view coordinates of point around which we zoom

        Change the map zoom level to that given. Returns True if the zoom
        succeeded, else False. If False is returned the method call has no effect.
        """

        # if x,y not given, use view centre
        if x is None:
            x = self.view_width // 2
        if y is None:
            y = self.view_height // 2

        log(f'zoom_level: level={level}, x={x}, y={y}')
        log(f'zoom_level: before, key tile data:\n{self.dump_key_data()}')

        # get tile source to use the new level
        result = self.tile_src.UseLevel(level)

        # if tile-source changed, calculate new centre tile
        if result:
            # calculate zoom point tile coordinates before zoom
            z_point = self.view_to_tile()
            log(f'zoom_level: z_point={z_point}')

            # figure out the scale of the zoom (2 or 0.5)
            log(f'level={level}, self.level={self.level}')
            scale = (self.level + 1) / (level + 1)
            scale = 2**(level - self.level)
            log(f'zoom_level: scale={scale}')

            new_z_point = self.zoom_tile(z_point, scale)
            log(f'zoom_level: new_z_point={new_z_point}')

            new_key = self.tile_to_key(new_z_point, x, y)
            log(f'zoom_level: new_key={new_key}')

            (self.key_tile_left, self.key_tile_xoffset,
                    self.key_tile_top, self.key_tile_yoffset) = new_key

#            # get centre tile details and move to key
##            xtile = self.key_tile_left
#            xoffset = self.key_tile_xoffset
#            while xoffset > 0:
#                log(f'canon X: xoffset={xoffset}, xtile={xtile}')
#                if xtile == 0:
#                    break
#                xtile -= 1
#                xoffset -= self.tile_width
#
#            ytile = self.key_tile_top
#            yoffset = self.key_tile_yoffset
#            while yoffset > 0:
#                log(f'canon Y: yoffset={yoffset}, ytile={ytile}')
#                if ytile == 0:
#                    break
#                ytile -= 1
#                yoffset -= self.tile_height

            # move to new level
            self.level = level
            (self.num_tiles_x, self.num_tiles_y, _, _) = self.tile_src.GetInfo(level)
            self.map_width = self.num_tiles_x * self.tile_width
            self.map_height = self.num_tiles_y * self.tile_height
            log(f'self.map_width={self.map_width}, self.map_height={self.map_height}')

#        self.key_tile_left = 0      # tile coordinates of key tile
#        self.key_tile_top = 0
#        self.key_tile_xoffset = 0   # view coordinates of key tile wrt view
#        self.key_tile_yoffset = 0

#            # calculate the key tile data
#            while xtile > 0:
#                xtile -= self.tile_width
#                xoffset -= 1
#            log(f'X normalized to xtile={xtile}, xoffset={xoffset}')
#            while ytile > 0:
#                ytile -= self.tile_height
#                yoffset -= 1
#            log(f'Y normalized to ytile={ytile}, yoffset={yoffset}')
#
#            self.key_tile_left = xtile
#            self.key_tile_top = ytile
#            self.key_tile_xoffset = xoffset
#            self.key_tile_yoffset = yoffset

            self.recalc_wrap_limits()

            self.update()       # redraw the map

        log(f'zoom_level:  after, key tile data:\n{self.dump_key_data()}')

        return result

    def pan_position(self, posn):
        """Pan to the given position in the current map zoom level.

        posn  a tuple (xgeo, ygeo)
        """

        pass

    def zoom_level_position(self, level, posn):
        """Zoom to a map level and pan to the given position in the map.

        level  map level to zoom to
        posn  a tuple (xgeo, ygeo)
        """

        pass

    def zoom_area(self, posn, size):
        """Zoom to a map level and area.

        posn  a tuple (xgeo, ygeo) of the centre of the area to show
        size  a tuple (width, height) of area in geo coordinate units

        Zooms to a map level and pans to a position such that the specified area
        is completely within the view. Provides a simple way to ensure an
        extended feature is wholly within the centre of the view.
        """

        pass
