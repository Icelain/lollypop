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

from gi.repository import Gtk, GLib

from lollypop.define import App, SidebarContent, Type
from lollypop.view import View
from lollypop.adaptive import AdaptiveStack
from lollypop.container_notification import NotificationContainer
from lollypop.container_scanner import ScannerContainer
from lollypop.container_playlists import PlaylistsContainer
from lollypop.container_lists import ListsContainer
from lollypop.container_views import ViewsContainer
from lollypop.progressbar import ProgressBar


class Container(Gtk.Overlay, NotificationContainer,
                ScannerContainer, PlaylistsContainer,
                ListsContainer, ViewsContainer):
    """
        Main view management
    """

    def __init__(self):
        """
            Init container
        """
        Gtk.Overlay.__init__(self)
        NotificationContainer.__init__(self)
        ScannerContainer.__init__(self)
        PlaylistsContainer.__init__(self)
        ListsContainer.__init__(self)
        ViewsContainer.__init__(self)
        self._rounded_artists_view = None
        self._stack = AdaptiveStack()
        self._stack.show()
        self.__setup_view()
        self.add(self.__paned_one)

    def stop_all(self):
        """
            Stop current view from processing
        """
        view = self._stack.get_visible_child()
        if view is not None:
            view.stop()

    def reload_view(self):
        """
            Reload current view
        """
        if App().settings.get_value("show-sidebar"):
            self._reload_list_view()
        else:
            self._reload_navigation_view()

    def show_sidebar(self, show):
        """
            Show/Hide navigation sidebar
            @param show as bool
        """
        def select_list_one(selection_list):
            self._reload_list_view()
            self._list_one.disconnect_by_func(select_list_one)

        adaptive_window = App().window.is_adaptive
        if self._rounded_artists_view is not None:
            self._rounded_artists_view.make_destroyable()
            self._rounded_artists_view = None
        if show or adaptive_window:
            if not adaptive_window:
                App().window.emit("show-can-go-back", False)
            self._list_one.show()
            if self._list_one.count == 0:
                self._list_one.connect("populated", select_list_one)
                self.update_list_one()
            else:
                # Show settings dialog
                from lollypop.view_settings import SettingsChildView
                from lollypop.view_settings import SettingsView
                if isinstance(self.view, SettingsChildView) or\
                        isinstance(self.view, SettingsView):
                    action = App().lookup_action("settings")
                    GLib.idle_add(action.activate,
                                  GLib.Variant("i", self.view.type))
                self._reload_list_view()
        elif not adaptive_window:
            if self._list_one.get_visible():
                self._list_two.hide()
                self._list_one.hide()
            from lollypop.view_search import SearchView
            for child in self._stack.get_children():
                if type(child) != SearchView:
                    child.destroy()
            self._reload_navigation_view()

    def show_artists_albums(self, artist_ids):
        """
            Show albums from artists
            @param artist_ids as [int]
        """
        def select_list_two(selection_list, artist_ids):
            self._list_two.select_ids(artist_ids)
            self._list_two.disconnect_by_func(select_list_two)
        sidebar_content = App().settings.get_enum("sidebar-content")
        if sidebar_content == SidebarContent.GENRES:
            # Get artist genres
            genre_ids = []
            for artist_id in artist_ids:
                album_ids = App().artists.get_albums(artist_ids)
                for album_id in album_ids:
                    for genre_id in App().albums.get_genre_ids(album_id):
                        if genre_id not in genre_ids:
                            genre_ids.append(genre_id)
            self.show_lists(genre_ids, artist_ids)
        elif sidebar_content == SidebarContent.ARTISTS:
            # Select artists on list one
            self.show_lists(artist_ids, [])
        else:
            self.show_view(artist_ids)

    @property
    def view(self):
        """
            Get current view
            @return View
        """
        view = self._stack.get_visible_child()
        if view is not None and isinstance(view, View):
            return view
        return None

    @property
    def stack(self):
        """
            Container stack
            @return stack as Gtk.Stack
        """
        return self._stack

    @property
    def paned_one(self):
        """
            Get first paned (list_one)
        """
        return self.__paned_one

    @property
    def paned_two(self):
        """
            Get second paned (list_two)
        """
        return self.__paned_two

    @property
    def progress(self):
        """
            Progress bar
            @return ProgressBar
        """
        return self.__progress

############
# PRIVATE  #
############
    def __setup_view(self):
        """
            Setup window main view:
                - genre list
                - artist list
                - main view as artist view or album view
        """
        self.__paned_one = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)
        self.__paned_two = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)

        self.__paned_one.connect("notify::position", self.__on_paned_position)
        self.__paned_two.connect("notify::position", self.__on_paned_position)

        self.__progress = ProgressBar()
        self.__progress.get_style_context().add_class("progress-bottom")
        self.__progress.set_property("valign", Gtk.Align.END)
        self.add_overlay(self.__progress)

        self.__paned_two.add1(self._list_two)
        self.__paned_two.add2(self._stack)
        self.__paned_one.add1(self._list_one)
        self.__paned_one.add2(self.__paned_two)
        position1 = App().settings.get_value(
            "paned-mainlist-width").get_int32()
        position2 = App().settings.get_value(
            "paned-listview-width").get_int32()
        self.__paned_one.set_position(position1)
        # GTK does not like paned inside paned set_position()
        GLib.timeout_add(100, self.__paned_two.set_position, position2)
        self.__paned_one.show()
        self.__paned_two.show()
        search_action = App().lookup_action("search")
        search_action.connect("activate", self.__on_search_activate)

    def __on_search_activate(self, action, variant):
        """
            @param action as Gio.SimpleAction
            @param variant as GLib.Variant
        """
        if App().window.is_adaptive:
            search = variant.get_string()
            App().window.container.show_view([Type.SEARCH], search)

    def __on_paned_position(self, paned, param):
        """
            Save paned position
            @param paned as Gtk.Paned
            @param param as GParamSpec
        """
        position = paned.get_property(param.name)
        if paned == self.__paned_one:
            setting = "paned-mainlist-width"
        else:
            setting = "paned-listview-width"
        if position < 100:
            position = 100
        App().settings.set_value(setting,
                                 GLib.Variant("i",
                                              position))
