# Copyright (c) 2014-2018 Cedric Bellegarde <cedric.bellegarde@adishatz.org>
# Copyright (c) 2019 Jordi Romera <jordiromera@users.sourceforge.net>
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

from gi.repository import GLib, GObject, Gio

from gi.repository.Gio import FILE_ATTRIBUTE_STANDARD_NAME, \
                              FILE_ATTRIBUTE_STANDARD_TYPE, \
                              FILE_ATTRIBUTE_STANDARD_IS_HIDDEN,\
                              FILE_ATTRIBUTE_TIME_CHANGED,\
                              FILE_ATTRIBUTE_TIME_MODIFIED

from gettext import gettext as _
from threading import Thread
from time import time, sleep

from lollypop.inotify import Inotify
from lollypop.define import App, Type, ScanType
from lollypop.objects import Track, Album
from lollypop.sqlcursor import SqlCursor
from lollypop.tagreader import TagReader
from lollypop.logger import Logger
from lollypop.database_history import History
from lollypop.utils import is_audio, is_pls, get_mtime, profile


SCAN_QUERY_INFO = "{},{},{},{},{}".format(FILE_ATTRIBUTE_STANDARD_NAME,
                                          FILE_ATTRIBUTE_STANDARD_TYPE,
                                          FILE_ATTRIBUTE_STANDARD_IS_HIDDEN,
                                          FILE_ATTRIBUTE_TIME_CHANGED,
                                          FILE_ATTRIBUTE_TIME_MODIFIED)


