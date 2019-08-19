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

from gi.repository import Gtk

from lollypop.define import App, Type
from lollypop.helper_signals import SignalsHelper, signals


class AdaptiveContainer(SignalsHelper):
    """
        Manage adaptive mode
    """

    @signals
    def __init__(self):
        """
            Init container
        """
        self._stack.connect("history-changed", self.__on_history_changed)
        return {
            "init": [
                (App().window, "adaptive-changed", "_on_adaptive_changed"),
                (self._stack, "visible-child-changed",
                 "_on_visible_child_changed")
            ]
        }

    def go_back(self):
        """
            Go back in container stack
        """
        if self._stack.history.count > 0:
            self._stack.go_back()
        elif App().window.is_adaptive:
            visible_child = self._stack.get_visible_child()
            if visible_child == self.left_list or\
                    not self.left_list.get_visible():
                Gtk.Stack.set_visible_child(self._stack, self._sidebar)
            else:
                Gtk.Stack.set_visible_child(self._stack, self.left_list)
            if visible_child is not None:
                visible_child.destroy_later()
        self.emit("can-go-back-changed", self.can_go_back)

    def go_home(self):
        """
            Go back to first page
        """
        self._stack.history.reset()
        visible_child = self._stack.get_visible_child()
        Gtk.Stack.set_visible_child(self._stack, self._sidebar)
        if visible_child is not None:
            visible_child.destroy_later()
        self.emit("can-go-back-changed", False)

    @property
    def can_go_back(self):
        """
            True if can go back
            @return bool
        """
        if App().window.is_adaptive:
            return self._stack.get_visible_child() != self._sidebar
        else:
            return self._stack.history.count > 0

##############
# PROTECTED  #
##############
    def _on_adaptive_changed(self, window, status):
        """
            Update current layout
            @param window as Window
            @param status as bool
        """
        if status:
            self._main_widget.remove(self._sidebar)
            self._sidebar_two.remove(self.left_list)
            self._stack.add(self._sidebar)
            self._stack.add(self.left_list)
        else:
            self._stack.remove(self._sidebar)
            self._stack.remove(self.left_list)
            self._main_widget.attach(self._sidebar, 0, 0, 1, 1)
            self._sidebar_two.pack1(self.left_list, False, False)
        self.emit("can-go-back-changed", self.can_go_back)

    def _on_visible_child_changed(self, stack, sidebar_id):
        """
            Active sidebar selected id
            @param stack as ContainerStack
            @param sidebar_id as int
        """
        if sidebar_id not in [Type.GENRES_LIST, Type.ARTISTS_LIST]:
            self.left_list.hide()
        self._sidebar.select_ids([sidebar_id], False)

############
# PRIVATE  #
############
    def __on_history_changed(self, stack):
        """
            Emit can-go-back-changed if can go back
            @param stack as Gtk.Stack
        """
        if self.can_go_back:
            self.emit("can-go-back-changed", True)
