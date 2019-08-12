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

from lollypop.define import App
from lollypop.helper_signals import SignalsHelper, signals


class ApplicationMenu(Gtk.Bin, SignalsHelper):
    """
        Configure defaults items
    """

    @signals
    def __init__(self):
        """
            Init popover
        """
        Gtk.Bin.__init__(self)
        builder = Gtk.Builder()
        builder.add_from_resource("/org/gnome/Lollypop/Appmenu.ui")
        widget = builder.get_object("widget")
        self.add(widget)
        self.__volume = builder.get_object("volume")
        self.__volume.set_value(App().player.volume)
        builder.connect_signals(self)
        if App().settings.get_value("background-mode"):
            builder.get_object("quit_button").show()
        return {
            "map": [
                (App().player, "volume-changed", "_on_volume_changed")
            ]
        }

#######################
# PROTECTED           #
#######################
    def _on_button_clicked(self, button):
        """
            Popdown popover if exists or destroy self
        """
        popover = self.get_ancestor(Gtk.Popover)
        if popover is not None:
            popover.popdown()

    def _on_volume_value_changed(self, scale):
        """
            Set volume
            @param scale as Gtk.Scale
        """
        new_volume = scale.get_value()
        if new_volume != App().player.volume:
            App().player.set_volume(scale.get_value())

    def _on_volume_changed(self, player):
        """
            Set scale value
            @param player as Player
        """
        volume = self.__volume.get_value()
        if player.volume != volume:
            self.__volume.set_value(player.volume)
