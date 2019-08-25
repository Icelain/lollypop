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

from gi.repository import Gtk, GLib

from random import sample

from lollypop.define import App, Type
from lollypop.objects_track import Track
from lollypop.widgets_albums_rounded import RoundedAlbumsWidget


class PlaylistRoundedWidget(RoundedAlbumsWidget):
    """
        Playlist widget showing cover for 4 albums
    """

    def __init__(self, playlist_id, view_type, font_height):
        """
            Init widget
            @param playlist_id as playlist_id
            @param view_type as ViewType
            @param font_height as int
        """
        self.__font_height = font_height
        name = sortname = App().playlists.get_name(playlist_id)
        RoundedAlbumsWidget.__init__(self, playlist_id, name,
                                     sortname, view_type)
        self._track_ids = []
        self._genre = Type.PLAYLISTS

    def populate(self):
        """
            Populate widget content
        """
        if self._artwork is None:
            RoundedAlbumsWidget.populate(self)
            label = Gtk.Label.new()
            markup = "<b>%s</b>" % GLib.markup_escape_text(self.name)
            label.set_markup(markup)
            label.show()
            self._grid.add(label)
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

    @property
    def track_ids(self):
        """
            Get current track ids
            @return [int]
        """
        return self._track_ids

#######################
# PROTECTED           #
#######################
    def _get_album_ids(self):
        """
            Get album ids
            @return [int]
        """
        album_ids = []
        if App().playlists.get_smart(self._data):
            request = App().playlists.get_smart_sql(self._data)
            if request is not None:
                self._track_ids = App().db.execute(request)
        else:
            self._track_ids = App().playlists.get_track_ids(self._data)
        sample(self._track_ids, len(self._track_ids))
        for track_id in self._track_ids:
            track = Track(track_id)
            if track.album.id not in album_ids:
                album_ids.append(track.album.id)
            if len(album_ids) == self._ALBUMS_COUNT:
                break
        return album_ids

#######################
# PRIVATE             #
#######################
