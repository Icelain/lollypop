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

from lollypop.define import App, Size, AdaptiveSize
from lollypop.toolbar_playback import ToolbarPlayback
from lollypop.toolbar_info import ToolbarInfo
from lollypop.toolbar_title import ToolbarTitle
from lollypop.toolbar_end import ToolbarEnd
from lollypop.helper_size_allocation import SizeAllocationHelper
from lollypop.helper_signals import SignalsHelper, signals


class Toolbar(Gtk.HeaderBar, SizeAllocationHelper, SignalsHelper):
    """
        Lollypop toolbar
    """

    @signals
    def __init__(self, window):
        """
            Init toolbar
            @param window as Window
        """
        Gtk.HeaderBar.__init__(self)
        SizeAllocationHelper.__init__(self)
        self.__width = Size.MINI
        self.__adaptive_size = AdaptiveSize.SMALL
        self.set_title("Lollypop")
        self.__toolbar_playback = ToolbarPlayback(window)
        self.__toolbar_playback.show()
        self.__toolbar_info = ToolbarInfo()
        self.__toolbar_title = ToolbarTitle()
        self.__toolbar_end = ToolbarEnd(window)
        self.__toolbar_end.show()
        self.pack_start(self.__toolbar_playback)
        self.pack_start(self.__toolbar_info)
        self.set_custom_title(self.__toolbar_title)
        self.pack_end(self.__toolbar_end)
        self.connect("realize", self.__on_realize)
        return [
            (App().player, "status-changed", "_on_status_changed"),
            (App().window, "adaptive-size-changed",
             "_on_adaptive_size_changed")
        ]

    def do_get_preferred_width(self):
        """
            Allow window resize
            @return (int, int)
        """
        width = max(Size.SMALL, self.__width)
        return (Size.SMALL, width)

    def set_mini(self, mini):
        """
            Set toolbar working when small
            @param mini as bool
        """
        self.__toolbar_playback.set_mini(mini)
        if mini:
            self.__toolbar_title.hide()
            self.__toolbar_info.hide()
        elif App().player.is_playing:
            self.__toolbar_title.show()
            self.__toolbar_info.show()

    @property
    def end(self):
        """
            Return end toolbar
            @return ToolbarEnd
        """
        return self.__toolbar_end

    @property
    def info(self):
        """
            Return info toolbar
            @return ToolbarInfo
        """
        return self.__toolbar_info

    @property
    def title(self):
        """
            Return title toolbar
            @return ToolbarTitle
        """
        return self.__toolbar_title

    @property
    def playback(self):
        """
            Return playback toolbar
            @return ToolbarPlayback
        """
        return self.__toolbar_playback

#######################
# PROTECTED           #
#######################
    def _handle_size_allocate(self, allocation):
        """
            Update artwork
            @param allocation as Gtk.Allocation
        """
        if SizeAllocationHelper._handle_size_allocate(self, allocation):
            width = self.__toolbar_playback.get_preferred_width()[1]
            width += self.__toolbar_end.get_preferred_width()[1]
            available = allocation.width - width
            title_width = available / 2.5
            self.__toolbar_title.set_width(title_width)
            self.__toolbar_info.set_width((available - title_width) / 2)

    def _on_status_changed(self, player):
        """
            Update buttons and progress bar
            @param player as Player
        """
        if player.is_playing and self.__adaptive_size & AdaptiveSize.BIG:
            self.__toolbar_title.show()
            self.__toolbar_info.show()
        else:
            self.__toolbar_title.hide()
            self.__toolbar_info.hide()

    def _on_adaptive_size_changed(self, window, adaptive_size):
        """
            Update internal widgets
            @param window as Gtk.Window
            @param adaptive_size as AdaptiveSize
        """
        self.__adaptive_size = adaptive_size
        if adaptive_size & AdaptiveSize.BIG and App().player.is_playing:
            self.__toolbar_title.show()
            self.__toolbar_info.show()

############
# PRIVATE  #
############
    def __on_realize(self, toolbar):
        """
            Calculate art size
            @param toolbar as ToolbarInfos
        """
        art_size = self.get_allocated_height()
        self.__toolbar_info.artwork.set_art_size(art_size, art_size)
