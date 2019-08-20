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

from gi.repository import GLib

from gettext import gettext as _

from lollypop.define import App, SelectionListMask, Type


class ScannerContainer:
    """
        Scanner management for main view
    """

    def __init__(self):
        """
            Init container
        """
        App().scanner.connect("scan-finished", self.__on_scan_finished)
        App().scanner.connect("genre-updated", self.__on_genre_updated)
        App().scanner.connect("artist-updated", self.__on_artist_updated)

############
# PRIVATE  #
############
    def __on_scan_finished(self, scanner, modifications):
        """
            Update lists
            @param scanner as CollectionScanner
            @param modifications as bool
        """
        if modifications:
            from lollypop.app_notification import AppNotification
            notification = AppNotification(_("New tracks available"),
                                           [_("Refresh")],
                                           [lambda: self.reload_view()])
            self.add_overlay(notification)
            notification.show()
            notification.set_reveal_child(True)
            GLib.timeout_add(5000, notification.set_reveal_child, False)
            GLib.timeout_add(10000, notification.destroy)

    def __on_genre_updated(self, scanner, genre_id, add):
        """
            Add genre to genre list
            @param scanner as CollectionScanner
            @param genre_id as int
            @param add as bool
        """
        if Type.GENRES_LIST in self.sidebar.selected_ids:
            if add:
                genre_name = App().genres.get_name(genre_id)
                self.left_list.add_value((genre_id, genre_name, genre_name))
            elif not App().artists.get_ids([genre_id]):
                self.left_list.remove_value(genre_id)

    def __on_artist_updated(self, scanner, artist_id, add):
        """
            Add/remove artist to/from list
            @param scanner as CollectionScanner
            @param artist_id as int
            @param add as bool
        """
        if Type.GENRES_LIST in self.sidebar.selected_ids:
            selection_list = self.right_list
            genre_ids = self.left_list.selected_ids
        elif Type.ARTISTS_LIST in self.sidebar.selected_ids and\
                self.left_list.mask & SelectionListMask.ARTISTS:
            selection_list = self.left_list
            genre_ids = []
        else:
            return
        artist_ids = App().artists.get_ids(genre_ids)
        # We only test add, remove and absent is safe
        if artist_id not in artist_ids and add:
            return
        artist_name = App().artists.get_name(artist_id)
        sortname = App().artists.get_sortname(artist_id)
        genre_ids = []
        if add:
            selection_list.add_value((artist_id, artist_name, sortname))
        elif not App().albums.get_ids([artist_id], genre_ids):
            selection_list.remove_value(artist_id)
