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

from gi.repository import GLib, Gtk

from lollypop.utils import tracks_to_albums
from lollypop.view import LazyLoadingView
from lollypop.define import App, ViewType, MARGIN, MARGIN_SMALL, Type, Size
from lollypop.objects_album import Album
from lollypop.objects_track import Track
from lollypop.controller_view import ViewController, ViewControllerType
from lollypop.widgets_banner_playlist import PlaylistBannerWidget
from lollypop.view_albums_list import AlbumsListView
from lollypop.logger import Logger
from lollypop.helper_filtering import FilteringHelper
from lollypop.helper_signals import SignalsHelper, signals_map
from lollypop.helper_size_allocation import SizeAllocationHelper


class PlaylistsView(FilteringHelper, LazyLoadingView, ViewController,
                    SignalsHelper, SizeAllocationHelper):
    """
        View showing playlists
    """

    @signals_map
    def __init__(self, playlist_id, view_type):
        """
            Init PlaylistView
            @parma playlist_id as int
            @param view_type as ViewType
        """
        LazyLoadingView.__init__(self, view_type)
        ViewController.__init__(self, ViewControllerType.ALBUM)
        FilteringHelper.__init__(self)
        SizeAllocationHelper.__init__(self)
        self._playlist_id = playlist_id
        # We remove SCROLLED because we want to be the scrolled view
        self._view = AlbumsListView([], [], view_type & ~ViewType.SCROLLED)
        self._view.set_width(Size.MEDIUM)
        if view_type & ViewType.DND:
            self._view.dnd_helper.connect("dnd-finished",
                                          self.__on_dnd_finished)
        self._view.show()
        self.__banner = PlaylistBannerWidget(playlist_id, self._view)
        self.__banner.connect("scroll", self._on_banner_scroll)
        self.__banner.connect("jump-to-current", self.__on_jump_to_current)
        self.__banner.show()
        self._overlay = Gtk.Overlay.new()
        self._overlay.show()
        self._overlay.add(self._scrolled)
        self._viewport.add(self._view)
        self._overlay.add_overlay(self.__banner)
        self.add(self._overlay)
        self.__banner.set_view_type(view_type)
        return [
                (App().playlists, "playlist-track-added",
                 "_on_playlist_track_added"),
                (App().playlists, "playlist-track-removed",
                 "_on_playlist_track_removed"),
                (App().playlists, "playlists-changed", "_on_playlist_changed")
        ]

    def populate(self):
        """
            Populate view
        """
        def load():
            track_ids = []
            if self._playlist_id == Type.LOVED:
                for track_id in App().tracks.get_loved_track_ids():
                    if track_id not in track_ids:
                        track_ids.append(track_id)
            else:
                for track_id in App().playlists.get_track_ids(
                        self._playlist_id):
                    if track_id not in track_ids:
                        track_ids.append(track_id)
            return tracks_to_albums(
                [Track(track_id) for track_id in track_ids])

        App().task_helper.run(load, callback=(self._view.populate,))

    def stop(self):
        """
            Stop populating
        """
        self._view.stop()

    def activate_child(self):
        """
            Activated typeahead row
        """
        try:
            if App().player.is_party:
                App().lookup_action("party").change_state(
                    GLib.Variant("b", False))
            for child in self.filtered:
                style_context = child.get_style_context()
                if style_context.has_class("typeahead"):
                    if hasattr(child, "album"):
                        App().player.play_album(child.album)
                    else:
                        track = child.track
                        App().player.add_album(track.album)
                        App().player.load(track.album.get_track(track.id))
                style_context.remove_class("typeahead")
        except Exception as e:
            Logger.error("PlaylistsView::activate_child: %s" % e)

    def remove_from_playlist(self, object):
        """
            Remove object from playlist
            @param object as Album/Track
        """
        if isinstance(object, Album):
            tracks = object.tracks
        else:
            tracks = [object]
        App().playlists.remove_tracks(self._playlist_id, tracks)

    @property
    def args(self):
        """
            Get default args for __class__, populate() plus sidebar_id and
            scrolled position
            @return ({}, int, int)
        """
        if self._view_type & ViewType.SCROLLED:
            position = self._scrolled.get_vadjustment().get_value()
        else:
            position = 0
        return ({"playlist_id": self._playlist_id,
                 "view_type": self.view_type}, self.sidebar_id, position)

    @property
    def filtered(self):
        """
            Get filtered children
            @return [Gtk.Widget]
        """
        filtered = []
        for child in self._view.children:
            filtered.append(child)
            for subchild in child.children:
                filtered.append(subchild)
        return filtered

    @property
    def scroll_shift(self):
        """
            Add scroll shift on y axes
            @return int
        """
        return self.__banner.height + MARGIN

    @property
    def scroll_relative_to(self):
        """
            Relative to scrolled widget
            @return Gtk.Widget
        """
        return self._view

