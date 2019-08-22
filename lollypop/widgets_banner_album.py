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

from lollypop.define import App, ArtSize, MARGIN, Type, ViewType, Size
from lollypop.define import ArtBehaviour
from lollypop.widgets_rating import RatingWidget
from lollypop.widgets_loved import LovedWidget
from lollypop.widgets_cover import CoverWidget
from lollypop.widgets_banner import BannerWidget
from lollypop.utils import get_human_duration, on_query_tooltip
from lollypop.utils import set_cursor_hand2, popup_widget
from lollypop.helper_signals import SignalsHelper, signals
from lollypop.helper_gestures import GesturesHelper


class AlbumBannerWidget(BannerWidget, SignalsHelper):
    """
        Banner for album
    """

    @signals
    def __init__(self, album, view_type=ViewType.DEFAULT):
        """
            Init cover widget
            @param album
            @param view_type as ViewType
        """
        BannerWidget.__init__(self, view_type)
        self.__cloud_image = None
        self.__album = album
        self.set_property("valign", Gtk.Align.START)
        builder = Gtk.Builder()
        builder.add_from_resource("/org/gnome/Lollypop/AlbumBannerWidget.ui")
        builder.connect_signals(self)
        self.__title_label = builder.get_object("name_label")
        self.__title_label.connect("query-tooltip", on_query_tooltip)
        self.__info_label = builder.get_object("info_label")
        self.__play_button = builder.get_object("play_button")
        self.__add_button = builder.get_object("add_button")
        self.__menu_button = builder.get_object("menu_button")
        self.__cover_widget = CoverWidget(album, view_type | ViewType.MEDIUM)
        self.__cover_widget.set_vexpand(True)
        self.__cover_widget.show()
        album_name = GLib.markup_escape_text(album.name)
        markup = "<b>%s</b>" % album_name
        if view_type & ViewType.ALBUM:
            artist_name = GLib.markup_escape_text(", ".join(album.artists))
            if view_type & ViewType.SMALL:
                markup += "\n<span alpha='40000'>%s</span>" % artist_name
            else:
                markup += "\n<span size='x-small' alpha='40000'>%s</span>" %\
                                                                  artist_name
        self.__title_label.set_markup(markup)
        duration = App().albums.get_duration(self.__album.id,
                                             self.__album.genre_ids)
        human_duration = get_human_duration(duration)
        markup = ""
        if album.year is not None:
            markup = "<b>%s</b>" % album.year
        markup += "\n<span alpha='40000'>%s</span>" % human_duration
        self.__info_label.set_markup(markup)
        info_eventbox = builder.get_object("info_eventbox")
        info_eventbox.connect("realize", set_cursor_hand2)
        self.__gesture = GesturesHelper(
            info_eventbox, primary_press_callback=self._on_year_press)
        self.__widget = builder.get_object("widget")
        self.init_background()
        self.__widget.attach(self.__cover_widget, 0, 0, 1, 3)
        self.__rating_grid = builder.get_object("rating_grid")
        self.__rating_widget = RatingWidget(album, Gtk.IconSize.INVALID)
        self.__rating_widget.set_property("halign", Gtk.Align.START)
        self.__rating_widget.set_property("valign", Gtk.Align.CENTER)
        self.__rating_widget.show()
        self.__rating_grid.attach(self.__rating_widget, 1, 0, 1, 1)
        self.__loved_widget = LovedWidget(album, Gtk.IconSize.INVALID)
        self.__loved_widget.set_margin_start(10)
        self.__loved_widget.set_property("halign", Gtk.Align.START)
        self.__loved_widget.set_property("valign", Gtk.Align.CENTER)
        self.__loved_widget.show()
        self.__rating_grid.attach(self.__loved_widget, 2, 0, 1, 1)
        self.__cover_widget.set_margin_start(MARGIN)
        self.__title_label.set_margin_start(MARGIN)
        self.__info_label.set_margin_end(MARGIN)
        self.__rating_grid.set_margin_end(MARGIN)
        self.set_view_type(view_type)
        self.add_overlay(self.__widget)
        return [
                (App().art, "album-artwork-changed",
                 "_on_album_artwork_changed"),
                (App().player, "playback-changed", "_on_playback_changed")
        ]

    def set_view_type(self, view_type):
        """
            Update widget internals for view_type
            @param view_type as ViewType
        """
        BannerWidget.set_view_type(self, view_type)
        art_size = 0
        if view_type & ViewType.SMALL:
            art_size = ArtSize.MEDIUM
            style = "menu-button"
            icon_size = Gtk.IconSize.BUTTON
        elif view_type & ViewType.MEDIUM:
            art_size = ArtSize.BANNER
            style = "menu-button-48"
            icon_size = Gtk.IconSize.LARGE_TOOLBAR
        else:
            art_size = ArtSize.BANNER
            style = "menu-button-48"
            icon_size = Gtk.IconSize.LARGE_TOOLBAR
        self.__rating_widget.set_icon_size(icon_size)
        self.__loved_widget.set_icon_size(icon_size)
        if self.__cloud_image is not None:
            self.__cloud_image.set_from_icon_name("goa-panel-symbolic",
                                                  icon_size)
        self.__cover_widget.set_artwork(art_size)
        for (button, icon_name) in [
                       (self.__menu_button, "view-more-symbolic"),
                       (self.__play_button, "media-playback-start-symbolic"),
                       (self.__add_button, self.__get_add_button_icon_name())]:
            button_style_context = button.get_style_context()
            button_style_context.remove_class("menu-button-48")
            button_style_context.remove_class("menu-button")
            button_style_context.add_class(style)
            button.get_image().set_from_icon_name(icon_name, icon_size)
        self.__set_text_height(self._collapsed)

    def collapse(self, collapsed):
        """
            Collapse banner
            @param collapse as bool
        """
        BannerWidget.collapse(self, collapsed)
        self.__set_text_height(collapsed)
        if collapsed:
            self.__cover_widget.hide()
            self.__rating_grid.hide()
            self.__info_label.set_vexpand(True)
        elif self.get_allocated_width() >= Size.SMALL + 100:
            self.__cover_widget.show()
            self.__rating_grid.show()
            self.__info_label.set_vexpand(False)

    def set_selected(self, selected):
        """
            Mark widget as selected
            @param selected as bool
        """
        if selected:
            self.__widget.set_state_flags(Gtk.StateFlags.SELECTED, True)
        else:
            self.__widget.set_state_flags(Gtk.StateFlags.NORMAL, True)