class CollectionScanner(GObject.GObject, TagReader):
    """
        Scan user music collection
    """
    __gsignals__ = {
        "scan-finished": (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
        "artist-updated": (GObject.SignalFlags.RUN_FIRST, None, (int, bool)),
        "genre-updated": (GObject.SignalFlags.RUN_FIRST, None, (int, bool)),
        "album-updated": (GObject.SignalFlags.RUN_FIRST, None, (int, bool))
    }

    def __init__(self):
        """
            Init collection scanner
        """
        GObject.GObject.__init__(self)
        TagReader.__init__(self)

        self.__thread = None
        self.__history = None
        self.__disable_compilations = True
        if App().settings.get_value("auto-update"):
            self.__inotify = Inotify()
        else:
            self.__inotify = None
        App().albums.update_max_count()

    def update(self, scan_type, uris=[]):
        """
            Update database
            @param scan_type as ScanType
            @param uris as [str]
        """
        # Stop previous scan
        if self.is_locked():
            self.stop()
            GLib.timeout_add(250, self.update, scan_type, uris)
        else:
            self.__disable_compilations = not App().settings.get_value(
                "show-compilations")

            if scan_type in [ScanType.FULL, ScanType.QUICK]:
                uris = App().settings.get_music_uris()
            if not uris:
                return
            # Register to progressbar
            App().window.container.progress.add(self)
            App().window.container.progress.set_fraction(0, self)
            # Launch scan in a separate thread
            self.__thread = Thread(target=self.__scan, args=(scan_type, uris))
            self.__thread.daemon = True
            self.__thread.start()

    def is_locked(self):
        """
            Return True if db locked
        """
        return self.__thread is not None and self.__thread.isAlive()

    def stop(self):
        """
            Stop scan
        """
        self.__thread = None

#######################
# PRIVATE             #
#######################
    def __update_progress(self, current, total):
        """
            Update progress bar status
            @param scanned items as int, total items as int
        """
        # Previous code (<= 0.9.910) was reading mtime in this loop
        # Since we are looping faster, seems it's makes python
        # lagging. If someone has a better idea
        if current % 1000:
            sleep(0.00001)
        GLib.idle_add(App().window.container.progress.set_fraction,
                      current / total,
                      self)

    def __finish(self, modifications):
        """
            Notify from main thread when scan finished
            @param modifications as bool
        """
        App().window.container.progress.set_fraction(1.0, self)
        self.stop()
        self.emit("scan-finished", modifications)
        # Update max count value
        App().albums.update_max_count()
        if App().settings.get_value("artist-artwork"):
            App().art.cache_artists_info()

    def __add_monitor(self, dirs):
        """
            Monitor any change in a list of directory
            @param dirs as str or list of directory to be monitored
        """
        if self.__inotify is None:
            return
        # Add monitors on dirs
        for d in dirs:
            # Handle a stop request
            if self.__thread is None:
                break
            if d.startswith("file://"):
                self.__inotify.add_monitor(d)

    @profile
    def __get_objects_for_uris(self, scan_type, uris):
        """
            Get all tracks and dirs in uris
            @param scan_type as ScanType
            @param uris as string
            @return (tracks [mtimes: int, uri: str], dirs as [uri: str])
        """
        files = []
        dirs = []
        walk_uris = list(uris)
        if scan_type == ScanType.QUICK:
            max_mtime = App().albums.get_max_mtime()
        while walk_uris:
            uri = walk_uris.pop(0)
            try:
                # Directly add files, walk through directories
                f = Gio.File.new_for_uri(uri)
                info = f.query_info(SCAN_QUERY_INFO,
                                    Gio.FileQueryInfoFlags.NONE,
                                    None)
                if info.get_file_type() == Gio.FileType.DIRECTORY:
                    dirs.append(uri)
                    infos = f.enumerate_children(SCAN_QUERY_INFO,
                                                 Gio.FileQueryInfoFlags.NONE,
                                                 None)
                    for info in infos:
                        f = infos.get_child(info)
                        child_uri = f.get_uri()
                        if info.get_is_hidden():
                            continue
                        elif info.get_file_type() == Gio.FileType.DIRECTORY:
                            dirs.append(child_uri)
                            walk_uris.append(child_uri)
                        elif self.__scan_to_handle(f):
                            mtime = get_mtime(info)
                            if scan_type == ScanType.QUICK:
                                if mtime > max_mtime:
                                    files.append((mtime, child_uri))
                            else:
                                files.append((mtime, child_uri))
                elif self.__scan_to_handle(f):
                    mtime = get_mtime(info)
                    if scan_type == ScanType.QUICK:
                        if mtime > max_mtime:
                            files.append((mtime, uri))
                    else:
                        files.append((mtime, uri))
            except Exception as e:
                Logger.error("CollectionScanner::__get_objects_for_uris(): %s"
                             % e)
        files.sort(reverse=True)
        return (files, dirs)

    @profile
    def __scan(self, scan_type, uris):
        """
            Scan music collection for music files
            @param scan_type as ScanType
            @param uris as [str]
            @thread safe
        """
        if self.__history is None:
            self.__history = History()

        (files, dirs) = self.__get_objects_for_uris(scan_type, uris)

        if scan_type == ScanType.NEW_FILES:
            full_db_uris = App().tracks.get_uris(uris)
        elif scan_type == ScanType.QUICK:
            full_db_uris = [uri for (mtime, uri) in files]
        elif scan_type == ScanType.EPHEMERAL:
            full_db_uris = uris
        else:
            full_db_uris = App().tracks.get_uris()
        new_tracks = self.__scan_files(files, full_db_uris, scan_type)

        self.__add_monitor(dirs)

        GLib.idle_add(self.__finish,
                      new_tracks and scan_type != ScanType.EPHEMERAL)

        if scan_type == ScanType.EPHEMERAL and self.__thread is not None:
            self.__play_new_tracks(new_tracks)

        del self.__history
        self.__history = None

    def __scan_to_handle(self, f):
        """
            Check if file has to be handle by scanner
            @param f as Gio.File
            @return bool
        """
        try:
            # Scan file
            if is_pls(f):
                # Handle playlist
                App().playlists.import_tracks(f)
            elif is_audio(f):
                return True
            else:
                Logger.debug("Not detected as a music file: %s" % f.get_uri())
        except Exception as e:
            Logger.error("CollectionScanner::__scan_to_handle(): %s" % e)
        return False

    def __scan_add(self, uri, mtime):
        """
            Add audio file to database
            @param uri as str
            @param mtime as float
        """
        try:
            Logger.debug("Adding file: %s" % uri)
            self.__add2db(uri, mtime)
            SqlCursor.allow_thread_execution(App().db)
        except Exception as e:
            Logger.error("CollectionScanner::__scan_add(add): "
                         "%s, %s" % (e, uri))

    def __scan_del(self, uri):
        """
            Delete file from DB
            @param uri as str
        """
        try:
            self.__del_from_db(uri)
            SqlCursor.allow_thread_execution(App().db)
        except Exception as e:
            Logger.error("CollectionScanner::__scan_del: %s" % e)

    @profile
    def __scan_files(self, files, full_db_uris, scan_type):
        """
            Scan music collection for new audio files
            @param files as [str]
            @param full_db_uris as [str]
            @param scan_type as ScanType
            @return new track uris as [str]
            @thread safe
        """
        SqlCursor.add(App().db)
        i = 0
        new_tracks = []
        # Get mtime of all tracks to detect which has to be updated
        db_mtimes = App().tracks.get_mtimes()
        count = len(files) + len(full_db_uris)
        try:
            # We delete missing tracks from DB as soon as possible
            # This allow metadata to be saved in history for example
            # if user moved an album in collection
            uris = [uri for (mtime, uri) in files]
            db_uris = []
            for uri in full_db_uris:
                # Handle a stop request
                if self.__thread is None:
                    raise Exception("Scan cancelled")
                if uri in uris:
                    db_uris.append(uri)
                else:
                    self.__scan_del(uri)
                i += 1
                self.__update_progress(i, count)
            # Scan new files
            while files:
                # Handle a stop request
                if self.__thread is None:
                    raise Exception("Scan cancelled")
                try:
                    (mtime, uri) = files.pop(0)
                    already_in_db = uri in db_uris
                    if already_in_db:
                        db_uris.remove(uri)
                    if mtime > db_mtimes.get(uri, 0):
                        if already_in_db:
                            self.__scan_del(uri)
                        # If not saved, use 0 as mtime, easy delete on quit
                        if scan_type == ScanType.EPHEMERAL:
                            mtime = 0
                        # Do not use mtime if not intial scan
                        elif db_mtimes:
                            mtime = int(time())
                        self.__scan_add(uri, mtime)
                        new_tracks.append(uri)
                except Exception as e:
                    Logger.error(
                               "CollectionScanner:: __scan_files: % s" % e)
                i += 1
                self.__update_progress(i, count)
        except Exception as e:
            Logger.warning("CollectionScanner:: __scan_files: % s" % e)
        SqlCursor.commit(App().db)
        SqlCursor.remove(App().db)
        return new_tracks

    def __add2db(self, uri, mtime):
        """
            Add new file(or update one) to db with information
            @param uri as string
            @param mtime as int
            @return track id as int
            @warning, be sure SqlCursor is available for App().db
        """
        f = Gio.File.new_for_uri(uri)
        Logger.debug("CollectionScanner::add2db(): Read tags")
        info = self.get_info(uri)
        tags = info.get_tags()
        name = f.get_basename()
        title = self.get_title(tags, name)
        version = self.get_version(tags)
        artists = self.get_artists(tags)
        composers = self.get_composers(tags)
        performers = self.get_performers(tags)
        a_sortnames = self.get_artist_sortnames(tags)
        aa_sortnames = self.get_album_artist_sortnames(tags)
        album_artists = self.get_album_artists(tags)
        album_name = self.get_album_name(tags)
        mb_album_id = self.get_mb_album_id(tags)
        mb_track_id = self.get_mb_track_id(tags)
        genres = self.get_genres(tags)
        discnumber = self.get_discnumber(tags)
        discname = self.get_discname(tags)
        tracknumber = self.get_tracknumber(tags, name)
        (year, timestamp) = self.get_original_year(tags)
        if year is None:
            (year, timestamp) = self.get_year(tags)
        duration = int(info.get_duration() / 1000000000)

        if version != "":
            title += " (%s)" % version

        # If no artists tag, use album artist
        if artists == "":
            artists = album_artists
        # if artists is always null, no album artists too,
        # use composer/performer
        if artists == "":
            artists = performers
            album_artists = composers
            if artists == "":
                artists = album_artists
            if artists == "":
                artists = _("Unknown")

        Logger.debug("CollectionScanner::add2db(): Restore stats")
        # Restore stats
        (track_pop, track_rate, track_ltime, album_mtime,
         track_loved, album_loved, album_pop, album_rate) = self.__history.get(
            name, duration)
        # If nothing in stats, use track mtime
        if album_mtime == 0:
            album_mtime = mtime

        Logger.debug("CollectionScanner::add2db(): Add artists %s" % artists)
        artist_ids = self.add_artists(artists, a_sortnames)

        Logger.debug("CollectionScanner::add2db(): "
                     "Add album artists %s" % album_artists)
        album_artist_ids = self.add_album_artists(album_artists, aa_sortnames)

        # User does not want compilations
        if self.__disable_compilations and not album_artist_ids:
            album_artist_ids = artist_ids

        missing_artist_ids = list(set(album_artist_ids) - set(artist_ids))
        # https://github.com/gnumdk/lollypop/issues/507#issuecomment-200526942
        # Special case for broken tags
        # Can't do more because don't want to break split album behaviour
        if len(missing_artist_ids) == len(album_artist_ids):
            artist_ids += missing_artist_ids

        Logger.debug("CollectionScanner::add2db(): Add album: "
                     "%s, %s" % (album_name, album_artist_ids))
        album_id = self.add_album(album_name, mb_album_id,
                                  album_artist_ids,
                                  uri, album_loved, album_pop,
                                  album_rate, mtime)

        genre_ids = self.add_genres(genres)

        # Add track to db
        Logger.debug("CollectionScanner::add2db(): Add track")
        track_id = App().tracks.add(title, uri, duration,
                                    tracknumber, discnumber, discname,
                                    album_id, year, timestamp, track_pop,
                                    track_rate, track_loved, track_ltime,
                                    mtime, mb_track_id)
        Logger.debug("CollectionScanner::add2db(): Update track")
        self.__update_track(track_id, artist_ids, genre_ids)
        Logger.debug("CollectionScanner::add2db(): Update album")
        SqlCursor.commit(App().db)
        self.__update_album(album_id, album_artist_ids,
                            genre_ids, year, timestamp)
        SqlCursor.commit(App().db)
        for genre_id in genre_ids:
            GLib.idle_add(self.emit, "genre-updated", genre_id, True)
        return track_id

    def __del_from_db(self, uri):
        """
            Delete track from db
            @param uri as str
        """
        try:
            f = Gio.File.new_for_uri(uri)
            name = f.get_basename()
            track_id = App().tracks.get_id_by_uri(uri)
            album_id = App().tracks.get_album_id(track_id)
            genre_ids = App().tracks.get_genre_ids(track_id)
            album_artist_ids = App().albums.get_artist_ids(album_id)
            artist_ids = App().tracks.get_artist_ids(track_id)
            popularity = App().tracks.get_popularity(track_id)
            rate = App().tracks.get_rate(track_id)
            ltime = App().tracks.get_ltime(track_id)
            mtime = App().tracks.get_mtime(track_id)
            loved_track = App().tracks.get_loved(track_id)
            duration = App().tracks.get_duration(track_id)
            album_popularity = App().albums.get_popularity(album_id)
            album_rate = App().albums.get_rate(album_id)
            loved_album = App().albums.get_loved(album_id)
            uri = App().tracks.get_uri(track_id)
            self.__history.add(name, duration, popularity, rate,
                               ltime, mtime, loved_track, loved_album,
                               album_popularity, album_rate)
            App().tracks.remove(track_id)
            App().tracks.clean(track_id)
            cleaned = App().albums.clean(album_id)
            if cleaned:
                SqlCursor.commit(App().db)
                GLib.idle_add(self.emit, "album-updated",
                              album_id, True)
            for artist_id in album_artist_ids + artist_ids:
                cleaned = App().artists.clean(artist_id)
                # Force update even if not cleaned as artist may
                # have been removed from a selected genre
                GLib.idle_add(self.emit, "artist-updated",
                              artist_id, False)
            for genre_id in genre_ids:
                cleaned = App().genres.clean(genre_id)
                if cleaned:
                    SqlCursor.commit(App().db)
                    GLib.idle_add(self.emit, "genre-updated",
                                  genre_id, False)
        except Exception as e:
            Logger.error("CollectionScanner::__del_from_db: %s" % e)

    def __update_album(self, album_id, artist_ids, genre_ids, year, timestamp):
        """
            Update album artists based on album-artist and artist tags
            This code auto handle compilations: empty "album artist" with
            different artists
            @param album id as int
            @param artist ids as [int]
            @param genre ids as [int]
            @param year as int
            @param timestmap as int
            @commit needed
        """
        album_artist_ids = []
        add = True
        # Set artist ids based on content
        if not artist_ids:
            new_artist_ids = App().albums.calculate_artist_ids(album_id)
            current_artist_ids = App().albums.get_artist_ids(album_id)
            if new_artist_ids != current_artist_ids:
                album_artist_ids = new_artist_ids
                if Type.COMPILATIONS in new_artist_ids:
                    add = False
                    album_artist_ids = current_artist_ids
                else:
                    album_artist_ids = new_artist_ids
                App().albums.set_artist_ids(album_id, new_artist_ids)
        # Update UI based on previous artist calculation
        for artist_id in album_artist_ids:
            GLib.idle_add(self.emit, "artist-updated", artist_id, add)
        # Update album genres
        for genre_id in genre_ids:
            App().albums.add_genre(album_id, genre_id)

        # Update year based on tracks
        year = App().tracks.get_year_for_album(album_id)
        App().albums.set_year(album_id, year)
        timestamp = App().tracks.get_timestamp_for_album(album_id)
        App().albums.set_timestamp(album_id, timestamp)

    def __update_track(self, track_id, artist_ids, genre_ids):
        """
            Set track artists/genres
            @param track id as int
            @param artist ids as [int]
            @param genre ids as [int]
            @param mtime as int
            @param popularity as int
            @commit needed
        """
        # Set artists/genres for track
        for artist_id in artist_ids:
            App().tracks.add_artist(track_id, artist_id)
        for genre_id in genre_ids:
            App().tracks.add_genre(track_id, genre_id)

    def __play_new_tracks(self, uris):
        """
            Play new tracks
            @param uri as [str]
        """
        # First get tracks
        tracks = []
        for uri in uris:
            track_id = App().tracks.get_id_by_uri(uri)
            tracks.append(Track(track_id))
        # Then get album ids
        album_ids = {}
        for track in tracks:
            if track.album.id in album_ids.keys():
                album_ids[track.album.id].append(track)
            else:
                album_ids[track.album.id] = [track]
        # Create albums with tracks
        play = True
        for album_id in album_ids.keys():
            album = Album(album_id)
            album.set_tracks(album_ids[album_id])
            if play:
                App().player.play_album(album)
            else:
                App().player.add_album(album)
