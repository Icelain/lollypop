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

from gi.repository import Gtk, Gdk

from lollypop.define import App, MARGIN_SMALL
from lollypop.helper_signals import SignalsHelper, signals


class TypeAheadWidget(Gtk.Revealer, SignalsHelper):
    """
        Type ahead widget
    """
    @signals
    def __init__(self):
        """
            Init widget
        """
        Gtk.Revealer.__init__(self)
        self.__current_focused_view = None
        self.__focus_in_event_id = None
        builder = Gtk.Builder()
        builder.add_from_resource("/org/gnome/Lollypop/TypeAhead.ui")
        builder.connect_signals(self)
        widget = builder.get_object("widget")
        widget.set_margin_top(MARGIN_SMALL)
        widget.set_margin_bottom(2)
        self.__entry = builder.get_object("entry")
        self.__next_button = builder.get_object("next_button")
        self.__prev_button = builder.get_object("prev_button")
        self.__next_button.connect("clicked", lambda x: self.__search_next())
        self.__prev_button.connect("clicked", lambda x: self.__search_prev())
        self.__entry.connect("map", self.__on_map)
        self.add(widget)
        return {
            "map": [
                ("App().window.container.list_view", "button-press-event",
                 "_on_list_key_press_event")
            ]
        }

    @property
    def entry(self):
        """
            Get popover entry
            @return Gtk.Entry
        """
        return self.__entry

#######################
# PROTECTED           #
#######################
    def _on_type_ahead_changed(self, entry):
        """
            Filter current widget
            @param entry as Gtk.entry
        """
        widget = self.__get_widget()
        if widget is not None:
            widget.search_for_child(entry.get_text())

    def _on_type_ahead_activate(self, entry):
        """
            Activate row
            @param entry as Gtk.Entry
        """
        widget = self.__get_widget()
        if widget is not None:
            widget.activate_child()
            self.__entry.set_text("")
            self.__entry.grab_focus()
            self.__current_focused_view = None

    def _on_entry_key_press_event(self, entry, event):
        """
            Handle special keys
            @param entry as Gtk.Entry
            @param Event as Gdk.EventKey
        """
        if event.keyval == Gdk.KEY_Up or event.keyval == Gdk.KEY_Down:
            return True
        elif event.keyval == Gdk.KEY_Escape:
            App().window.container.show_filter()

    def _on_entry_key_release_event(self, entry, event):
        """
            Handle special keys
            @param entry as Gtk.Entry
            @param Event as Gdk.EventKey
        """
        if event.keyval == Gdk.KEY_Up:
            self.__search_prev()
        elif event.keyval == Gdk.KEY_Down:
            self.__search_next()

    def _on_list_key_press_event(self, selection_list, event):
        """
            Force focus on list
            @param selection_list as SelectionList
            @param event as Gdk.Event
        """
        self.__current_focused_view = selection_list

#######################
# PRIVATE             #
#######################
    def __search_prev(self):
        """
            Search previous item
        """
        widget = self.__get_widget()
        if widget is not None:
            widget.search_prev(self.__entry.get_text())

    def __search_next(self):
        """
            Search next item
        """
        widget = self.__get_widget()
        if widget is not None:
            widget.search_next(self.__entry.get_text())

    def __get_widget(self):
        """
            Get widget for activated button
            @return Gtk.Widget
        """
        if App().window.is_adaptive:
            return App().window.container.stack
        else:
            if self.__current_focused_view is not None:
                return self.__current_focused_view
            else:
                return App().window.container.stack

    def __on_map(self, widget):
        """
            Connect signals
            @param widget as Gtk.Widget
        """
        if App().window.container.list_view.get_visible():
            self.__current_focused_view = App().window.container.list_view
