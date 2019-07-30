# Copyright (c) 2014-2019 Cedric Bellegarde <cedric.bellegarde@adishatz.org>
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

from random import shuffle

from lollypop.define import App, ArtBehaviour
from lollypop.utils import get_icon_name
from lollypop.objects_album import Album
from lollypop.widgets_flowbox_rounded import RoundedFlowBoxWidget


class RoundedArtistWidget(RoundedFlowBoxWidget):
    """
        Artist photo or artist's albums in a rounded widget
    """

    def __init__(self, item, view_type, font_height):
        """
            Init widget
            @param item as (int, str, str)
            @param view_type as ViewType
            @param font_height as int
        """
        self.__font_height = font_height
        RoundedFlowBoxWidget.__init__(self, item[0], item[1],
                                      item[1], view_type)

    def populate(self):
        """
            Populate widget content
        """
        if self._artwork is None:
            RoundedFlowBoxWidget.populate(self)
            self._grid.add(self._label)
            self.connect("destroy", self.__on_destroy)
        else:
            self.set_artwork()

    def set_artwork(self):
        """
            Set artist artwork
        """
        self._set_artwork()

    def set_view_type(self, view_type):
        """
            Update view type
            @param view_type as ViewType
        """
        RoundedFlowBoxWidget.set_view_type(self, view_type)
        self.set_size_request(self._art_size,
                              self._art_size + self.__font_height)

#######################
# PROTECTED           #
#######################
    def _set_artwork(self):
        """
            Set artist artwork
        """
        def set_icon_name():
            icon_name = get_icon_name(self._data) or "avatar-default-symbolic"
            self._artwork.set_from_icon_name(icon_name, Gtk.IconSize.DIALOG)
            self.emit("populated")
            self._artwork.get_style_context().add_class("artwork-icon-large")

        if self._artwork is None:
            return
        RoundedFlowBoxWidget.set_artwork(self)
        if self._data < 0:
            set_icon_name()
        elif App().settings.get_value("artist-artwork"):
            App().art_helper.set_artist_artwork(
                                            self.name,
                                            self._art_size,
                                            self._art_size,
                                            self._artwork.get_scale_factor(),
                                            ArtBehaviour.ROUNDED |
                                            ArtBehaviour.CROP_SQUARE |
                                            ArtBehaviour.CACHE,
                                            self.__on_artist_artwork)
        else:
            album_ids = App().albums.get_ids([self._data], [])
            if album_ids:
                shuffle(album_ids)
                App().art_helper.set_album_artwork(
                                            Album(album_ids[0]),
                                            self._art_size,
                                            self._art_size,
                                            self._artwork.get_scale_factor(),
                                            ArtBehaviour.ROUNDED |
                                            ArtBehaviour.CROP_SQUARE |
                                            ArtBehaviour.CACHE,
                                            self.__on_artist_artwork)
            else:
                set_icon_name()

#######################
# PRIVATE             #
#######################
    def __on_artist_artwork(self, surface):
        """
            Finish widget initialisation
            @param surface as cairo.Surface
        """
        if self._artwork is None:
            return
        if surface is None:
            self._artwork.set_from_icon_name("avatar-default-symbolic",
                                             Gtk.IconSize.DIALOG)
        else:
            self._artwork.set_from_surface(surface)
        if self._artwork.props.surface is None:
            self._artwork.get_style_context().add_class("artwork-icon")
        self.emit("populated")

    def __on_destroy(self, widget):
        """
            Destroyed widget
            @param widget as Gtk.Widget
        """
        self.__artwork = None
