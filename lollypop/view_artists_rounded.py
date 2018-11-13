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

from gi.repository import GLib

from lollypop.view_flowbox import FlowBoxView
from lollypop.define import App, Type
from lollypop.widgets_artist_rounded import RoundedArtistWidget


class RoundedArtistsView(FlowBoxView):
    """
        Show artists in a FlowBox
    """

    def __init__(self):
        """
            Init decade view
        """
        FlowBoxView.__init__(self)
        self._widget_class = RoundedArtistWidget
        self.connect("realize", self.__on_realize)
        self.connect("unrealize", self.__on_unrealize)
        self.connect("destroy", self.__on_destroy)

    def stop(self):
        """
            We want this view to be populated anyway (no sidebar mode)
        """
        pass

#######################
# PROTECTED           #
#######################
    def _add_items(self, item_ids, *args):
        """
            Add artists to the view
            Start lazy loading
            @param item ids as [int]
        """
        for item_id in [Type.ALL, Type.USB_DISKS]:
            if item_id in item_ids:
                item_ids.remove(item_id)
        art_size = App().settings.get_value("cover-size").get_int32()
        FlowBoxView._add_items(self, item_ids, art_size)

    def _on_item_activated(self, flowbox, widget):
        """
            Show artist albums
            @param flowbox as Gtk.Flowbox
            @param widget as ArtistRoundedWidget
        """
        App().window.container.show_view(widget.data)

    def _on_map(self, widget):
        """
            Set active ids
        """
        App().settings.set_value("list-one-ids",
                                 GLib.Variant("ai", [Type.POPULARS]))
        App().settings.set_value("list-two-ids",
                                 GLib.Variant("ai", []))

#######################
# PRIVATE             #
#######################
    def __on_destroy(self, widget):
        """
            Stop loading
            @param widget as Gtk.Widget
        """
        RoundedArtistsView.stop(self)

    def __on_artist_artwork_changed(self, art, prefix):
        """
            Update artwork if needed
            @param art as Art
            @param prefix as str
        """
        for child in self._box.get_children():
            if child.artist_name == prefix:
                child.set_artwork()

    def __on_realize(self, widget):
        """
            Connect signals
            @param widget as Gtk.Widget
        """
        self.__art_signal_id = App().art.connect(
                                              "artist-artwork-changed",
                                              self.__on_artist_artwork_changed)

    def __on_unrealize(self, widget):
        """
            Connect signals
            @param widget as Gtk.Widget
        """
        if self.__art_signal_id is not None:
            App().art.disconnect(self.__art_signal_id)
