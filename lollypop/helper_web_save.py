# Copyright (c) 2014-2017 Cedric Bellegarde <cedric.bellegarde@adishatz.org>
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

from gi.repository import GLib, GObject

from time import time
import json

from lollypop.logger import Logger
from lollypop.utils import emit_signal
from lollypop.utils import get_lollypop_album_id, get_lollypop_track_id
from lollypop.objects_album import Album
from lollypop.define import App, Type
from lollypop.collection_item import CollectionItem


class SaveWebHelper(GObject.Object):
    """
       Web helper for saving Spotify payloads
    """

    __gsignals__ = {
        "match-album": (GObject.SignalFlags.RUN_FIRST, None, (int, int)),
        "match-track": (GObject.SignalFlags.RUN_FIRST, None, (int, int)),
        "match-artist": (GObject.SignalFlags.RUN_FIRST, None, (int, int)),
        "finished": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self):
        """
            Init helper
        """
        GObject.Object.__init__(self)

    def save_track_payload_to_db(self, payload, item,
                                 storage_type, notify, cancellable):
        """
            Save track to DB
            @param payload as {}
            @param item as CollectionItem
            @param storage_type as StorageType
            @param cancellable as Gio.Cancellable
            @param notify as bool
        """
        lp_track_id = get_lollypop_track_id(payload["name"],
                                            payload["artists"],
                                            item.year,
                                            item.album_name)
        item.track_id = App().tracks.get_id_for_lp_track_id(lp_track_id)
        if item.track_id < 0:
            self.__save_track(payload, item, storage_type)
        if notify:
            emit_signal(self, "match-track", item.track_id, storage_type)

    def save_album_payload_to_db(self, payload, storage_type,
                                 notify, cancellable):
        """
            Save album to DB
            @param payload as {}
            @param storage_type as StorageType
            @param notify as bool
            @param cancellable as Gio.Cancellable
            @return CollectionItem/None
        """
        lp_album_id = get_lollypop_album_id(payload["name"],
                                            payload["artists"],
                                            payload["date"])
        album_id = App().albums.get_id_for_lp_album_id(lp_album_id)
        if album_id >= 0:
            album = Album(album_id)
            if notify:
                self.save_artwork(album,
                                  payload["artwork-uri"],
                                  cancellable)
                emit_signal(self, "match-album", album_id, storage_type)
            return album.collection_item
        item = self.__save_album(payload, storage_type)
        album = Album(item.album_id)
        if notify:
            self.save_artwork(album,
                              payload["artwork-uri"],
                              cancellable)
            emit_signal(self, "match-album", album.id, storage_type)
        return item

    def save_artwork(self, obj, cover_uri, cancellable):
        """
            Save artwork for obj
            @param obj as Album/Track
            @param cover_uri/mbid as str
            @param cancellable as Gio.Cancellable
        """
        if not cover_uri:
            return
        try:
            if cancellable.is_cancelled():
                return
            if isinstance(obj, Album):
                album = obj
            else:
                album = obj.album
            if App().art.get_album_artwork_uri(album) is None:
                # We need to get URI from mbid
                if not cover_uri.startswith("http"):
                    cover_uri = self.__get_cover_art_uri(cover_uri,
                                                         cancellable)
                if cover_uri is None:
                    return
                (status, data) = App().task_helper.load_uri_content_sync(
                                                        cover_uri,
                                                        cancellable)
                if status:
                    App().art.save_album_artwork(album, data)
        except Exception as e:
            Logger.error(
                "SaveWebHelper::save_artwork(): %s", e)

#######################
# PRIVATE             #
#######################
    def __get_cover_art_uri(self, mbid, cancellable):
        """
            Get cover art URI for mbid
            @param mbid as str
            @param cancellable as Gio.Cancellable
            @return str/None
        """
        try:
            uri = "http://coverartarchive.org/release/%s" % mbid
            (status, data) = App().task_helper.load_uri_content_sync(uri, None)
            if status:
                decode = json.loads(data.decode("utf-8"))
                for image in decode["images"]:
                    if not image["front"]:
                        continue
                    return image["image"]
        except Exception as e:
            Logger.error(e)
            Logger.error(
                "SaveWebHelper::__get_cover_art_uri(): %s", data)
        return None

    def __save_album(self, payload, storage_type):
        """
            Save album payload to DB
            @param payload as {}
            @param storage_type as StorageType
            @return CollectionItem
        """
        album_artists = payload["artists"]
        album_artists = ";".join(album_artists)
        album_name = payload["name"]
        mtime = int(time())
        track_count = payload["track-count"]
        mb_album_id = payload["mbid"]
        uri = payload["uri"]
        Logger.debug("SaveWebHelper::save_album(): %s - %s",
                     album_artists, album_name)
        item = CollectionItem(album_name=album_name)
        App().scanner.save_album(
                        item,
                        album_artists,
                        "", "", album_name,
                        mb_album_id, uri, 0, 0, 0,
                        # HACK: Keep total tracks in sync int field
                        track_count, mtime, storage_type)
        App().albums.add_genre(item.album_id, Type.WEB)
        try:
            release_date = payload["date"]
            dt = GLib.DateTime.new_from_iso8601(release_date,
                                                GLib.TimeZone.new_local())
            item.timestamp = dt.to_unix()
            item.year = dt.get_year()
        except:
            pass
        return item

    def __save_track(self, payload, item, storage_type):
        """
            Save track payload to DB
            @param payload as {}
            @param storage_type as StorageType
            @return track_id as int
        """
        title = payload["name"]
        _artists = []
        for artist in payload["artists"]:
            _artists.append(artist)
        Logger.debug("SaveWebHelper::save_track(): %s - %s",
                     _artists, title)
        # Translate to tag value
        artists = ";".join(_artists)
        discnumber = int(payload["discnumber"])
        discname = ""
        tracknumber = int(payload["tracknumber"])
        duration = payload["duration"]
        mtime = int(time())
        uri = payload["uri"]
        mb_track_id = payload["mbid"]
        App().scanner.save_track(
                   item, None, artists, "", "",
                   uri, title, duration, tracknumber, discnumber,
                   discname, item.year, item.timestamp, mtime, 0, 0, 0, 0,
                   mb_track_id, 0, storage_type)
