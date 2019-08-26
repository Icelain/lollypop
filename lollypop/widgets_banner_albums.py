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

from gi.repository import Gtk, GObject

from lollypop.define import App, ArtSize, ArtBehaviour, ViewType
from lollypop.widgets_banner import BannerWidget
from lollypop.shown import ShownLists


class AlbumsBannerWidget(BannerWidget):
    """
        Banner for albums
    """

    __gsignals__ = {
        "play-all": (GObject.SignalFlags.RUN_FIRST, None, (bool,))
    }

    def __init__(self, genre_ids, artist_ids, view_type):
        """
            Init banner
            @param genre_ids as [int]
            @param artist_ids as [int]
            @param view_type as ViewType
        """
        BannerWidget.__init__(self, view_type)
        self.__genre_ids = genre_ids
        self.__artist_ids = artist_ids
        builder = Gtk.Builder()
        builder.add_from_resource(
            "/org/gnome/Lollypop/AlbumsBannerWidget.ui")
        self.__title_label = builder.get_object("title")
        self.__duration_label = builder.get_object("duration")
        self.__play_button = builder.get_object("play_button")
        self.__shuffle_button = builder.get_object("shuffle_button")
        self.__menu_button = builder.get_object("menu_button")
        self.add_overlay(builder.get_object("widget"))
        genres = []
        for genre_id in genre_ids:
            if genre_id < 0:
                genres.append(ShownLists.IDS[genre_id])
            else:
                genres.append(App().genres.get_name(genre_id))
        self.__title_label.set_label(",".join(genres))
        builder.connect_signals(self)

    def set_view_type(self, view_type):
        """
            Update view type
            @param view_type as ViewType
        """
        def update_button(button, style, icon_size, icon_name):
            context = button.get_style_context()
            context.remove_class("menu-button-48")
            context.remove_class("menu-button")
            context.add_class(style)
            button.get_image().set_from_icon_name(icon_name, icon_size)

        BannerWidget.set_view_type(self, view_type)
        duration_context = self.__duration_label.get_style_context()
        title_context = self.__title_label.get_style_context()
        for c in title_context.list_classes():
            title_context.remove_class(c)
        for c in duration_context.list_classes():
            duration_context.remove_class(c)
        if view_type & ViewType.MEDIUM:
            style = "menu-button"
            icon_size = Gtk.IconSize.BUTTON
            title_context.add_class("text-large")
        else:
            style = "menu-button-48"
            icon_size = Gtk.IconSize.LARGE_TOOLBAR
            title_context.add_class("text-x-large")
            duration_context.add_class("text-large")
        update_button(self.__play_button, style,
                      icon_size, "media-playback-start-symbolic")
        update_button(self.__shuffle_button, style,
                      icon_size, "media-playlist-shuffle-symbolic")

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
            Play playlist
            @param button as Gtk.Button
        """
        self.emit("play-all", False)

    def _on_shuffle_button_clicked(self, button):
        """
            Play playlist shuffled
            @param button as Gtk.Button
        """
        self.emit("play-all", True)

#######################
# PRIVATE             #
#######################
    def __on_artwork(self, surface):
        """
            Set album artwork
            @param surface as str
        """
        if surface is not None:
            self._artwork.set_from_surface(surface)