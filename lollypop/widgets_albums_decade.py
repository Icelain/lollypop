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

from gi.repository import GLib

from lollypop.define import App, Type
from lollypop.widgets_albums_rounded import RoundedAlbumsWidget
from lollypop.helper_overlay_decade import OverlayDecadeHelper
from lollypop.objects_album import Album


class AlbumsDecadeWidget(RoundedAlbumsWidget, OverlayDecadeHelper):
    """
        Decade widget showing cover for 4 albums
    """

    def __init__(self, item_ids, view_type, font_height):
        """
            Init widget
            @param decade as [int]
            @param view_type as ViewType
            @param font_height as int
        """
        OverlayDecadeHelper.__init__(self)
        self.__font_height = font_height
        decade_str = "%s - %s" % (item_ids[0], item_ids[-1])
        RoundedAlbumsWidget.__init__(self, item_ids, decade_str,
                                     decade_str, view_type)
        self._genre = Type.YEARS

    def populate(self):
        """
            Populate widget content
        """
        if self._artwork is None:
            RoundedAlbumsWidget.populate(self)
        else:
            self.set_artwork()

    def set_view_type(self, view_type):
        """
            Update view type
            @param view_type as ViewType
        """
        RoundedAlbumsWidget.set_view_type(self, view_type)
        self.set_size_request(self._art_size,
                              self._art_size + self.__font_height)

#######################
# PROTECTED           #
#######################
    def _get_album_ids(self):
        """
            Get album ids
            @return [int]
        """
        album_ids = []
        for year in self._data:
            album_ids += App().albums.get_albums_for_year(year,
                                                          self._ALBUMS_COUNT)
            l = len(album_ids)
            if l < self._ALBUMS_COUNT:
                album_ids += App().albums.get_compilations_for_year(
                                                       year,
                                                       self._ALBUMS_COUNT)
        return album_ids

    def _on_play_clicked(self, button):
        """
            Play decade
            @param button as Gtk.Button
        """
        if App().player.is_party:
            App().lookup_action("party").change_state(GLib.Variant("b", False))
        album_ids = []
        for year in self._data:
            album_ids += App().albums.get_albums_for_year(year)
            album_ids += App().albums.get_compilations_for_year(year)
        albums = [Album(album_id) for album_id in album_ids]
        App().player.play_albums(albums)

#######################
# PRIVATE             #
#######################
