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

from lollypop.define import App
# For lint
App()


class SignalsHelper():
    """
        Helper for autoconnect/disconnect signals on map
    """

    signals = {}

    def __init__(self):
        """
            Init helper
        """
        self.__connected = []
        self.connect("map", self.__on_map)
        self.connect("unmap", self.__on_unmap)

#######################
# PRIVATE             #
#######################
    def __on_map(self, widget):
        """
            Connect signals
            @param widget as Gtk.Widget
        """
        for (obj, signal, callback_str) in self.signals:
            name = "%s_%s" % (obj, signal)
            if name in self.__connected:
                continue
            if isinstance(obj, str):
                obj = eval(obj)
            callback = getattr(self, callback_str)
            obj.connect(signal, callback)
            self.__connected.append(name)

    def __on_unmap(self, widget):
        """
            Disconnect signals
            @param widget as Gtk.Widget
        """
        for (obj, signal, callback_str) in self.signals:
            name = "%s_%s" % (obj, signal)
            if name not in self.__connected:
                continue
            if isinstance(obj, str):
                obj = eval(obj)
            callback = getattr(self, callback_str)
            obj.disconnect_by_func(callback)
            self.__connected.remove(name)
