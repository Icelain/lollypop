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

from gi.repository import Gtk, Gdk, GLib, GObject, Pango

from locale import strcoll

from lollypop.view import LazyLoadingView
from lollypop.helper_filtering import FilteringHelper
from lollypop.helper_gestures import GesturesHelper
from lollypop.fastscroll import FastScroll
from lollypop.define import Type, App, ArtSize, SelectionListMask
from lollypop.define import ArtBehaviour, ViewType
from lollypop.logger import Logger
from lollypop.utils import get_icon_name, on_query_tooltip
from lollypop.shown import ShownPlaylists


class SelectionListRow(Gtk.ListBoxRow):
    """
        A selection list row
    """

    __gsignals__ = {
        "populated": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def get_best_height(widget):
        """
            Calculate widget height
            @param widget as Gtk.Widget
        """
        ctx = widget.get_pango_context()
        layout = Pango.Layout.new(ctx)
        layout.set_text("a", 1)
        font_height = int(layout.get_pixel_size()[1])
        return font_height

    def __init__(self, rowid, name, sortname, mask, height):
        """
            Init row
            @param rowid as int
            @param name as str
            @param sortname as str
            @param mask as SelectionListMask
            @param height as str
        """
        Gtk.ListBoxRow.__init__(self)
        self.__artwork = None
        self.__rowid = rowid
        self.__name = name
        self.__sortname = sortname
        self.__mask = mask
        self.set_style(height)

    def populate(self):
        """
            Populate widget
        """
        if self.__rowid == Type.SEPARATOR:
            separator = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
            separator.show()
            self.add(separator)
            self.set_sensitive(False)
            self.emit("populated")
        else:
            self.__grid = Gtk.Grid()
            self.__grid.set_column_spacing(7)
            self.__grid.show()
            self.__artwork = Gtk.Image.new()
            self.__grid.add(self.__artwork)
            self.__label = Gtk.Label.new()
            self.__label.set_ellipsize(Pango.EllipsizeMode.END)
            self.__label.set_markup(GLib.markup_escape_text(self.__name))
            self.__label.set_property("has-tooltip", True)
            self.__label.connect("query-tooltip", on_query_tooltip)
            self.__grid.add(self.__label)
            if self.__mask & SelectionListMask.ARTISTS:
                self.__grid.set_margin_end(20)
            self.add(self.__grid)
            self.set_artwork()
            self.show_label()

    def set_label(self, string):
        """
            Set label for row
            @param string as str
        """
        self.__name = string
        if not self.__mask & SelectionListMask.SIDEBAR:
            self.__label.set_markup(GLib.markup_escape_text(string))

    def set_artwork(self):
        """
            set_artwork widget
        """
        if self.__rowid == Type.SEPARATOR:
            pass
        elif self.__mask & SelectionListMask.ARTISTS and\
                self.__rowid >= 0 and\
                App().settings.get_value("artist-artwork"):
            App().art_helper.set_artist_artwork(
                                    self.__name,
                                    ArtSize.SMALL,
                                    ArtSize.SMALL,
                                    self.get_scale_factor(),
                                    ArtBehaviour.ROUNDED |
                                    ArtBehaviour.CROP_SQUARE |
                                    ArtBehaviour.CACHE,
                                    self.__on_artist_artwork)
            self.__artwork.show()
        elif self.__rowid < 0:
            icon_name = get_icon_name(self.__rowid, self.__mask)
            self.__artwork.set_from_icon_name(icon_name,
                                              Gtk.IconSize.BUTTON)
            self.__artwork.show()
            self.emit("populated")
        else:
            self.__artwork.hide()
            self.emit("populated")

    def show_label(self, mask=None):
        """
            Show label
            @param mask as SelectionListMask
        """
        # Do nothing if widget not populated
        if self.__artwork is None:
            self.__mask = mask
            return
        # Do not update widget if mask does not changed
        elif mask == self.__mask:
            return
        # If no mask, use current one
        elif mask is None:
            mask = self.__mask
        # Else use new mask
        else:
            self.__mask = mask

        if mask & (SelectionListMask.LABEL |
                   SelectionListMask.ARTISTS |
                   SelectionListMask.GENRES):
            self.__artwork.set_property("halign", Gtk.Align.FILL)
            self.__artwork.set_hexpand(False)
            self.__label.show()
            self.set_tooltip_text("")
            self.set_has_tooltip(False)
        else:
            self.__artwork.set_property("halign", Gtk.Align.CENTER)
            self.__artwork.set_hexpand(True)
            self.__label.hide()
            self.set_tooltip_text(self.__label.get_text())
            self.set_has_tooltip(True)

    def set_style(self, height):
        """
            Set internal sizing
        """
        if self.__rowid == Type.SEPARATOR:
            height = -1
            self.set_sensitive(False)
        elif self.__mask & SelectionListMask.ARTISTS and\
                self.__rowid >= 0 and\
                App().settings.get_value("artist-artwork"):
            self.get_style_context().add_class("row")
            if height < ArtSize.SMALL:
                height = ArtSize.SMALL
            # Padding => application.css
            height += 12
        elif self.__mask & SelectionListMask.SIDEBAR:
            self.get_style_context().add_class("row-big")
            # Padding => application.css
            height += 30
        else:
            self.get_style_context().add_class("row")
        self.set_size_request(-1, height)

    @property
    def is_populated(self):
        """
            Return True if populated
            @return bool
        """
        return True

    @property
    def name(self):
        """
            Get row name
            @return str
        """
        return self.__name

    @property
    def sortname(self):
        """
            Get row sortname
            @return str
        """
        return self.__sortname

    @property
    def id(self):
        """
            Get row id
            @return int
        """
        return self.__rowid

#######################
# PRIVATE             #
#######################
    def __on_artist_artwork(self, surface):
        """
            Set artist artwork
            @param surface as cairo.Surface
        """
        if surface is None:
            self.__artwork.get_style_context().add_class("artwork-icon")
            self.__artwork.set_size_request(ArtSize.SMALL,
                                            ArtSize.SMALL)
            self.__artwork.set_from_icon_name(
                                              "avatar-default-symbolic",
                                              Gtk.IconSize.DND)
        else:
            self.__artwork.get_style_context().remove_class("artwork-icon")
            self.__artwork.set_from_surface(surface)
        self.emit("populated")


class SelectionList(LazyLoadingView, FilteringHelper, GesturesHelper):
    """
        A list for artists/genres
    """
    __gsignals__ = {
        "populated": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self, base_mask):
        """
            Init Selection list ui
            @param base_mask as SelectionListMask
        """
        LazyLoadingView.__init__(self, ViewType.SCROLLED)
        FilteringHelper.__init__(self)
        self.__base_mask = base_mask
        self.__mask = SelectionListMask.NONE
        self.__sort = False
        self.__height = SelectionListRow.get_best_height(self)
        self._box = Gtk.ListBox()
        self._box.set_sort_func(self.__sort_func)
        self._box.show()
        GesturesHelper.__init__(self, self._box)
        self._viewport.add(self._box)
        if self.__base_mask & SelectionListMask.LIST_VIEW:
            overlay = Gtk.Overlay.new()
            overlay.set_hexpand(True)
            overlay.set_vexpand(True)
            overlay.show()
            overlay.add(self._scrolled)
            self.__fastscroll = FastScroll(self._box,
                                           self._scrolled)
            overlay.add_overlay(self.__fastscroll)
            self.add(overlay)
            self.__base_mask |= SelectionListMask.LABEL
        else:
            self._scrolled.set_policy(Gtk.PolicyType.NEVER,
                                      Gtk.PolicyType.AUTOMATIC)
            self.add(self._scrolled)
            self.get_style_context().add_class("sidebar")
            self.__menu_button = Gtk.Button.new_from_icon_name(
                "view-more-horizontal-symbolic", Gtk.IconSize.BUTTON)
            self.__menu_button.get_style_context().add_class("no-border")
            self.__menu_button.connect("clicked",
                                       lambda x: self.__popup_menu(0, 0, x))
            self.__menu_button.show()
            self.add(self.__menu_button)
        if self.__base_mask & SelectionListMask.LIST_VIEW:
            App().settings.connect("changed::artist-artwork",
                                   self.__on_artist_artwork_changed)
            App().art.connect("artist-artwork-changed",
                              self.__on_artist_artwork_changed)

    def set_mask(self, mask):
        """
            Mark list as artists list
            @param mask as SelectionListMask
        """
        self.__mask = mask

    def add_mask(self, mask):
        """
            Mark list as artists list
            @param mask as SelectionListMask
        """
        self.__mask |= mask

    def populate(self, values):
        """
            Populate view with values
            @param [(int, str, optional str)], will be deleted
        """
        self.__sort = False
        self._scrolled.get_vadjustment().set_value(0)
        self.clear()
        self.__add_values(values)

    def remove_value(self, object_id):
        """
            Remove id from list
            @param object_id as int
        """
        for child in self._box.get_children():
            if child.id == object_id:
                child.destroy()
                break

    def add_value(self, value):
        """
            Add item to list
            @param value as (int, str, optional str)
        """
        self.__sort = True
        # Do not add value if already exists
        for child in self._box.get_children():
            if child.id == value[0]:
                return
        row = self.__add_value(value[0], value[1], value[2])
        row.populate()

    def update_value(self, object_id, name):
        """
            Update object with new name
            @param object_id as int
            @param name as str
        """
        found = False
        for child in self._box.get_children():
            if child.id == object_id:
                child.set_label(name)
                found = True
                break
        if not found:
            if self.__base_mask & SelectionListMask.ARTISTS:
                self.__fastscroll.clear()
            row = self.__add_value(object_id, name, name)
            row.populate()
            if self.mask & SelectionListMask.ARTISTS:
                self.__fastscroll.populate()

    def update_values(self, values):
        """
            Update view with values
            @param [(int, str, optional str)]
        """
        if self.mask & SelectionListMask.ARTISTS:
            self.__fastscroll.clear()
        # Remove not found items
        value_ids = set([v[0] for v in values])
        for child in self._box.get_children():
            if child.id not in value_ids:
                self.remove_value(child.id)
        # Add items which are not already in the list
        item_ids = set([child.id for child in self._box.get_children()])
        for value in values:
            if not value[0] in item_ids:
                row = self.__add_value(value[0], value[1], value[2])
                row.populate()
        if self.mask & SelectionListMask.ARTISTS:
            self.__fastscroll.populate()

    def select_ids(self, ids=[], activate=True):
        """
            Select listbox items
            @param ids as [int]
            @param activate as bool
        """
        selected_ids = self.selected_ids
        if len(set(ids) & set(selected_ids)) == len(ids):
            return
        self._box.unselect_all()
        for row in self._box.get_children():
            if row.id in ids:
                self._box.select_row(row)
        if activate:
            for row in self._box.get_selected_rows():
                row.activate()
                break

    def grab_focus(self):
        """
            Grab focus on treeview
        """
        self._box.grab_focus()

    def clear(self):
        """
            Clear treeview
        """
        for child in self._box.get_children():
            child.destroy()
        if self.__base_mask & SelectionListMask.ARTISTS:
            self.__fastscroll.clear()
            self.__fastscroll.clear_chars()

    def get_playlist_headers(self):
        """
            Return playlist headers
            @return items as [(int, str)]
        """
        lists = ShownPlaylists.get()
        if lists:
            lists.append((Type.SEPARATOR, "", ""))
        return lists

    def select_first(self):
        """
            Select first available item
        """
        try:
            self._box.unselect_all()
            row = self._box.get_children()[0]
            row.activate()
        except Exception as e:
            Logger.warning("SelectionList::select_first(): %s", e)

    def activate_child(self):
        """
            Activated typeahead row
        """
        self._box.unselect_all()
        for row in self._box.get_children():
            style_context = row.get_style_context()
            if style_context.has_class("typeahead"):
                row.activate()
            style_context.remove_class("typeahead")

    @property
    def filtered(self):
        """
            Get filtered children
            @return [Gtk.Widget]
        """
        filtered = []
        for child in self._box.get_children():
            if isinstance(child, SelectionListRow):
                filtered.append(child)
        return filtered

    @property
    def listbox(self):
        """
            Get listbox
            @return Gtk.ListBox
        """
        return self._box

    @property
    def should_destroy(self):
        """
            True if view should be destroyed
            @return bool
        """
        return False

    @property
    def mask(self):
        """
            Get selection list type
            @return bit mask
        """
        return self.__mask | self.__base_mask

    @property
    def count(self):
        """
            Get items count in list
            @return int
        """
        return len(self._box.get_children())

    @property
    def selected_ids(self):
        """
            Get selected ids
            @return array of ids as [int]
        """
        return [row.id for row in self._box.get_selected_rows()]

#######################
# PROTECTED           #
#######################
    def _scroll_to_child(self, row):
        """
            Scroll to row
            @param row as SelectionListRow
        """
        coordinates = row.translate_coordinates(self._box, 0, 0)
        if coordinates:
            self._scrolled.get_vadjustment().set_value(coordinates[1])

    def _on_adaptive_changed(self, window, status):
        """
            Update internals
            @param window as Window
            @param status as bool
        """
        if status:
            self.__base_mask |= SelectionListMask.LABEL
        else:
            self.__base_mask &= ~SelectionListMask.LABEL
        for row in self._box.get_children():
            row.show_label(self.mask)
        self._scrolled.set_vexpand(True)
        self._scrolled.set_hexpand(status)
        if self.mask & SelectionListMask.SIDEBAR:
            if status:
                self.__menu_button.hide()
            else:
                self.__menu_button.show()

    def _on_map(self, widget):
        """
            Unselect all if adaptive
            @param widget as Gtk.Widget
        """
        if App().window.is_adaptive:
            self._box.unselect_all()

    def _on_primary_long_press_gesture(self, x, y):
        """
            Show row menu
            @param x as int
            @param y as int
        """
        self.__popup_menu(x, y)

    def _on_primary_press_gesture(self, x, y, event):
        """
            Activate current row
            @param x as int
            @param y as int
            @param event as Gdk.Event
        """
        if self.__base_mask & SelectionListMask.LIST_VIEW:
            row = self._box.get_row_at_y(y)
            if row is not None:
                (exists, state) = event.get_state()
                if state & Gdk.ModifierType.CONTROL_MASK or\
                        state & Gdk.ModifierType.SHIFT_MASK:
                    self._box.set_selection_mode(Gtk.SelectionMode.MULTIPLE)
                else:
                    self._box.set_selection_mode(Gtk.SelectionMode.SINGLE)

    def _on_secondary_press_gesture(self, x, y, event):
        """
            Show row menu
            @param x as int
            @param y as int
            @param event as Gdk.Event
        """
        self.__popup_menu(x, y)

#######################
# PRIVATE             #
#######################
    def __add_values(self, values):
        """
            Add values to the list
            @param items as [(int, str, str)]
        """
        if values:
            (rowid, name, sortname) = values.pop(0)
            row = self.__add_value(rowid, name, sortname)
            self._lazy_queue.append(row)
            GLib.idle_add(self.__add_values, values)
        else:
            if self.mask & SelectionListMask.ARTISTS:
                self.__fastscroll.populate()
            self.__sort = True
            self.emit("populated")
            self.lazy_loading()
            # Scroll to first selected item
            for row in self._box.get_selected_rows():
                GLib.idle_add(self._scroll_to_child, row)
                break

    def __add_value(self, rowid, name, sortname):
        """
            Add value to list
            @param rowid as int
            @param name as str
            @param sortname as str
            @return row as SelectionListRow
        """
        if rowid > 0 and self.mask & SelectionListMask.ARTISTS:
            used = sortname if sortname else name
            self.__fastscroll.add_char(used[0])
        row = SelectionListRow(rowid, name, sortname,
                               self.mask, self.__height)
        row.show()
        self._box.add(row)
        return row

    def __sort_func(self, row_a, row_b):
        """
            Sort rows
            @param row_a as SelectionListRow
            @param row_b as SelectionListRow
        """
        if not self.__sort:
            return False
        a_index = row_a.id
        b_index = row_b.id

        # Static vs static
        if a_index < 0 and b_index < 0:
            return a_index < b_index
        # Static entries always on top
        elif b_index < 0:
            return True
        # Static entries always on top
        if a_index < 0:
            return False
        # String comparaison for non static
        else:
            if self.mask & SelectionListMask.ARTISTS:
                a = row_a.sortname
                b = row_b.sortname
            else:
                a = row_a.name
                b = row_b.name
            return strcoll(a, b)

    def __popup_menu(self, x, y, relative=None):
        """
            Show menu at (x, y)
            @param x as int
            @param y as int
            @param relative as Gtk.Widget
        """
        if self.__base_mask & (SelectionListMask.SIDEBAR |
                               SelectionListMask.LIST_VIEW):
            from lollypop.menu_selectionlist import SelectionListMenu
            from lollypop.widgets_utils import Popover
            if relative is None:
                row = self._box.get_row_at_y(y)
                row_id = row.id
                relative = self._box
            else:
                row_id = None
            menu = SelectionListMenu(self, row_id, self.mask)
            popover = Popover()
            popover.bind_model(menu, None)
            popover.set_relative_to(relative)
            if x != y != 0:
                rect = Gdk.Rectangle()
                rect.x = x
                rect.y = y
                rect.width = rect.height = 1
                popover.set_pointing_to(rect)
            popover.popup()

    def __on_artist_artwork_changed(self, object, value):
        """
            Update row artwork
            @param object as GObject.Object
            @param value as str
        """
        artist = value if object == App().art else None
        if self.mask & SelectionListMask.ARTISTS:
            for row in self._box.get_children():
                if artist is None:
                    row.set_style(self.__height)
                    row.set_artwork()
                elif row.name == artist:
                    row.set_artwork()
                    break
