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

from lollypop.helper_art import ArtBehaviour
from lollypop.utils import set_cursor_hand2
from lollypop.define import App, ArtSize, MARGIN_SMALL
from lollypop.widgets_player_progress import ProgressPlayerWidget
from lollypop.widgets_player_buttons import ButtonsPlayerWidget
from lollypop.widgets_player_artwork import ArtworkPlayerWidget
from lollypop.widgets_player_label import LabelPlayerWidget
from lollypop.helper_size_allocation import SizeAllocationHelper
from lollypop.helper_signals import SignalsHelper, signals
from lollypop.helper_gestures import GesturesHelper


class MiniPlayer(Gtk.Overlay, SizeAllocationHelper, SignalsHelper):
    """
        Mini player shown in adaptive mode
    """
    __gsignals__ = {
        "revealed": (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
    }

    @signals
    def __init__(self):
        """
            Init mini player
        """
        Gtk.Overlay.__init__(self)
        SizeAllocationHelper.__init__(self)
        self.__size = 0
        self.__previous_artwork_id = None
        self.__per_track_cover = App().settings.get_value(
            "allow-per-track-cover")
        self.get_style_context().add_class("black")
        self.__box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        self.__box.show()
        self.__box.get_style_context().add_class("big-padding")
        self.__revealer = Gtk.Revealer.new()
        self.__revealer.show()
        revealer_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, MARGIN_SMALL)
        revealer_box.show()
        bottom_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, MARGIN_SMALL)
        bottom_box.show()
        self.__eventbox = Gtk.EventBox.new()
        self.__eventbox.show()
        self.__eventbox.connect("realize", set_cursor_hand2)
        self.__gesture = GesturesHelper(
                               self.__eventbox,
                               primary_press_callback=self.__on_eventbox_press)
        self.__progress_widget = ProgressPlayerWidget()
        self.__progress_widget.show()
        self.__progress_widget.set_vexpand(True)
        buttons_widget = ButtonsPlayerWidget(["menu-button",
                                              "black-transparent"])
        buttons_widget.show()
        buttons_widget.update()
        buttons_widget.set_size_request(200, -1)
        self.__artwork_widget = ArtworkPlayerWidget()
        self.__artwork_widget.show()
        self.__artwork_widget.set_vexpand(True)
        self.__artwork_widget.set_art_size(ArtSize.MINIPLAYER,
                                           ArtSize.MINIPLAYER)
        label_widget = LabelPlayerWidget()
        label_widget.show()
        label_widget.set_property("halign", Gtk.Align.START)
        label_widget.update()
        self.__background = Gtk.Image()
        self.__background.show()
        # Assemble UI
        self.__eventbox.add(label_widget)
        self.__box.pack_start(self.__revealer, False, True, 0)
        self.__box.pack_start(bottom_box, False, False, 0)
        bottom_box.pack_start(self.__eventbox, True, True, 0)
        bottom_box.pack_end(buttons_widget, False, False, 0)
        self.__revealer.add(revealer_box)
        revealer_box.pack_start(self.__artwork_widget, False, True, 0)
        revealer_box.pack_start(self.__progress_widget, False, True, 0)
        self.add(self.__background)
        self.add_overlay(self.__box)
        return [
            (App().player, "current-changed", "_on_current_changed")
        ]

    def do_get_preferred_width(self):
        """
            Force preferred width
        """
        (min, nat) = Gtk.Bin.do_get_preferred_width(self)
        # Allow resizing
        return (0, nat)

    def do_get_preferred_height(self):
        """
            Force preferred height
        """
        (min, nat) = self.__box.get_preferred_height()
        return (min, min)

#######################
# PROTECTED           #
#######################
    def _on_current_changed(self, player):
        """
            Update artwork and labels
            @param player as Player
        """
        if self.__size == 0:
            return
        same_artwork = self.__previous_artwork_id ==\
            App().player.current_track.album.id and not self.__per_track_cover
        if same_artwork:
            return
        self.__previous_artwork_id = App().player.current_track.album.id
        self.__artwork_widget.set_artwork(
                self.__size, self.__size, self.__on_artwork,
                ArtBehaviour.BLUR_HARD | ArtBehaviour.DARKER)

#######################
# PRIVATE             #
#######################
    def _handle_size_allocate(self, allocation):
        """
            Handle artwork sizing
            @param allocation as Gtk.Allocation
        """
        if SizeAllocationHelper._handle_size_allocate(self, allocation):
            # We use parent height because we may be collapsed
            parent = self.get_parent()
            if parent is None:
                height = allocation.height
            else:
                height = parent.get_allocated_height()
            new_size = max(allocation.width, height)
            if new_size == 1 or self.__size == new_size:
                return
            self.__size = new_size
            self.__artwork_widget.set_artwork(
                new_size, new_size, self.__on_artwork,
                ArtBehaviour.BLUR_HARD | ArtBehaviour.DARKER)

    def __on_eventbox_press(self,  x, y, event):
        """
            Set revealer on/off
            @param button as Gtk.Button
            @param x as int
            @param y as int
            @param event as Gdk.Event
        """
        if self.__revealer.get_reveal_child():
            self.__revealer.set_reveal_child(False)
            self.emit("revealed", False)
        else:
            self.__revealer.set_reveal_child(True)
            self.emit("revealed", True)
            self.__progress_widget.update()
            self.__artwork_widget.update()

    def __on_artwork(self, surface):
        """
            Set artwork
            @param surface as str
        """
        if surface is None:
            pass
        else:
            self.__background.set_from_surface(surface)
