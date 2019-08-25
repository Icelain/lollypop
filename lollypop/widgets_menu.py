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

from lollypop.objects_album import Album
from lollypop.define import App, ArtSize, ArtBehaviour, MARGIN


class MenuBuilder(Gtk.Stack):
    """
        Advanced menu model constructor
        Does not support submenus
    """

    __gsignals__ = {
        "closed": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "hidden": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self, menu):
        """
            Init menu
            @param menu as Gio.Menu
        """
        Gtk.Stack.__init__(self)
        self.__boxes = {}
        self.__add_menu(menu, "main")

#######################
# PRIVATE             #
#######################
    def __add_menu(self, menu, menu_name, submenu=False):
        """
            Build menu
            @param menu as Gio.Menu
            @param menu_name as str
            @param submenu = False
        """
        box = self.get_child_by_name(menu_name)
        if box is None:
            box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
            box.connect("map", self.__on_box_map, menu_name)
            self.__boxes[menu_name] = box
            box.set_property("margin", 10)
            box.show()
            if submenu:
                scrolled = Gtk.ScrolledWindow()
                scrolled.set_policy(Gtk.PolicyType.NEVER,
                                    Gtk.PolicyType.AUTOMATIC)
                scrolled.show()
                scrolled.add(box)
                self.add_named(scrolled, menu_name)
                button = Gtk.ModelButton.new()
                button.get_style_context().add_class("padding")
                button.set_property("menu-name", "main")
                button.set_property("inverted", True)
                button.set_label(menu_name)
                button.show()
                box.add(button)
            else:
                self.add_named(box, menu_name)
        n_items = menu.get_n_items()
        for i in range(0, n_items):
            label = menu.get_item_attribute_value(i, "label")
            action = menu.get_item_attribute_value(i, "action")
            header = menu.get_item_attribute_value(i, "header")
            tooltip = menu.get_item_attribute_value(i, "tooltip")
            close = menu.get_item_attribute_value(i, "close") is not None
            if header is not None:
                album_id = menu.get_item_attribute_value(i, "album-id")
                icon_name = menu.get_item_attribute_value(i, "icon-name")
                if album_id is not None:
                    self.__add_album_header(label, album_id, menu_name)
                elif icon_name is not None:
                    self.__add_header(label, icon_name, menu_name)
            elif action is None:
                link = menu.get_item_link(i, "section")
                submenu = menu.get_item_link(i, "submenu")
                if link is not None:
                    self.__add_section(label, link, menu_name)
                elif submenu is not None:
                    self.__add_submenu(label, submenu, menu_name)
            else:
                target = menu.get_item_attribute_value(i, "target")
                self.__add_item(label, action, target,
                                tooltip, close, menu_name)

    def __add_item(self, text, action, target, tooltip, close, menu_name):
        """
            Add a Menu item
            @param text as GLib.Variant
            @param action as Gio.Action
            @param target as GLib.Variant
            @parmam tooltip as GLib.Variant
            @param close as bool
            @param menu_name as str
        """
        button = Gtk.ModelButton.new()
        button.set_action_name(action.get_string())
        button.set_label(text.get_string())
        button.set_alignment(0, 0.5)
        if close:
            button.connect("clicked", lambda x: self.emit("closed"))
        if tooltip is not None:
            button.set_tooltip_markup(tooltip.get_string())
            button.set_has_tooltip(True)
        if target is not None:
            button.set_action_target_value(target)
        button.show()
        self.__boxes[menu_name].add(button)

    def __add_section(self, text, menu, menu_name):
        """
            Add section to menu
            @param text as as GLib.Variant
            @param menu as Gio.Menu
            @param menu_name as str
        """
        box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 4)
        sep1 = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
        sep1.set_hexpand(True)
        sep1.set_property("valign", Gtk.Align.CENTER)
        box.add(sep1)
        label = Gtk.Label.new(text.get_string())
        label.get_style_context().add_class("dim-label")
        if App().window.is_adaptive:
            label.get_style_context().add_class("padding")
        box.add(label)
        sep2 = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
        sep2.set_property("valign", Gtk.Align.CENTER)
        sep2.set_hexpand(True)
        box.add(sep2)
        box.show_all()
        self.__boxes[menu_name].add(box)
        self.__add_menu(menu, menu_name)

    def __add_submenu(self, text, menu, menu_name):
        """
            Add submenu
            @param text as GLib.Variant
            @param menu as Gio.Menu
            @param menu_name as str
        """
        submenu_name = text.get_string()
        self.__add_menu(menu, submenu_name, True)
        button = Gtk.ModelButton.new()
        button.set_property("menu-name", submenu_name)
        button.set_label(text.get_string())
        button.set_alignment(0, 0.5)
        button.show()
        self.__boxes[menu_name].add(button)

    def __add_header(self, text, icon_name, menu_name):
        """
            Add an header for albums to close menu
            @param text as GLib.Variant
            @param icon_name as GLib.Variant
            @param menu_name as str
        """
        button = Gtk.ModelButton.new()
        button.set_alignment(0, 0.5)
        button.connect("clicked", lambda x: self.emit("closed"))
        button.show()
        label = Gtk.Label.new()
        label.set_markup(text.get_string())
        label.show()
        artwork = Gtk.Image.new_from_icon_name(icon_name.get_string(),
                                               Gtk.IconSize.INVALID)
        artwork.set_pixel_size(ArtSize.MEDIUM)
        artwork.show()
        grid = Gtk.Grid()
        grid.set_column_spacing(MARGIN)
        grid.add(artwork)
        grid.add(label)
        button.set_image(grid)
        button.get_style_context().add_class("padding")
        self.__boxes[menu_name].add(button)

    def __add_album_header(self, text, album_id, menu_name):
        """
            Add an header for albums to close menu
            @param text as GLib.Variant
            @param album_id as GLib.Variant
            @param menu_name as str
        """
        button = Gtk.ModelButton.new()
        button.set_alignment(0, 0.5)
        button.connect("clicked", lambda x: self.emit("closed"))
        button.show()
        label = Gtk.Label.new()
        label.set_markup(text.get_string())
        label.show()
        artwork = Gtk.Image.new()
        grid = Gtk.Grid()
        grid.set_column_spacing(MARGIN)
        grid.add(artwork)
        grid.add(label)
        button.set_image(grid)
        button.get_style_context().add_class("padding")
        App().art_helper.set_album_artwork(
                Album(album_id.get_int32()),
                ArtSize.MEDIUM,
                ArtSize.MEDIUM,
                artwork.get_scale_factor(),
                ArtBehaviour.CACHE | ArtBehaviour.CROP_SQUARE,
                self.__on_album_artwork,
                artwork)
        self.__boxes[menu_name].add(button)

    def __on_album_artwork(self, surface, artwork):
        """
            Set album artwork
            @param surface as str
            @param artwork as Gtk.Image
        """
        if surface is None:
            artwork.set_from_icon_name("folder-music-symbolic",
                                       Gtk.IconSize.BUTTON)
        else:
            artwork.set_from_surface(surface)
        artwork.show()

    def __on_box_map(self, widget, menu_name):
        """
            On map, set stack order
            @param widget as Gtk.Widget
            @param menu_name as str
        """
        if menu_name == "main":
            self.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
            self.set_size_request(-1, -1)
        else:
            self.set_size_request(-1, 300)
            self.set_transition_type(Gtk.StackTransitionType.SLIDE_RIGHT)