#######################
# PROTECTED           #
#######################
    def _on_adaptive_changed(self, window, status):
        """
            Handle adaptive mode for views
        """
        LazyLoadingView._on_adaptive_changed(self, window, status)
        self.__banner.set_view_type(self._view_type)
        self.__set_margin()

    def _on_value_changed(self, adj):
        """
            Update banner
            @param adj as Gtk.Adjustment
        """
        LazyLoadingView._on_value_changed(self, adj)
        reveal = self.should_reveal_header(adj)
        self.__banner.set_reveal_child(reveal)
        if reveal:
            self.__set_margin()
        else:
            self._scrolled.get_vscrollbar().set_margin_top(0)

    def _on_playlist_track_added(self, playlists, playlist_id, uri):
        """
            Append track to album list
            @param playlists as Playlists
            @param playlist_id as int
            @param uri as str
        """
        if playlist_id == self._playlist_id:
            track = Track(App().tracks.get_id_by_uri(uri))
            album = Album(track.album.id)
            album.set_tracks([track])
            self._view.insert_album(album, True, -1)

    def _on_playlist_track_removed(self, playlists, playlist_id, uri):
        """
            Remove track from album list
            @param playlists as Playlists
            @param playlist_id as int
            @param uri as str
        """
        if playlist_id == self._playlist_id:
            track = Track(App().tracks.get_id_by_uri(uri))
            children = self._view.children
            for album_row in children:
                if album_row.album.id == track.album.id:
                    for track_row in album_row.children:
                        if track_row.track.id == track.id:
                            track_row.destroy()
                            if len(children) == 1:
                                album_row.destroy()
                                break

    def _on_playlist_changed(self, playlists, playlist_id):
        """
            Destroy self if removed
            @param playlists as Playlists
            @param playlist_id as int
        """
        if playlist_id == self._playlist_id and\
                not playlists.exists(playlist_id):
            App().window.container.go_back()

#######################
# PRIVATE             #
#######################
    def __set_margin(self):
        """
            Set margin from header
        """
        self._view.set_margin_top(self.__banner.height + MARGIN_SMALL)
        self._scrolled.get_vscrollbar().set_margin_top(self.__banner.height)

    def __on_jump_to_current(self, banner):
        """
            Jump to current track
            @param banner as PlaylistBannerWidget
        """
        self._view.jump_to_current(self._scrolled)

    def __on_dnd_finished(self, dnd_helper):
        """
            Save playlist if needed
            @param dnd_helper as DNDHelper
        """
        if self._playlist_id >= 0:
            uris = []
            for child in self._view.children:
                for track in child.album.tracks:
                    uris.append(track.uri)
            App().playlists.clear(self._playlist_id)
            App().playlists.add_uris(self._playlist_id, uris)


class SmartPlaylistsView(PlaylistsView):
    """
        View showing smart playlists
    """

    def __init__(self, playlist_id, view_type):
        """
            Init PlaylistView
            @parma playlist_id as int
            @param view_type as ViewType
        """
        PlaylistsView.__init__(self, playlist_id, view_type)

    def populate(self):
        """
            Populate view
        """
        def load():
            request = App().playlists.get_smart_sql(self._playlist_id)
            track_ids = App().db.execute(request)
            return tracks_to_albums(
                [Track(track_id) for track_id in track_ids])

        App().task_helper.run(load, callback=(self._view.populate,))
