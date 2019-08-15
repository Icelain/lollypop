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

from gi.repository import Gio

from random import shuffle

from lollypop.objects_album import Album
from lollypop.logger import Logger
from lollypop.define import App, Repeat
from lollypop.utils import get_network_available


class InternalProvider:
    """
        Internal lollypop provider for SimilarsPlayer
    """

    def __init__(self):
        """
            Init provider
        """
        pass

    def get_similar_artists(self, artist, cancellable):
        """
            Search similar artists
            @param artist as str
            @param cancellable as Gio.Cancellable
            @return [(str, str)] : list of (artist, cover_uri)
        """
        artists = []
        (artist_id, db_name) = App().artists.get_id(artist)
        album_ids = App().albums.get_ids([artist_id], [])
        if album_ids:
            genre_ids = App().albums.get_genre_ids(album_ids[0])
            artist_ids = App().artists.get(genre_ids)
        for (artist_id, name, sortname) in artist_ids:
            artists.append((name, name, None))
        return artists

    def get_artist_id(self, artist_name, cancellable):
        return artist_name


class SimilarsPlayer:
    """
        Manage playback when going to end
    """

    def __init__(self):
        """
            Init player
        """
        self.__cancellable = Gio.Cancellable()
        self.connect("next-changed", self.__on_next_changed)

#######################
# PRIVATE             #
#######################
    def __populate(self, providers, cancellable):
        """
            Populate view with providers
            @param providers as {}
            @param cancellable as Gio.Cancellable
        """
        for provider in providers.keys():
            artist = providers[provider]
            App().task_helper.run(provider.get_artist_id,
                                  artist, cancellable,
                                  callback=(self.__on_get_artist_id,
                                            providers, provider, cancellable))
            del providers[provider]
            break

    def __add_a_new_album(self, similar_artist_ids):
        """
            Add a new album to playback
            @param similar_artist_ids as [int]
            @return True if added
        """
        # Get an album
        album_ids = App().albums.get_ids(similar_artist_ids, [])
        shuffle(album_ids)
        while album_ids:
            album_id = album_ids.pop(0)
            if album_id not in self.album_ids:
                self.add_album(Album(album_id))
                return True
        return False

    def __get_artist_ids(self, artists):
        """
            Get a valid artist id from list
            @param artists as [str]
            @return artist_id as int
        """
        similar_artist_ids = []
        for (spotify_id, artist, cover_uri) in artists:
            similar_artist_id = App().artists.get_id_for_escaped_string(
                artist.lower())
            if similar_artist_id is not None:
                if App().artists.get_albums([similar_artist_id]):
                    similar_artist_ids.append(similar_artist_id)
        return similar_artist_ids

    def __on_next_changed(self, player):
        """
            Add a new album if playback finished and wanted by user
        """
        self.__cancellable.cancel()
        self.__cancellable = Gio.Cancellable()
        # Check if we need to add a new album
        if App().settings.get_enum("repeat") == Repeat.AUTO and\
                player.next_track.id is None and\
                player.current_track.id is not None and\
                player.current_track.id >= 0 and\
                Gio.NetworkMonitor.get_default().get_network_available() and\
                player.current_track.artist_ids:
            artist_id = player.current_track.artist_ids[0]
            artist_name = App().artists.get_name(artist_id)
            providers = {}
            if get_network_available("SPOTIFY"):
                providers[App().spotify] = artist_name
            if App().lastfm is not None and get_network_available("LASTFM"):
                providers[App().lastfm] = artist_name
            providers[InternalProvider()] = artist_name
            self.__populate(providers, self.__cancellable)

    def __on_get_artist_id(self, artist_id, providers, provider, cancellable):
        """
            Get similars
            @param artist_id as str
            @param providers as {}
            @param provider as SpotifyHelper/LastFM
            @param cancellable as Gio.Cancellable
        """
        if artist_id is None:
            if providers.keys():
                self.__populate(providers, cancellable)
        else:
            App().task_helper.run(provider.get_similar_artists,
                                  artist_id, cancellable,
                                  callback=(self.__on_similar_artists,
                                            providers, cancellable))

    def __on_similar_artists(self, artists, providers, cancellable):
        """
            Add one album from artist to player
            @param artists as [str]
            @param providers as {}
            @param cancellable as Gio.Cancellable
        """
        if cancellable.is_cancelled():
            return
        similar_artist_ids = self.__get_artist_ids(artists)
        added = False
        if similar_artist_ids:
            Logger.info("Found a similar artist: artists")
            if self.albums:
                added = self.__add_a_new_album(similar_artist_ids)
        if not added:
            self.__populate(providers, cancellable)
