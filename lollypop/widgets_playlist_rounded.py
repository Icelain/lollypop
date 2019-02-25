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

from random import sample

from lollypop.define import App, Type, SelectionListMask
from lollypop.objects import Track, Album, Disc
from lollypop.widgets_albums_rounded import RoundedAlbumsWidget
from lollypop.helper_overlay_playlist import OverlayPlaylistHelper


class PlaylistRoundedWidget(RoundedAlbumsWidget, OverlayPlaylistHelper):
    """
        Playlist widget showing cover for 4 albums
    """

    def __init__(self, playlist_id, obj, view_type):
        """
            Init widget
            @param playlist_id as playlist_id
            @param obj as Track/Album
            @param view_type as ViewType
        """
        OverlayPlaylistHelper.__init__(self)
        name = sortname = App().playlists.get_name(playlist_id)
        RoundedAlbumsWidget.__init__(self, playlist_id, name,
                                     sortname, view_type)
        self._track_ids = []
        self._obj = obj
        self._genre = Type.PLAYLISTS
        if obj is not None:
            if isinstance(obj, Album) or\
                    isinstance(obj, Disc):
                self._add = not App().playlists.exists_album(
                    playlist_id,
                    obj)
            else:
                self._add = not App().playlists.exists_track(
                    playlist_id,
                    obj.uri)

    def populate(self):
        """
            Populate widget content
        """
        self.__set_album_ids()
        RoundedAlbumsWidget.populate(self)
        self._widget.connect("enter-notify-event", self._on_enter_notify)
        self._widget.connect("leave-notify-event", self._on_leave_notify)
        self.connect("button-release-event", self.__on_button_release_event)
        self.__gesture = Gtk.GestureLongPress.new(self)
        self.__gesture.connect("pressed", self.__on_gesture_pressed)
        # We want to get release event after gesture
        self.__gesture.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        self.__gesture.set_button(0)

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

#######################
# PRIVATE             #
#######################
    def __set_album_ids(self):
        """
            Set album ids
        """
        if App().playlists.get_smart(self._data):
            request = App().playlists.get_smart_sql(self._data)
            if request is not None:
                self._track_ids = App().db.execute(request)
        else:
            self._track_ids = App().playlists.get_track_ids(self._data)
        sample(self._track_ids, len(self._track_ids))
        for track_id in self._track_ids:
            track = Track(track_id)
            if track.album.id not in self._album_ids:
                self._album_ids.append(track.album.id)
            if len(self._album_ids) == self._ALBUMS_COUNT:
                break

    def __popup_menu(self, widget):
        """
            Popup menu for track
            @param widget as Gtk.Widget
        """
        from lollypop.pop_menu_views import ViewsMenuPopover
        from lollypop.view_playlists_manager import PlaylistsManagerView
        popover = ViewsMenuPopover(self.get_ancestor(PlaylistsManagerView),
                                   self.data,
                                   SelectionListMask.PLAYLISTS)
        popover.set_relative_to(widget)
        popover.popup()

    def __on_gesture_pressed(self, gesture, x, y):
        """
            Show current track menu
            @param gesture as Gtk.GestureLongPress
            @param x as float
            @param y as float
        """
        self.__popup_menu(self)

    def __on_button_release_event(self, widget, event):
        """
            Handle button release event
            @param widget as Gtk.Widget
            @param event as Gdk.Event
        """
        if event.button == 1:
            self.activate()
        elif event.button == 3:
            self.__popup_menu(self)
        return True
