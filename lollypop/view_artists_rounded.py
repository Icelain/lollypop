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

from gi.repository import Gtk, Pango

from gettext import gettext as _

from lollypop.view_flowbox import FlowBoxView
from lollypop.define import App, Type, ViewType, MARGIN
from locale import strcoll
from lollypop.helper_horizontal_scrolling import HorizontalScrollingHelper
from lollypop.widgets_artist_rounded import RoundedArtistWidget
from lollypop.utils import get_icon_name, get_font_height
from lollypop.helper_signals import SignalsHelper, signals


class RoundedArtistsView(FlowBoxView, SignalsHelper):
    """
        Show artists in a FlowBox
    """

    @signals
    def __init__(self, view_type):
        """
            Init artist view
            @param view_type as ViewType
        """
        FlowBoxView.__init__(self, view_type)
        self._widget_class = RoundedArtistWidget
        self.connect("destroy", self.__on_destroy)
        self._empty_icon_name = get_icon_name(Type.ARTISTS)
        return [
            (App().art, "artist-artwork-changed",
             "_on_artist_artwork_changed"),
            (App().scanner, "artist-updated", "_on_artist_updated")
        ]

    def populate(self):
        """
            Populate view
        """
        def on_load(items):
            FlowBoxView.populate(self, items)

        def load():
            if App().settings.get_value("show-performers"):
                ids = App().artists.get_all()
            else:
                ids = App().artists.get()
            return ids

        App().task_helper.run(load, callback=(on_load,))

    def add_value(self, item):
        """
            Insert item
            @param item as (int, str, str)
        """
        for child in self._box.get_children():
            if child.data == item[0]:
                return
        # Setup sort on insert
        self._box.set_sort_func(self.__sort_func)
        widget = RoundedArtistWidget(item, self._view_type, self.font_height)
        widget.populate()
        widget.show()
        self._box.insert(widget, -1)

    def remove_value(self, item_id):
        """
            Remove value
            @param item_id as int
        """
        for child in self._box.get_children():
            if child.data == item_id:
                child.destroy()
                break

    @property
    def args(self):
        """
            Get default args for __class__, populate() plus sidebar_id and
            scrolled position
            @return ({}, int, int)
        """
        if self._view_type & ViewType.SCROLLED:
            position = self._scrolled.get_vadjustment().get_value()
        else:
            position = 0
        view_type = self._view_type & ~self.view_sizing_mask
        return ({"view_type": view_type}, self.sidebar_id, position)

#######################
# PROTECTED           #
#######################
    def _add_items(self, items, *args):
        """
            Add artists to the view
            @param items as [(int, str, str)]
        """
        FlowBoxView._add_items(self, items, self._view_type)

    def _on_child_activated(self, flowbox, child):
        """
            Enter child
            @param flowbox as Gtk.FlowBox
            @param child as Gtk.FlowBoxChild
        """
        App().window.container.show_view([Type.ARTISTS], [child.data])

    def _on_artist_artwork_changed(self, art, prefix):
        """
            Update artwork if needed
            @param art as Art
            @param prefix as str
        """
        for child in self._box.get_children():
            if child.name == prefix:
                child.set_artwork()

    def _on_artist_updated(self, scanner, artist_id, add):
        """
            Add/remove artist to/from list
            @param scanner as CollectionScanner
            @param artist_id as int
            @param add as bool
        """
        if add:
            artist_ids = App().artists.get_ids()
            position = artist_ids.index(artist_id)
            artist_name = App().artists.get_name(artist_id)
            sortname = App().artists.get_sortname(artist_id)
            widget = RoundedArtistWidget((artist_id, artist_name, sortname),
                                         self._view_type,
                                         get_font_height())
            self._box.insert(widget, position)
            widget.show()
            widget.populate()
        else:
            for child in self._box.get_children():
                if child.data == artist_id:
                    child.destroy()
                    break

#######################
# PRIVATE             #
#######################
    def __sort_func(self, widget1, widget2):
        """
            Sort function
            @param widget1 as RoundedArtistWidget
            @param widget2 as RoundedArtistWidget
        """
        return strcoll(widget1.sortname, widget2.sortname)

    def __on_destroy(self, widget):
        """
            Stop loading
            @param widget as Gtk.Widget
        """
        RoundedArtistsView.stop(self)


class RoundedArtistsRandomView(RoundedArtistsView, HorizontalScrollingHelper):
    """
        Show 6 random artists in a FlowBox
    """

    def __init__(self, view_type):
        """
            Init artist view
            @param view_type as ViewType
        """
        RoundedArtistsView.__init__(self, view_type)
        self.insert_row(0)
        self.set_row_spacing(5)
        self._label = Gtk.Label.new()
        self._label.set_ellipsize(Pango.EllipsizeMode.END)
        self._label.get_style_context().add_class("dim-label")
        self.__update_label(App().window.is_adaptive)
        self._label.set_hexpand(True)
        self._label.set_property("halign", Gtk.Align.START)
        self._backward_button = Gtk.Button.new_from_icon_name(
                                                    "go-previous-symbolic",
                                                    Gtk.IconSize.BUTTON)
        self._forward_button = Gtk.Button.new_from_icon_name(
                                                   "go-next-symbolic",
                                                   Gtk.IconSize.BUTTON)
        self._backward_button.get_style_context().add_class("menu-button-48")
        self._forward_button.get_style_context().add_class("menu-button-48")
        header = Gtk.Grid()
        header.set_column_spacing(10)
        header.add(self._label)
        header.add(self._backward_button)
        header.add(self._forward_button)
        header.set_margin_end(MARGIN)
        header.show_all()
        HorizontalScrollingHelper.__init__(self)
        self.attach(header, 0, 0, 1, 1)
        self._label.set_property("halign", Gtk.Align.START)
        self._box.set_property("halign", Gtk.Align.CENTER)

    def populate(self):
        """
            Populate view
        """
        def on_load(items):
            self._box.set_min_children_per_line(len(items))
            FlowBoxView.populate(self, items)
            if items:
                self.show()

        def load():
            ids = App().artists.get_randoms(15)
            return ids

        self._label.set_text(_("Why not listen to?"))
        App().task_helper.run(load, callback=(on_load,))

    @property
    def args(self):
        return None

#######################
# PROTECTED           #
#######################
    def _on_adaptive_changed(self, window, status):
        """
            Update label
            @param window as Window
            @param status as bool
        """
        if RoundedArtistsView._on_adaptive_changed(self, window, status):
            self.__update_label(status)

    def _on_populated(self, widget, lazy_loading_id):
        """
            Update button state
            @param widget as Gtk.Widget
            @parma lazy_loading_id as int
        """
        RoundedArtistsView._on_populated(self, widget, lazy_loading_id)
        if self.is_populated:
            self._update_buttons()

    def _on_artist_updated(self, scanner, artist_id, add):
        pass

#######################
# PRIVATE             #
#######################
    def __update_label(self, is_adaptive):
        """
            Update label style based on current adaptive state
            @param is_adaptive as bool
        """
        style_context = self._label.get_style_context()
        if is_adaptive:
            style_context.remove_class("text-x-large")
        else:
            style_context.add_class("text-x-large")
