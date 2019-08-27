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

from lollypop.logger import Logger
from lollypop.selectionlist import SelectionList
from lollypop.define import App, Type, SelectionListMask
from lollypop.shown import ShownLists
from lollypop.helper_gestures import GesturesHelper


class ListsContainer:
    """
        Selections lists management for main view
    """

    def __init__(self):
        """
            Init container
        """
        pass

    def setup_lists(self):
        """
            Setup container lists
        """
        self.__left_list = None
        self.__right_list = None
        self._sidebar = SelectionList(SelectionListMask.SIDEBAR)
        self._sidebar.show()
        self._sidebar.listbox.connect("row-activated",
                                      self.__on_sidebar_activated)
        self._sidebar.connect("populated", self.__on_sidebar_populated)
        self._main_widget.insert_column(0)
        self._sidebar.set_mask(SelectionListMask.SIDEBAR)
        items = ShownLists.get(SelectionListMask.SIDEBAR)
        self._sidebar.populate(items)

    @property
    def sidebar(self):
        """
            Get first SelectionList
            @return SelectionList
        """
        return self._sidebar

    @property
    def left_list(self):
        """
            Get left selection list
            @return SelectionList
        """
        if self.__left_list is None:
            self.__left_list = SelectionList(SelectionListMask.VIEW)
            self.__left_list.listbox.connect("row-activated",
                                             self.__on_left_list_activated)
        return self.__left_list

    @property
    def right_list(self):
        """
            Get right selection list
            @return SelectionList
        """
        if self.__right_list is None:
            eventbox = Gtk.EventBox.new()
            eventbox.set_size_request(50, -1)
            eventbox.show()
            self.__right_list_grid = Gtk.Grid()
            style_context = self.__right_list_grid.get_style_context()
            style_context.add_class("left-gradient")
            style_context.add_class("opacity-transition-fast")
            self.__right_list = SelectionList(SelectionListMask.VIEW)
            self.__right_list.show()
            self.__gesture = GesturesHelper(
                eventbox, primary_press_callback=self.__hide_right_list)
            self.__right_list.listbox.connect("row-activated",
                                              self.__on_right_list_activated)
            self.__right_list_grid.add(eventbox)
            self.__right_list_grid.add(self.__right_list)
            self.__left_list.overlay.add_overlay(self.__right_list_grid)
        return self.__right_list

##############
# PROTECTED  #
##############

