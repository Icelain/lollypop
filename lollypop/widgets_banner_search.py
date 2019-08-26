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

from random import shuffle

from lollypop.define import App, ArtSize, ArtBehaviour, Type, ViewType
from lollypop.define import Shuffle
from lollypop.widgets_banner import BannerWidget
from lollypop.logger import Logger
from lollypop.utils import update_button


class SearchBannerWidget(BannerWidget):
    """
        Banner for search
    """

    def __init__(self, view):
        """
            Init banner
            @param view as PlaylistView
        """
        BannerWidget.__init__(self, view.args[0]["view_type"])
        builder = Gtk.Builder()
        builder.add_from_resource("/org/gnome/Lollypop/SearchBannerWidget.ui")
        self.__view = view
        self.__play_button = builder.get_object("play_button")
        self.__new_button = builder.get_object("new_button")
        self.__spinner = builder.get_object("spinner")
        self.__entry = builder.get_object("entry")
        self.add_overlay(builder.get_object("widget"))
        self.connect("map", self.__on_map)
        builder.connect_signals(self)

    def set_view_type(self, view_type):
        """
            Update view type
            @param view_type as ViewType
        """
        BannerWidget.set_view_type(self, view_type)
        if view_type & ViewType.MEDIUM:
            style = "menu-button"
            icon_size = Gtk.IconSize.BUTTON
            self.__entry.set_size_request(200, -1)
        else:
            style = "menu-button-48"
            icon_size = Gtk.IconSize.LARGE_TOOLBAR
            self.__entry.set_size_request(400, -1)
        update_button(self.__play_button, style,
                      icon_size, "media-playback-start-symbolic")
        update_button(self.__new_button, style,
                      icon_size, "document-new-symbolic")

    @property
    def spinner(self):
        """
            Get banner spinner
            @return Gtk.Spinner
        """
        return self.__spinner

    @property
    def entry(self):
        """
            Get banner entry
            @return Gtk.Entry
        """
        return self.__entry

    @property
    def new_button(self):
        """
            Get new button
            @return Gtk.Button
        """
        return self.__new_button

    @property
    def play_button(self):
        """
            Get play button
            @return Gtk.Button
        """
        return self.__play_button

    @property
    def height(self):
        """
            Get wanted height
            @return int
        """
        return ArtSize.SMALL

#######################
# PROTECTED           #
#######################
    def _handle_size_allocate(self, allocation):
        """
            Update artwork
            @param allocation as Gtk.Allocation
        """
        if BannerWidget._handle_size_allocate(self, allocation):
            App().art_helper.set_banner_artwork(
                # +100 to prevent resize lag
                allocation.width + 100,
                ArtSize.SMALL,
                self._artwork.get_scale_factor(),
                ArtBehaviour.BLUR |
                ArtBehaviour.DARKER,
                self.__on_artwork)

    def _on_play_button_clicked(self, button):
        """
            Play search
            @param button as Gtk.Button
        """
        try:
            App().player.clear_albums()
            shuffle_setting = App().settings.get_enum("shuffle")
            children = self.__view.children
            if shuffle_setting == Shuffle.ALBUMS:
                shuffle(children)
            for child in children:
                App().player.add_album(child.album)
            App().player.load(App().player.albums[0].tracks[0])
        except Exception as e:
            Logger.error("SearchPopover::_on_play_button_clicked(): %s", e)

    def _on_new_button_clicked(self, button):
        """
            Create a new playlist based on search
            @param button as Gtk.Button
        """
        App().task_helper.run(self.__search_to_playlist)

#######################
# PRIVATE             #
#######################
    def __search_to_playlist(self):
        """
            Create a new playlist based on search
        """
        tracks = []
        for child in self.__view.children:
            tracks += child.album.tracks
        if tracks:
            playlist_id = App().playlists.get_id(self.__current_search)
            if playlist_id is None:
                playlist_id = App().playlists.add(self.__current_search)
            App().playlists.add_tracks(playlist_id, tracks)
            App().window.container.show_view(Type.PLAYLISTS, [playlist_id])

    def __on_map(self, widget):
        """
            Grab focus
            @param widget as Gtk.Widget
        """
        GLib.idle_add(self.__entry.grab_focus)

    def __on_artwork(self, surface):
        """
            Set album artwork
            @param surface as str
        """
        if surface is not None:
            self._artwork.set_from_surface(surface)
