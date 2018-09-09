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

from lollypop.view_flowbox import FlowBoxView
# from lollypop.widgets_album_decade import AlbumDecadeWidget


class PlaylistsBoxView(FlowBoxView):
    """
        Show decades in a FlowBox
    """

    def __init__(self):
        """
            Init decade view
        """
        FlowBoxView.__init__(self)
        self._widget_class = None