#######################
# PROTECTED           #
#######################
    def _handle_size_allocate(self, allocation):
        """
            Update artwork
            @param allocation as Gtk.Allocation
        """
        if BannerWidget._handle_size_allocate(self, allocation):
            App().art_helper.set_album_artwork(
                    self.__album,
                    # +100 to prevent resize lag
                    allocation.width + 100,
                    ArtSize.BANNER + MARGIN * 2,
                    self._artwork.get_scale_factor(),
                    ArtBehaviour.BLUR_HARD |
                    ArtBehaviour.DARKER,
                    self.__on_album_artwork)
            if allocation.width < Size.SMALL + 100:
                self.__cover_widget.hide()
            elif not self._collapsed:
                self.__cover_widget.show()

    def _on_menu_button_clicked(self, button):
        """
            Show album menu
            @param button as Gtk.Button
        """
        from lollypop.widgets_menu import MenuBuilder
        from lollypop.menu_objects import AlbumMenu
        menu = AlbumMenu(self.__album, self._view_type,
                         App().window.is_adaptive)
        menu_widget = MenuBuilder(menu)
        menu_widget.show()
        popup_widget(menu_widget, button)

    def _on_play_button_clicked(self, button):
        """
            Play album
           @param button as Gtk.Button
        """
        App().player.play_album(self.__album)

    def _on_add_button_clicked(self, button):
        """
            Add/Remove album
           @param button as Gtk.Button
        """
        (icon_name, icon_size) = button.get_image().get_icon_name()
        if icon_name == "list-add-symbolic":
            App().player.add_album(self.__album)
            App().player.update_next_prev()
            button.get_image().set_from_icon_name("list-remove-symbolic",
                                                  icon_size)
        else:
            App().player.remove_album_by_id(self.__album.id)
            App().player.update_next_prev()
            button.get_image().set_from_icon_name("list-add-symbolic",
                                                  icon_size)

    def _on_album_artwork_changed(self, art, album_id):
        """
            Update cover for album_id
            @param art as Art
            @param album_id as int
        """
        if album_id == self.__album.id:
            App().art_helper.set_album_artwork(
                            self.__album,
                            # +100 to prevent resize lag
                            self.get_allocated_width() + 100,
                            self.height,
                            self._artwork.get_scale_factor(),
                            ArtBehaviour.BLUR_HARD |
                            ArtBehaviour.DARKER,
                            self.__on_album_artwork)

    def _on_playback_changed(self, player):
        """
            Update add button
            @param player as Player
        """
        (icon_name, icon_size) = self.__add_button.get_image().get_icon_name()
        icon_name = self.__get_add_button_icon_name()
        self.__add_button.get_image().set_from_icon_name(icon_name, icon_size)

    def _on_year_press(self, x, y, event):
        """
            Show years view
            @param x as int
            @param y as int
            @param event as Gdk.EventButton
        """
        App().window.container.show_view([Type.YEARS], [self.__album.year])

#######################
# PRIVATE             #
#######################
    def __get_add_button_icon_name(self):
        """
            Get add button icon name
            @return str
        """
        if self.__album.id in App().player.album_ids:
            return "list-remove-symbolic"
        else:
            return "list-add-symbolic"

    def __set_text_height(self, collapsed):
        """
            Set text height
            @param collapsed as bool
        """
        title_context = self.__title_label.get_style_context()
        info_context = self.__info_label.get_style_context()
        for c in title_context.list_classes():
            title_context.remove_class(c)
        for c in info_context.list_classes():
            info_context.remove_class(c)
        if collapsed:
            self.__title_label.get_style_context().add_class(
                "text-large")
        elif self._view_type & (ViewType.MEDIUM | ViewType.SMALL):
            self.__title_label.get_style_context().add_class(
                "text-x-large")
            self.__info_label.get_style_context().add_class(
                "text-medium")
        else:
            self.__title_label.get_style_context().add_class(
                "text-xx-large")
            self.__info_label.get_style_context().add_class(
                "text-x-large")

    def __on_album_artwork(self, surface):
        """
            Set album artwork
            @param surface as str
        """
        if surface is not None:
            self._artwork.set_from_surface(surface)
