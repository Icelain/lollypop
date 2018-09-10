# Copyright (c) 2014-2018 Cedric Bellegarde <cedric.bellegarde@adishatz.org>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from gi.repository import Gtk

from lollypop.view_flowbox import FlowBoxView
from lollypop.widgets_album_simple import AlbumSimpleWidget
from lollypop.pop_album import AlbumPopover
from lollypop.define import ArtSize
from lollypop.controller_view import ViewController


class AlbumsBoxView(FlowBoxView, ViewController):
    """
        Show albums in a box
    """

    def __init__(self, genre_ids, artist_ids):
        """
            Init album view
            @param genre ids as [int]
            @param artist ids as [int]
        """
        FlowBoxView.__init__(self)
        ViewController.__init__(self)
        self._widget_class = AlbumSimpleWidget
        self.__genre_ids = genre_ids
        self.__artist_ids = artist_ids
        self._box.connect("child-activated", self.__on_album_activated)
        self.connect_current_changed_signal()
        self.connect_artwork_changed_signal("album")

#######################
# PROTECTED           #
#######################
    def _on_current_changed(self, player):
        """
            Update children state
            @param player as Player
        """
        for child in self._box.get_children():
            child.set_selection()

    def _on_artwork_changed(self, artwork, album_id):
        """
            Update children artwork if matching album id
            @param artwork as Artwork
            @param album_id as int
        """
        for child in self._box.get_children():
            child.set_artwork(album_id)

    def _add_items(self, album_ids, *args):
        """
            Add albums to the view
            Start lazy loading
            @param album ids as [int]
        """
        widget = FlowBoxView._add_items(self, album_ids,
                                        self.__genre_ids, self.__artist_ids)
        if widget is not None:
            widget.connect("overlayed", self._on_overlayed)

#######################
# PRIVATE             #
#######################
    def __on_album_activated(self, flowbox, album_widget):
        """
            Show Context view for activated album
            @param flowbox as Gtk.Flowbox
            @param album_widget as AlbumSimpleWidget
        """
        # Here some code for touch screens
        # If mouse pointer activate Gtk.FlowBoxChild, overlay is on,
        # as enter notify event enabled it
        # Else, we are in touch screen, first time show overlay, next time
        # show popover
        if not album_widget.is_overlay:
            album_widget.show_overlay(True)
            return
        artwork = album_widget.get_artwork()
        if artwork is None:
            return
        # If widget top not on screen, popover will fail to show
        # FIXME: Report a bug and check always true
        (x, y) = album_widget.translate_coordinates(self._scrolled, 0, 0)
        if y < 0:
            y = album_widget.translate_coordinates(self._box, 0, 0)[1]
            self._scrolled.get_allocation().height + y
            self._scrolled.get_vadjustment().set_value(y)
        allocation = self.get_allocation()
        (x, top_height) = album_widget.translate_coordinates(self, 0, 0)
        bottom_height = allocation.height -\
            album_widget.get_allocation().height -\
            top_height
        if bottom_height > top_height:
            height = bottom_height
        else:
            height = top_height
        popover = AlbumPopover(album_widget.album,
                               self.__genre_ids,
                               self.__artist_ids,
                               allocation.width,
                               height,
                               ArtSize.NONE)
        popover.set_relative_to(artwork)
        popover.set_position(Gtk.PositionType.BOTTOM)
        album_widget.show_overlay(False)
        album_widget.lock_overlay(True)
        popover.connect("closed", self.__on_album_popover_closed, album_widget)
        popover.show()
        artwork.set_opacity(0.9)

    def __on_album_popover_closed(self, popover, album_widget):
        """
            Remove overlay and restore opacity
            @param popover as Gtk.Popover
            @param album_widget as AlbumWidget
        """
        album_widget.lock_overlay(False)
        album_widget.get_artwork().set_opacity(1)
