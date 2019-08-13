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

from gi.repository import Gtk, Pango, GLib

from gettext import gettext as _

from lollypop.define import App, ViewType, MARGIN_SMALL, IndicatorType
from lollypop.define import StorageType
from lollypop.widgets_indicator import IndicatorWidget
from lollypop.helper_gestures import GesturesHelper
from lollypop.utils import seconds_to_string, on_query_tooltip, popup_widget


class TrackRow(Gtk.ListBoxRow):
    """
        A track row
    """

    def get_best_height(widget):
        """
            Calculate widget height
            @param widget as Gtk.Widget
        """
        ctx = widget.get_pango_context()
        layout = Pango.Layout.new(ctx)
        layout.set_text("a", 1)
        font_height = int(layout.get_pixel_size()[1])
        # application.css
        min_height = 32
        if font_height > min_height:
            height = font_height
        else:
            height = min_height
        return height

    def __init__(self, track, album_artist_ids, view_type):
        """
            Init row widgets
            @param track as Track
            @param album_artist_ids as [int]
            @param view_type as ViewType
        """
        # We do not use Gtk.Builder for speed reasons
        Gtk.ListBoxRow.__init__(self)
        self._view_type = view_type
        self._artists_label = None
        self._track = track
        self._indicator = IndicatorWidget(self, view_type)
        self._indicator.show()
        self._grid = Gtk.Grid()
        self._grid.set_property("valign", Gtk.Align.CENTER)
        self._grid.set_column_spacing(5)
        self._grid.show()
        self._title_label = Gtk.Label.new(
            GLib.markup_escape_text(self._track.name))
        self._title_label.set_use_markup(True)
        self._title_label.set_property("has-tooltip", True)
        self._title_label.connect("query-tooltip", on_query_tooltip)
        self._title_label.set_property("hexpand", True)
        self._title_label.set_property("halign", Gtk.Align.START)
        self._title_label.set_property("xalign", 0)
        self._title_label.set_ellipsize(Pango.EllipsizeMode.END)
        self._title_label.show()
        featuring_artist_ids = track.get_featuring_artist_ids(album_artist_ids)
        if featuring_artist_ids:
            artists = []
            for artist_id in featuring_artist_ids:
                artists.append(App().artists.get_name(artist_id))
            self._artists_label = Gtk.Label.new(GLib.markup_escape_text(
                ", ".join(artists)))
            self._artists_label.set_use_markup(True)
            self._artists_label.set_property("has-tooltip", True)
            self._artists_label.connect("query-tooltip", on_query_tooltip)
            self._artists_label.set_property("hexpand", True)
            self._artists_label.set_property("halign", Gtk.Align.END)
            self._artists_label.set_ellipsize(Pango.EllipsizeMode.END)
            self._artists_label.set_opacity(0.3)
            self._artists_label.set_margin_end(5)
            self._artists_label.show()
        duration = seconds_to_string(self._track.duration)
        self._duration_label = Gtk.Label.new(duration)
        self._duration_label.get_style_context().add_class("dim-label")
        self._duration_label.show()
        self._num_label = Gtk.Label.new()
        self._num_label.set_ellipsize(Pango.EllipsizeMode.END)
        self._num_label.set_width_chars(4)
        self._num_label.get_style_context().add_class("dim-label")
        self._num_label.show()
        self.update_number_label()
        self._grid.add(self._indicator)
        self._grid.add(self._num_label)
        self._grid.add(self._title_label)
        if self._artists_label is not None:
            self._grid.add(self._artists_label)
        self._grid.add(self._duration_label)
        if self._view_type & (ViewType.PLAYBACK | ViewType.PLAYLISTS):
            self.__action_button = Gtk.Button.new_from_icon_name(
               "list-remove-symbolic",
               Gtk.IconSize.MENU)
            self.__action_button.set_tooltip_text(
               _("Remove from playlist"))
        elif not self._view_type & ViewType.SEARCH:
            self.__action_button = Gtk.Button.new_from_icon_name(
               "view-more-symbolic",
               Gtk.IconSize.MENU)
        else:
            self.__action_button = None
        if self.__action_button is not None:
            self.__action_button.show()
            self.__gesture_helper = GesturesHelper(
                self.__action_button,
                primary_press_callback=self._on_action_button_press)
            self.__action_button.set_margin_end(MARGIN_SMALL)
            self.__action_button.set_relief(Gtk.ReliefStyle.NONE)
            context = self.__action_button.get_style_context()
            context.add_class("menu-button")
            self._grid.add(self.__action_button)
        else:
            self._duration_label.set_margin_end(MARGIN_SMALL)
        self.add(self._grid)
        self.set_indicator(self._get_indicator_type())
        self.update_duration()
        self.get_style_context().add_class("trackrow")

    def update_duration(self):
        """
            Update track duration
        """
        self._track.reset("duration")
        duration = seconds_to_string(self._track.duration)
        self._duration_label.set_label(duration)

    def set_indicator(self, indicator_type=None):
        """
            Show indicator
            @param indicator_type as IndicatorType
        """
        if indicator_type is None:
            indicator_type = self._get_indicator_type()
        self._indicator.clear()
        if indicator_type & IndicatorType.LOADING:
            self._indicator.set_opacity(1)
            self._indicator.load()
        elif indicator_type & IndicatorType.PLAY:
            self._indicator.set_opacity(1)
            self.set_state_flags(Gtk.StateFlags.VISITED, True)
            if indicator_type & IndicatorType.LOVED:
                self._indicator.play_loved()
            else:
                self._indicator.play()
        else:
            self.unset_state_flags(Gtk.StateFlags.VISITED)
            if indicator_type & IndicatorType.LOVED:
                self._indicator.set_opacity(1)
                self._indicator.loved()
            elif indicator_type & IndicatorType.SKIP:
                self._indicator.set_opacity(1)
                self._indicator.skip()
            else:
                self._indicator.set_opacity(0)

    def update_number_label(self):
        """
            Update position label for row
        """
        if App().player.track_in_queue(self._track):
            self._num_label.get_style_context().add_class("queued")
            pos = App().player.get_track_position(self._track.id)
            self._num_label.set_text(str(pos))
        elif self._track.number > 0:
            self._num_label.get_style_context().remove_class("queued")
            self._num_label.set_text(str(self._track.number))
        else:
            self._num_label.get_style_context().remove_class("queued")
            self._num_label.set_text("")

    def set_position(self, position):
        """
            Update row position
            @param position as int
        """
        if App().settings.get_value("show-tag-tracknumber") and\
                not (self._view_type & ViewType.PLAYLISTS | ViewType.POPOVER):
            return
        self._track.set_number(position)
        self.update_number_label()

    def popup_menu(self, parent, x=None, y=None):
        """
            Popup menu for track
            @param parent as Gtk.Widget
            @param x as int
            @param y as int
        """
        def on_closed(popover):
            self.unset_state_flags(Gtk.StateFlags.FOCUSED)
            self.set_indicator()

        from lollypop.menu_objects import TrackMenu, TrackMenuExt
        from lollypop.widgets_menu import MenuBuilder
        menu = TrackMenu(self._track, App().window.is_adaptive)
        menu_widget = MenuBuilder(menu)
        main = menu_widget.get_child_by_name("main")
        menu_widget.show()
        if not self._track.storage_type & StorageType.EPHEMERAL:
            menu_ext = TrackMenuExt(self._track)
            menu_ext.show()
            main.add(menu_ext)
        self.set_state_flags(Gtk.StateFlags.FOCUSED, False)
        popover = popup_widget(menu_widget, parent, x, y)
        if popover is not None:
            popover.connect("closed", on_closed)

    @property
    def name(self):
        """
            Get row name
            @return str
        """
        return self._title_label.get_text()

    @property
    def track(self):
        """
            Get row track
            @return Track
        """
        return self._track

#######################
# PROTECTED           #
#######################
    def _get_indicator_type(self):
        """
            Get indicator type for current row
            @return IndicatorType
        """
        indicator_type = IndicatorType.NONE
        if App().player.current_track.id == self._track.id:
            indicator_type |= IndicatorType.PLAY
        if self._track.loved == 1:
            indicator_type |= IndicatorType.LOVED
        elif self._track.loved == -1:
            indicator_type |= IndicatorType.SKIP
        return indicator_type

    def _on_action_button_press(self, x, y, event):
        """
            Show row menu
            @param x as int
            @param y as int
            @param event as Gdk.EventButton
        """
        if not self.get_state_flags() & Gtk.StateFlags.PRELIGHT:
            return True
        if self._view_type & ViewType.PLAYBACK:
            self._track.album.remove_track(self._track)
            App().player.set_next()
            App().player.set_prev()
            self.destroy()
        elif self._view_type & ViewType.PLAYLISTS:
            from lollypop.view_playlists import PlaylistsView
            view = self.get_ancestor(PlaylistsView)
            if view is not None:
                view.remove_from_playlist(self._track)
            self.destroy()
        else:
            self.popup_menu(self.__action_button)

#######################
# PRIVATE             #
#######################
