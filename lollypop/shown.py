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

from gettext import gettext as _

from lollypop.define import Type, App, SelectionListMask


class ShownLists:
    """
        Handle shown lists
    """

    IDS = {
        Type.POPULARS: (_("Popular albums"), SelectionListMask.LIST_ONE),
        Type.RANDOMS: (_("Random albums"), SelectionListMask.LIST_ONE),
        Type.LOVED: (_("Loved albums"), SelectionListMask.LIST_ONE),
        Type.RECENTS: (_("Recently added albums"), SelectionListMask.LIST_ONE),
        Type.NEVER: (_("Unplayed albums"), SelectionListMask.LIST_ONE),
        Type.PLAYLISTS: (_("Playlists"), SelectionListMask.LIST_ONE),
        Type.RADIOS: (_("Radios"), SelectionListMask.LIST_ONE),
        Type.YEARS: (_("Years"), SelectionListMask.LIST_ONE),
        Type.GENRES: (_("Genres"), SelectionListMask.LIST_ONE),
        Type.ALL: (_("All albums"), SelectionListMask.LIST_ONE),
        Type.ARTISTS: (_("All artists"), SelectionListMask.ALL_ARTISTS),
        Type.COMPILATIONS: (_("Compilations"), SelectionListMask.COMPILATIONS),
        Type.USB_DISKS: (_("USB disks"),  SelectionListMask.LIST_ONE)
    }

    def get(mask, get_all=False):
        """
            Get list
            @param mask as bit mask
            @param get_all as bool
            @return [(,)]
        """
        wanted = list(App().settings.get_value("shown-album-lists"))
        if get_all:
            wanted.append(Type.USB_DISKS)
        lists = []
        for key in ShownLists.IDS.keys():
            (string, id_mask) = ShownLists.IDS[key]
            if mask & id_mask and (get_all or key in wanted):
                lists.append((key, string, ""))
        return lists


class ShownPlaylists:
    """
        Handle shown playlists
    """
    def get(get_all=False):
        """
            get list
            @param get_all as bool
        """
        wanted = App().settings.get_value("shown-playlists")
        lists = []
        if get_all or Type.POPULARS in wanted:
            lists.append((Type.POPULARS, _("Popular tracks"), ""))
        if get_all or Type.LOVED in wanted:
            lists.append((Type.LOVED, App().playlists.LOVED, ""))
        if get_all or Type.RECENTS in wanted:
            lists.append((Type.RECENTS, _("Recently played"), ""))
        if get_all or Type.NEVER in wanted:
            lists.append((Type.NEVER, _("Unplayed"), ""))
        if get_all or Type.RANDOMS in wanted:
            lists.append((Type.RANDOMS, _("Random tracks"), ""))
        return lists
