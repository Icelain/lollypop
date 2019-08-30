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

from gi.repository import Gtk, GLib, Gdk


from lollypop.utils import set_cursor_type, popup_widget
from lollypop.objects_radio import Radio
from lollypop.widgets_player_artwork import ArtworkPlayerWidget
from lollypop.widgets_player_label import LabelPlayerWidget
from lollypop.define import App, ArtBehaviour, StorageType, MARGIN
from lollypop.helper_gestures import GesturesHelper
from lollypop.helper_signals import SignalsHelper, signals


class ToolbarInfo(Gtk.Bin, ArtworkPlayerWidget,
                  SignalsHelper, GesturesHelper):
    """
        Informations toolbar
    """

    @signals
    def __init__(self):
        """
            Init toolbar
        """
        Gtk.Bin.__init__(self)
        self.__width = 0
        horizontal_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 15)
        horizontal_box.show()
        self.__eventbox = Gtk.EventBox.new()
        self.__eventbox.add(horizontal_box)
        self.__eventbox.set_property("halign", Gtk.Align.START)
        self.__eventbox.show()
        self.add(self.__eventbox)
        GesturesHelper.__init__(self, self.__eventbox)
        self.special_headerbar_hack()

        self.__label = LabelPlayerWidget()
        self.__label.show()
        self.__artwork = ArtworkPlayerWidget(ArtBehaviour.CROP_SQUARE |
                                             ArtBehaviour.CACHE)
        self.__artwork.show()
        self.__artwork.set_property("has-tooltip", True)
        horizontal_box.pack_start(self.__artwork, False, False, 0)
        horizontal_box.pack_start(self.__label, False, False, 0)
        self.connect("realize", self.__on_realize)
        self.get_style_context().add_class("opacity-transition")
        return [
            (App().player, "status-changed", "_on_status_changed")
        ]

    def do_get_preferred_width(self):
        """
            We force preferred width
            @return (int, int)
        """
        return (self.__width, self.__width)

    def get_preferred_height(self):
        """
            Return preferred height
            @return (int, int)
        """
        return self.__labels.get_preferred_height()

    def set_width(self, width):
        """
            Set widget width
            @param width as int
        """
        self.__width = width
        self.set_property("width-request", width)

    def set_mini(self, mini):
        """
            Show/hide
            @param mini as bool
        """
        if mini:
            self.hide()
        else:
            self.show()

    @property
    def art_size(self):
        """
            Get art size
            return int
        """
        return self.__art_size

#######################
# PROTECTED           #
#######################
    def _on_status_changed(self, player):
        """
            Show/hide eventbox
        """
        if player.is_playing:
            set_cursor_type(self.__eventbox)
            self.set_state_flags(Gtk.StateFlags.VISITED, False)
        else:
            set_cursor_type(self.__eventbox, Gdk.CursorType.LEFT_PTR)
            self.unset_state_flags(Gtk.StateFlags.VISITED)

    def _on_primary_long_press_gesture(self, x, y):
        """
            Show menu
            @param x as int
            @param y as int
        """
        if App().window.is_adaptive or not self.__artwork.get_visible():
            return
        if isinstance(App().player.current_track, Radio):
            return
        if App().player.current_track.id is not None:
            self.__popup_menu()

    def _on_primary_press_gesture(self, x, y, event):
        """
            Show information popover
            @param x as int
            @param y as int
            @param evnet as Gdk.Event
        """
        if App().window.is_adaptive or not self.__artwork.get_visible():
            return
        if isinstance(App().player.current_track, Radio):
            from lollypop.pop_tunein import TuneinPopover
            popover = TuneinPopover()
            popover.populate()
        elif App().player.current_track.id is not None:
            from lollypop.pop_information import InformationPopover
            popover = InformationPopover()
            popover.populate()
        popover.set_relative_to(self.__eventbox)
        popover.popup()

    def _on_secondary_press_gesture(self, x, y, event):
        """
            Show menu
            @param x as int
            @param y as int
        """
        self._on_primary_long_press_gesture(x, y)

#######################
# PRIVATE             #
#######################
    def __update_cover(self, art, album_id):
        """
            Update cover for album_id
            @param art as Art
            @param album_id as int
        """
        if App().player.current_track.album.id == album_id:
            self._previous_artwork_id = None
            self.update_artwork(self.__art_size, self.__art_size)

    def __update_logo(self, art, name):
        """
            Update logo for name
            @param art as Art
            @param name as str
        """
        if App().player.current_track.album_artist == name:
            pixbuf = App().art.get_radio_artwork(
                name, self.__art_size, self.__art_size)
            self.__artwork.set_from_surface(pixbuf)

    def __popup_menu(self):
        """
            Show contextual menu
        """
        if App().window.is_adaptive or not self.__artwork.get_visible():
            return
        track = App().player.current_track
        if track.id >= 0:
            from lollypop.menu_objects import MinTrackMenu, TrackMenuExt
            from lollypop.widgets_menu import MenuBuilder
            menu = MinTrackMenu(track)
            menu_widget = MenuBuilder(menu)
            menu_widget.show()
            if not track.storage_type & StorageType.EPHEMERAL:
                menu_ext = TrackMenuExt(track)
                menu_ext.show()
                menu_widget.get_child_by_name("main").add(menu_ext)
            self.set_state_flags(Gtk.StateFlags.FOCUSED, False)
            popup_widget(menu_widget, self.__eventbox)

    def __on_realize(self, toolbar):
        """
            Calculate art size
            @param toolbar as ToolbarInfos
        """
        self.set_margin_start(MARGIN)
        art_size = self.get_allocated_height()
        self.__artwork.set_art_size(art_size, art_size)

    def __on_query_tooltip(self, widget, x, y, keyboard, tooltip):
        """
            Show tooltip if needed
            @param widget as Gtk.Widget
            @param x as int
            @param y as int
            @param keyboard as bool
            @param tooltip as Gtk.Tooltip
        """
        layout_title = self._title_label.get_layout()
        layout_artist = self._artist_label.get_layout()
        if layout_title.is_ellipsized() or layout_artist.is_ellipsized():
            artist = GLib.markup_escape_text(self._artist_label.get_text())
            title = GLib.markup_escape_text(self._title_label.get_text())
            tooltip.set_markup("<b>%s</b> - %s" % (artist, title))
        else:
            return False
        return True
