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

# This is global object initialised at lollypop start
# member init order is important!

from gi.repository import Gio, GLib


LOLLYPOP_DATA_PATH = GLib.get_user_data_dir() + "/lollypop"

App = Gio.Application.get_default

GOOGLE_API_ID = "015987506728554693370:waw3yqru59a"

TAG_EDITORS = ["kid3-qt", "exfalso", "easytag", "picard", "puddletag"]

MARGIN = 15
MARGIN_SMALL = 5

# All cache goes here
CACHE_PATH = GLib.get_user_cache_dir() + "/lollypop"
# Fallback when album dir is readonly
STORE_PATH = GLib.get_user_data_dir() + "/lollypop/store"
# Store for Web
WEB_PATH = GLib.get_user_data_dir() + "/lollypop/web_store"


class Repeat:
    NONE = 0
    AUTO = 1
    TRACK = 2
    ALL = 3


class GstPlayFlags:
    GST_PLAY_FLAG_VIDEO = 1 << 0  # We want video output
    GST_PLAY_FLAG_AUDIO = 1 << 1  # We want audio output
    GST_PLAY_FLAG_TEXT = 1 << 3   # We want subtitle output


class StorageType:
    NONE = 1 << 0
    COLLECTION = 1 << 1
    EPHEMERAL = 1 << 2
    SAVED = 1 << 3
    SPOTIFY_NEW_RELEASES = 1 << 4
    SPOTIFY_SIMILARS = 1 << 5


class ArtBehaviour:
    NONE = 1 << 0
    ROUNDED = 1 << 1
    ROUNDED_BORDER = 1 << 2
    BLUR = 1 << 3
    BLUR_HARD = 1 << 4
    BLUR_MAX = 1 << 5
    FALLBACK = 1 << 6
    DARKER = 1 << 7
    LIGHTER = 1 << 8
    CROP = 1 << 9
    CROP_SQUARE = 1 << 10
    CACHE = 1 << 11
    NO_CACHE = 1 << 12


class ViewType:
    DEFAULT = 1 << 0
    TWO_COLUMNS = 1 << 1
    DND = 1 << 2
    SEARCH = 1 << 3
    PLAYLISTS = 1 << 4
    POPOVER = 1 << 5
    ALBUM = 1 << 6
    SMALL = 1 << 7
    MEDIUM = 1 << 8
    SCROLLED = 1 << 9
    FULLSCREEN = 1 << 10
    PLACEHOLDER = 1 << 11
    NO_PADDING = 1 << 12
    PLAYBACK = 1 << 13


NetworkAccessACL = {
    "DATA": 1 << 1,
    "LASTFM": 1 << 2,
    "SPOTIFY": 1 << 3,
    "YOUTUBE": 1 << 4,
    "GOOGLE": 1 << 5,
    "STARTPAGE": 1 << 6,
    "WIKIPEDIA": 1 << 7,
    "TUNEIN": 1 << 8,
    "MUSICBRAINZ": 1 << 9,
    "ITUNES": 1 << 10,
    "DEEZER": 1 << 11,
    "WIKIA": 1 << 12,
    "GENIUS": 1 << 13,
    "AUDIODB": 1 << 14
}


class IndicatorType:
    NONE = 1 << 0
    PLAY = 1 << 1
    LOVED = 1 << 2
    SKIP = 1 << 3
    LOADING = 1 << 4


class ArtSize:
    SMALL = 50
    MEDIUM = 100
    BANNER = 150
    BIG = 200
    MINIPLAYER = 300
    FULLSCREEN = 400
    MPRIS = 900


class ScanType:
    EPHEMERAL = 0
    NEW_FILES = 1
    FULL = 2


class SelectionListMask:
    NONE = 1 << 0
    SIDEBAR = 1 << 1
    VIEW = 1 << 2
    ARTISTS = 1 << 3
    GENRES = 1 << 4
    PLAYLISTS = 1 << 5
    COMPILATIONS = 1 << 6
    LABEL = 1 << 7
    ELLIPSIZE = 1 << 8


class Shuffle:
    NONE = 0             # No shuffle
    TRACKS = 1           # Shuffle by tracks on genre
    ALBUMS = 2           # Shuffle by albums on genre


class Notifications:
    NONE = 0
    ALL = 1
    MPRIS = 2


class PowerManagement:
    NONE = 0             # Use OS defaults
    IDLE = 1             # Inhibit screensaver
    SUSPEND = 2          # Inhibit suspend
    BOTH = 3             # Inhibit screensaver and suspend


class AdaptiveSize:
    NONE = 1 << 0
    SMALL = 1 << 1
    MEDIUM = 1 << 2
    NORMAL = 1 << 3
    BIG = 1 << 4
    LARGE = 1 << 5


class Size:
    MINI = 250
    SMALL = 400
    MEDIUM = 720  # Librem Phone
    NORMAL = 1000
    BIG = 1300


class OrderBy:
    ARTIST = 0
    NAME = 1
    YEAR = 2
    POPULARITY = 3


# Order is important
class Type:
    NONE = -1
    SUGGESTIONS = -2
    POPULARS = -3
    RANDOMS = -4
    RECENTS = -5
    LOVED = -6
    NEVER = -7
    PLAYLISTS = -8
    RADIOS = -9
    INFO = -10
    YEARS = -11
    ARTISTS = -12
    ARTISTS_LIST = -13
    SETTINGS = -14
    SETTINGS_APPEARANCE = -15
    SETTINGS_BEHAVIOUR = -16
    SETTINGS_COLLECTIONS = -17
    SETTINGS_WEB = -18
    SETTINGS_DEVICES = -19
    GENRES = -20
    GENRES_LIST = -21
    # WEB is stored in DB, can't be changed
    WEB = -22
    ALBUM = -23
    SMART = -24
    EQUALIZER = -25
    ALL = -100
    DEVICE_ALBUMS = -1000
    DEVICE_PLAYLISTS = -1001
    # Stored in DB, can't be changed
    COMPILATIONS = -2001
    SEPARATOR = -2002
    CURRENT = -2003
    SEARCH = -2004
    LYRICS = -2005


LATIN1_ENCODING = b"\x00"
"""Byte code for latin1"""
UTF_16_ENCODING = b"\x01"
"""Byte code for UTF-16"""
UTF_16BE_ENCODING = b"\x02"
"""Byte code for UTF-16 (big endian)"""
UTF_8_ENCODING = b"\x03"
"""Byte code for UTF-8 (Not supported in ID3 versions < 2.4)"""


SPOTIFY_CLIENT_ID = "0b144843878a46b2b12e0958c342c3ac"
SPOTIFY_SECRET = "265ab8e057684f1b9e69e0c58f4881c1"
AUDIODB_CLIENT_ID = "195003"

STATIC_ALBUM_NAME = {
    Type.POPULARS: "Popular albums",
    Type.RANDOMS: "Random albums",
    Type.LOVED: "Loved albums",
    Type.RECENTS: "Recently added albums",
    Type.NEVER: "Unplayed albums",
    Type.PLAYLISTS: "Playlists",
    Type.RADIOS: "Radios",
    Type.YEARS: "Years",
    Type.ALL: "All albums",
    Type.COMPILATIONS: "Compilations"
}
