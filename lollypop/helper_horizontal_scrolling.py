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

from lollypop.define import ArtSize


class HorizontalScrollingHelper:
    """
        Manage 2 button and scroll a scrolled window
    """

    def __init__(self):
        """
            Init helper
        """
        self.__adjustment = self._scrolled.get_hadjustment()
        self._backward_button.connect("clicked",
                                      self.__on_backward_button_clicked)
        self._forward_button.connect("clicked",
                                     self.__on_forward_button_clicked)
        self._scrolled.get_hscrollbar().hide()
        self._scrolled.set_policy(Gtk.PolicyType.AUTOMATIC,
                                  Gtk.PolicyType.NEVER)

#######################
# PROTECTED             #
#######################
    def _update_buttons(self):
        """
            Update buttons state
        """
        value = self._scrolled.get_allocated_width()
        self._backward_button.set_sensitive(self.__adjustment.get_value() !=
                                            self.__adjustment.get_lower())
        self._forward_button.set_sensitive(self.__adjustment.get_value() <=
                                           self.__adjustment.get_upper() -
                                           value)

#######################
# PRIVATE             #
#######################
    def __smooth_scrolling(self, value, direction):
        """
            Emulate smooth scrolling
        """
        if value > 0:
            value -= 1
            current = self.__adjustment.get_value()
            if direction == Gtk.DirectionType.LEFT:
                self.__adjustment.set_value(current - 1)
            else:
                self.__adjustment.set_value(current + 1)
            if value % 10:
                GLib.idle_add(self.__smooth_scrolling, value, direction)
            else:
                GLib.timeout_add(1, self.__smooth_scrolling, value, direction)
        else:
            self._update_buttons()

    def __on_backward_button_clicked(self, backward_button):
        """
            Scroll left
            @param backward_button as Gtk.Button
        """
        backward_button.set_sensitive(False)
        value = self._scrolled.get_allocated_width() - ArtSize.BIG / 2
        self.__smooth_scrolling(value, Gtk.DirectionType.LEFT)

    def __on_forward_button_clicked(self, forward_button):
        """
            Scroll right
            @param forward_button as Gtk.Button
        """
        forward_button.set_sensitive(False)
        value = self._scrolled.get_allocated_width() - ArtSize.BIG / 2
        self.__smooth_scrolling(value, Gtk.DirectionType.RIGHT)
