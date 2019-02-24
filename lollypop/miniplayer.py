# Copyright (c) 2014-2018 Cedric Bellegarde <cedric.bellegarde@adishatz.org>
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

from lollypop.helper_art import ArtHelperEffect
from lollypop.controller_information import InformationController
from lollypop.controller_progress import ProgressController
from lollypop.controller_playback import PlaybackController
from lollypop.widgets_cover import CoverWidget
from lollypop.utils import on_realize
from lollypop.define import App, ArtSize


class MiniPlayer(Gtk.Bin, InformationController,
                 ProgressController, PlaybackController):
    """
        Mini player shown in adaptive mode
    """
    __gsignals__ = {
        "revealed": (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
    }

    def __init__(self, width):
        """
            Init mini player
            @param width as int
        """
        self.__width = width
        self.__height = 0
        self.__cover_widget = None
        Gtk.Bin.__init__(self)
        InformationController.__init__(self, False, ArtHelperEffect.BLUR_HARD)
        ProgressController.__init__(self)
        PlaybackController.__init__(self)
        builder = Gtk.Builder()
        builder.add_from_resource("/org/gnome/Lollypop/MiniPlayer.ui")
        builder.connect_signals(self)

        self.__grid = builder.get_object("grid")
        self.__revealer = builder.get_object("revealer")
        self.__revealer_box = builder.get_object("revealer_box")
        self.__eventbox = builder.get_object("eventbox")
        self.__eventbox.connect("realize", on_realize)

        self._progress = builder.get_object("progress_scale")
        self._progress.set_sensitive(False)
        self._progress.set_hexpand(True)
        self._timelabel = builder.get_object("playback")
        self._total_time_label = builder.get_object("duration")

        self._artist_label = builder.get_object("artist_label")
        self._title_label = builder.get_object("title_label")

        self._prev_button = builder.get_object("previous_button")
        self._play_button = builder.get_object("play_button")
        self._next_button = builder.get_object("next_button")
        self.__back_button = builder.get_object("back_button")
        self._play_image = builder.get_object("play_image")
        self._pause_image = builder.get_object("pause_image")

        self.__grid = builder.get_object("grid")
        self._artwork = builder.get_object("cover")
        self.__signal_id1 = App().player.connect("current-changed",
                                                 self.__on_current_changed)
        self.__signal_id2 = App().player.connect("status-changed",
                                                 self.__on_status_changed)
        self.__signal_id3 = App().player.connect("lock-changed",
                                                 self.__on_lock_changed)
        self.__on_current_changed(App().player)
        if App().player.current_track.id is not None:
            PlaybackController.on_status_changed(self, App().player)
            self.update_position()
            ProgressController.on_status_changed(self, App().player)
        self.add(builder.get_object("widget"))
        self.connect("destroy", self.__on_destroy)

    def update_cover(self, width):
        """
            Update cover for width
            @param width as int
        """
        if self.__width == width:
            return
        self.__width = width
        InformationController.on_current_changed(self, width, None)

    def do_get_preferred_width(self):
        """
            Force preferred width
        """
        (min, nat) = Gtk.Bin.do_get_preferred_width(self)
        # Allow resizing
        return (0, 0)

    def do_get_preferred_height(self):
        """
            Force preferred height
        """
        return self.__grid.get_preferred_height()

#######################
# PROTECTED           #
#######################
    def _on_lyrics_button_clicked(self, button):
        """
            Show lyrics view
            @param button as Gtk.Button
        """
        self._on_reveal_button_release_event(None, None)
        App().window.container.show_lyrics()

    def _on_button_release_event(self, *ignore):
        """
            Set revealer on/off
            @param button as Gtk.Button
        """
        if self.__revealer.get_reveal_child():
            self.__revealer.set_reveal_child(False)
            self.emit("revealed", False)
            if self.__cover_widget is not None:
                self.__cover_widget.destroy()
                self.__cover_widget = None
        else:
            if self.__cover_widget is None:
                self.__cover_widget = CoverWidget(False, ArtSize.BIG)
                self.__cover_widget.update(App().player.current_track.album)
                self.__cover_widget.show()
                self.__revealer_box.pack_start(self.__cover_widget,
                                               True, True, 0)
            self.__revealer.set_reveal_child(True)
            self.emit("revealed", True)

#######################
# PRIVATE             #
#######################
    def __on_destroy(self, widget):
        """
            Handle widget cleanup
            @param widget as Gtk.Widget
        """
        ProgressController.do_destroy(self)
        App().player.disconnect(self.__signal_id1)
        App().player.disconnect(self.__signal_id2)
        App().player.disconnect(self.__signal_id3)

    def __on_current_changed(self, player):
        """
            Update controllers
            @param player as Player
        """
        if App().player.current_track.id is not None:
            self.show()
        InformationController.on_current_changed(self, self.__width, None)
        ProgressController.on_current_changed(self, player)
        PlaybackController.on_current_changed(self, player)
        if self.__cover_widget is not None:
            self.__cover_widget.update(App().player.current_track.album)

    def __on_status_changed(self, player):
        """
            Update controllers
            @param player as Player
        """
        ProgressController.on_status_changed(self, player)
        PlaybackController.on_status_changed(self, player)

    def __on_lock_changed(self, player):
        """
            Lock toolbar
            @param player as Player
        """
        self._prev_button.set_sensitive(not player.is_locked)
        self._next_button.set_sensitive(not player.is_locked)