############
# PRIVATE  #
############
    def __hide_right_list(self, *ignore):
        """
            Hide right list
        """
        if self.__right_list is not None:
            self.__right_list_grid.unset_state_flags(Gtk.StateFlags.VISITED)
            GLib.timeout_add(200, self.__right_list_grid.hide)
            self.__right_list.clear()

    def __show_genres_list(self, selection_list):
        """
            Setup list for genres
            @param list as SelectionList
        """
        def load():
            genres = App().genres.get()
            return genres
        selection_list.set_mask(SelectionListMask.GENRES)
        App().task_helper.run(load, callback=(selection_list.populate,))

    def __show_artists_list(self, selection_list, genre_ids=[]):
        """
            Setup list for artists
            @param list as SelectionList
            @param genre_ids as [int]
        """
        def load():
            if App().settings.get_value("show-performers"):
                artists = App().artists.get_all(genre_ids)
            else:
                artists = App().artists.get(genre_ids)
            return artists
        selection_list.set_mask(SelectionListMask.ARTISTS)
        App().task_helper.run(load, callback=(selection_list.populate,))

    def __on_sidebar_activated(self, listbox, row):
        """
            Update view based on selected object
            @param listbox as Gtk.ListBox
            @param row as Gtk.ListBoxRow
        """
        Logger.debug("Container::__on_sidebar_activated()")
        view = None
        selected_ids = self._sidebar.selected_ids
        if not selected_ids:
            return
        # Update lists
        if selected_ids[0] == Type.ARTISTS_LIST:
            self.__show_artists_list(self.left_list)
            self.__hide_right_list()
            self.left_list.show()
            self.left_list.set_sidebar_id(Type.ARTISTS_LIST)
        elif selected_ids[0] == Type.GENRES_LIST:
            self.__show_genres_list(self.left_list)
            self.__hide_right_list()
            self.left_list.show()
            self.left_list.set_sidebar_id(Type.GENRES_LIST)
        else:
            self.left_list.hide()

        if selected_ids[0] == Type.PLAYLISTS:
            view = self._get_view_playlists()
        elif selected_ids[0] == Type.LYRICS:
            view = self._get_view_lyrics()
        elif selected_ids[0] == Type.CURRENT:
            view = self.get_view_current()
        elif selected_ids[0] == Type.SEARCH:
            view = self.get_view_search()
        elif selected_ids[0] == Type.SUGGESTIONS:
            view = self._get_view_suggestions()
        elif selected_ids[0] in [Type.POPULARS,
                                 Type.LOVED,
                                 Type.RECENTS,
                                 Type.NEVER,
                                 Type.RANDOMS,
                                 Type.WEB]:
            view = self._get_view_albums(selected_ids, [])
        elif selected_ids[0] == Type.RADIOS:
            view = self._get_view_radios()
        elif selected_ids[0] == Type.YEARS:
            view = self._get_view_albums_decades()
        elif selected_ids[0] == Type.GENRES:
            view = self._get_view_genres()
        elif selected_ids[0] == Type.ARTISTS:
            view = self._get_view_artists_rounded()
        elif selected_ids[0] == Type.ALL:
            view = self._get_view_albums(selected_ids, [])
        elif selected_ids[0] == Type.COMPILATIONS:
            view = self._get_view_albums(selected_ids, [])
        if view is not None and view not in self._stack.get_children():
            view.show()
            self._stack.add(view)
        # If we are in paned stack mode, show list two if wanted
        if App().window.is_adaptive\
                and selected_ids[0] in [Type.ARTISTS_LIST,
                                        Type.GENRES_LIST]:
            self._stack.set_visible_child(self.left_list)
            self.left_list.set_sidebar_id(selected_ids[0])
        elif view is not None:
            self._stack.set_visible_child(view)
            view.set_sidebar_id(selected_ids[0])

    def __on_sidebar_populated(self, selection_list):
        """
            @param selection_list as SelectionList
        """
        if App().settings.get_value("save-state"):
            self._stack.load_history()
            self.emit("can-go-back-changed", self.can_go_back)
        else:
            startup_id = App().settings.get_value("startup-id").get_int32()
            if startup_id == -1:
                if not App().window.is_adaptive:
                    selection_list.select_first()
            else:
                selection_list.select_ids([startup_id], True)

    def __on_left_list_activated(self, listbox, row):
        """
            Update view based on selected object
            @param listbox as Gtk.ListBox
            @param row as Gtk.ListBoxRow
        """
        Logger.debug("Container::__on_left_list_activated()")
        selected_ids = self.left_list.selected_ids
        view = None
        if self.left_list.mask & SelectionListMask.GENRES:
            if not App().window.is_adaptive:
                view = self._get_view_albums(selected_ids, [])
            self.__show_artists_list(self.right_list, selected_ids)
            self.__right_list_grid.show()
            self.__right_list_grid.set_state_flags(Gtk.StateFlags.VISITED,
                                                   False)
        else:
            view = self._get_view_artists([], selected_ids)
        if view is not None:
            view.show()
            view.set_sidebar_id(self.left_list.sidebar_id)
            self._stack.add(view)
            self._stack.set_visible_child(view)

    def __on_right_list_activated(self, listbox, row):
        """
            Update view based on selected object
            @param listbox as Gtk.ListBox
            @param row as Gtk.ListBoxRow
        """
        genre_ids = self.left_list.selected_ids
        artist_ids = self.right_list.selected_ids
        view = self._get_view_artists(genre_ids, artist_ids)
        view.show()
        view.set_sidebar_id(self.left_list.sidebar_id)
        self._stack.add(view)
        self._stack.set_visible_child(view)
