# Copyright (c) 2014-2019 Cedric Bellegarde <cedric.bellegarde@adishatz.org>
# Copyright (c) 2015 Jean-Philippe Braun <eon@patapon.info>
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

from lollypop.define import App, StorageType
from lollypop.objects_track import Track
from lollypop.objects import Base


class Disc:
    """
        Represent an album disc
    """

    def __init__(self, album, disc_number, disallow_ignored_tracks):
        self.db = App().albums
        self.__tracks = []
        self.__album = album
        self.__number = disc_number
        self.__disallow_ignored_tracks = disallow_ignored_tracks

    def set_tracks(self, tracks):
        """
            Set disc tracks
            @param tracks as [Track]
        """
        self.__tracks = tracks

    @property
    def number(self):
        """
            Get disc number
        """
        return self.__number

    @property
    def album(self):
        """
            Get disc album
            @return Album
        """
        return self.__album

    @property
    def track_ids(self):
        """
            Get disc track ids
            @return [int]
        """
        return [track.id for track in self.tracks]

    @property
    def track_uris(self):
        """
            Get disc track uris
            @return [str]
        """
        return [track.uri for track in self.tracks]

    @property
    def tracks(self):
        """
            Get disc tracks
            @return [Track]
        """
        if not self.__tracks and self.album.id is not None:
            self.__tracks = [Track(track_id, self.album)
                             for track_id in self.db.get_disc_track_ids(
                self.album.id,
                self.album.genre_ids,
                self.album.artist_ids,
                self.number,
                self.__disallow_ignored_tracks)]
        return self.__tracks


class Album(Base):
    """
        Represent an album
    """
    DEFAULTS = {"name": "",
                "artists": [],
                "artist_ids": [],
                "year": None,
                "timestamp": 0,
                "uri": "",
                "tracks_count": 1,
                "duration": 0,
                "popularity": 0,
                "mtime": 1,
                "synced": False,
                "loved": False,
                "storage_type": 0,
                "mb_album_id": None}

    def __init__(self, album_id=None, genre_ids=[], artist_ids=[],
                 disallow_ignored_tracks=False):
        """
            Init album
            @param album_id as int
            @param genre_ids as [int]
            @param disallow_ignored_tracks as bool
        """
        Base.__init__(self, App().albums)
        self.id = album_id
        self.genre_ids = genre_ids
        self._tracks = []
        self._discs = []
        self.__disallow_ignored_tracks = disallow_ignored_tracks
        self.__one_disc = None
        # Use artist ids from db else
        if artist_ids:
            self.artist_ids = artist_ids

    def clone(self, disallow_ignored_tracks):
        """
            Clone album
            @param disallow_ignored_tracks as bool
        """
        album = Album(self.id, self.genre_ids,
                      self.artist_ids, disallow_ignored_tracks)
        if not disallow_ignored_tracks:
            album.set_tracks(self.tracks)
        return album

    def set_discs(self, discs):
        """
            Set album discs
            @param discs as [Disc]
        """
        self._discs = discs

    def set_tracks(self, tracks):
        """
            Set album tracks (cloned tracks)
            @param tracks as [Track]
        """
        self._tracks = []
        for track in tracks:
            new_track = Track(track.id, self)
            self._tracks.append(new_track)

    def append_tracks(self, tracks):
        """
            Append tracks to albums
            @param tracks as [Track]
        """
        cloned = []
        for track in tracks:
            cloned.append(Track(track.id, self))
        self._tracks += cloned

    def insert_tracks(self, tracks, position):
        """
            Insert tracks at position
        """
        for track in tracks:
            clone = Track(track.id, self)
            self._tracks.insert(position, clone)
            position += 1

    def remove_track(self, track):
        """
            Remove track from album
            @param track as Track
            @return True if album empty
        """
        if track in self.tracks:
            self._tracks.remove(track)
        return len(self._tracks) == 0

    def clear_tracks(self):
        """
            Clear album tracks
        """
        self._tracks = []

    def disc_names(self, disc):
        """
            Disc names
            @param disc as int
            @return disc names as [str]
        """
        return self.db.get_disc_names(self.id, disc)

    def set_loved(self, loved):
        """
            Mark album as loved
            @param loved as bool
        """
        if self.id >= 0:
            App().albums.set_loved(self.id, loved)
            self.loved = loved

    def set_uri(self, uri):
        """
            Set album uri
            @param uri as str
        """
        if self.id >= 0:
            App().albums.set_uri(self.id, uri)
        self.uri = uri

    def get_track(self, track_id):
        """
            Get track
            @param track_id as int
            @return Track
        """
        for track in self.tracks:
            if track.id == track_id:
                return track
        return Track()

    def save(self, save):
        """
            Save album to collection
            @param save as bool
        """
        if save:
            App().albums.set_storage_type(self.id, StorageType.SAVED)
        else:
            App().albums.set_storage_type(self.id, StorageType.EPHEMERAL)
        for track in self.tracks:
            track.save(save)
        self.reset("mtime")
        for artist_id in self.artist_ids:
            App().scanner.emit("artist-updated", artist_id, save)
        App().scanner.emit("album-updated", self.id, save)

    @property
    def is_web(self):
        """
            True if track is a web track
            @return bool
        """
        return not self.storage_type & StorageType.COLLECTION

    @property
    def synced(self):
        """
            Get synced state
            Remove from cache
            @return int
        """
        return App().albums.get_synced(self.id)

    @property
    def title(self):
        """
            Get album name
            @return str
        """
        return self.name

    @property
    def track_ids(self):
        """
            Get album track ids
            @return [int]
        """
        return [track.id for track in self.tracks]

    @property
    def track_uris(self):
        """
            Get album track uris
            @return [str]
        """
        return [track.uri for track in self.tracks]

    @property
    def tracks(self):
        """
            Get album tracks
            @return [Track]
        """
        if not self._tracks and self.id is not None:
            for disc in self.discs:
                self._tracks += disc.tracks
        return self._tracks

    @property
    def one_disc(self):
        """
            Get album as one disc
            @return Disc
        """
        if self.__one_disc is None:
            tracks = self.tracks
            self.__one_disc = Disc(self, 0, self.__disallow_ignored_tracks)
            self.__one_disc.set_tracks(tracks)
        return self.__one_disc

    @property
    def discs(self):
        """
            Get albums discs
            @return [Disc]
        """
        if not self._discs:
            disc_numbers = self.db.get_discs(self.id, self.genre_ids)
            self._discs = [Disc(self, number, self.__disallow_ignored_tracks)
                           for number in disc_numbers]
        return self._discs