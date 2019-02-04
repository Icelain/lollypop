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

from lollypop.define import App, ArtSize


class PlaylistsContainer:
    """
        Playlists management for main view
    """

    def __init__(self):
        """
            Init container
        """
        pass

    def show_playlist_manager(self, obj):
        """
            Show playlist manager for object_id
            Current view stay present in ViewContainer
            @param obj as Track/Album
        """
        from lollypop.view_playlists_manager import PlaylistsManagerView
        current = self._stack.get_visible_child()
        if App().window.is_adaptive:
            art_size = ArtSize.BIG
        else:
            art_size = ArtSize.ROUNDED
        view = PlaylistsManagerView(obj, art_size)
        view.populate(App().playlists.get_ids())
        view.show()
        self._stack.add(view)
        App().window.container.stack.set_navigation_enabled(True)
        self._stack.set_visible_child(view)
        App().window.container.stack.set_navigation_enabled(False)
        current.disable_overlay()

    def show_smart_playlist_editor(self, playlist_id):
        """
            Show a view allowing user to edit smart view
            @param playlist_id as int
        """
        App().window.emit("can-go-back-changed", True)
        from lollypop.view_playlist_smart import SmartPlaylistView
        current = self._stack.get_visible_child()
        view = SmartPlaylistView(playlist_id)
        view.populate()
        view.show()
        self._stack.add(view)
        App().window.container.stack.set_navigation_enabled(True)
        self._stack.set_visible_child(view)
        App().window.container.stack.set_navigation_enabled(False)
        current.disable_overlay()

##############
# PROTECTED  #
##############

############
# PRIVATE  #
############
