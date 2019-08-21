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

from gi.repository import Gtk, Gio, GLib, GObject, Pango

from gettext import gettext as _

from lollypop.view_tracks import TracksView
from lollypop.define import ArtSize, App, ViewType, MARGIN_SMALL, Type
from lollypop.define import ArtBehaviour, StorageType
from lollypop.utils import popup_widget
from lollypop.helper_gestures import GesturesHelper


class AlbumRow(Gtk.ListBoxRow):
    """
        Album row
    """

    __gsignals__ = {
        "populated": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    __MARGIN = 4

    def get_best_height(widget):
        """
            Helper to pass object it's height request
            @param widget as Gtk.Widget
        """
        ctx = widget.get_pango_context()
        layout = Pango.Layout.new(ctx)
        layout.set_text("a", 1)
        font_height = int(AlbumRow.__MARGIN * 2 +
                          2 * layout.get_pixel_size()[1])
        cover_height = AlbumRow.__MARGIN * 2 + ArtSize.SMALL
        if font_height > cover_height:
            return font_height + 2
        else:
            return cover_height + 2

    def __init__(self, album, height, view_type, reveal):
        """
            Init row widgets
            @param album as Album
            @param height as int
            @param view_type as ViewType
            @param reveal as bool
            @param parent as AlbumListView
        """
        Gtk.ListBoxRow.__init__(self)
        self.__view_type = view_type
        self.__revealer = None
        self.__artwork = None
        self.__album = album
        self.__cancellable = Gio.Cancellable()
        self.set_sensitive(False)
        self.set_property("height-request", height)
        self.connect("destroy", self.__on_destroy)
        self.__tracks_view = TracksView(self.__album, None,
                                        Gtk.Orientation.VERTICAL,
                                        self.__view_type)
        self.__tracks_view.connect("populated", self.__on_tracks_populated)
        self.__tracks_view.show()
        if reveal or self.__view_type & ViewType.PLAYLISTS:
            self.populate()
            self.__revealer.set_reveal_child(True)
            self.__tracks_view.populate()

    def populate(self):
        """
            Populate widget content
        """
        if self.__artwork is not None:
            return
        self.__artwork = Gtk.Image.new()
        App().art_helper.set_frame(self.__artwork, "small-cover-frame",
                                   ArtSize.SMALL, ArtSize.SMALL)
        self.__artwork.set_margin_start(self.__MARGIN)
        # Little hack: we do not set margin_bottom because already set by
        # get_best_height(): we are Align.FILL
        # This allow us to not Align.CENTER row_widget and not jump up
        # and down on reveal()
        self.__artwork.set_margin_top(self.__MARGIN)
        self.get_style_context().add_class("albumrow")
        self.set_sensitive(True)
        self.set_property("has-tooltip", True)
        self.connect("query-tooltip", self.__on_query_tooltip)
        grid = Gtk.Grid()
        grid.set_column_spacing(8)
        if self.__album.artists:
            artists = GLib.markup_escape_text(", ".join(self.__album.artists))
        else:
            artists = _("Compilation")
        self.__artist_label = Gtk.Label.new("<b>%s</b>" % artists)
        self.__artist_label.set_use_markup(True)
        self.__artist_label.set_hexpand(True)
        self.__artist_label.set_property("halign", Gtk.Align.START)
        self.__artist_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.__title_label = Gtk.Label.new(self.__album.name)
        self.__title_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.__title_label.set_property("halign", Gtk.Align.START)
        self.__title_label.get_style_context().add_class("dim-label")
        self.__action_button = None
        if self.__view_type & (ViewType.PLAYBACK | ViewType.PLAYLISTS):
            self.__action_button = Gtk.Button.new_from_icon_name(
                "list-remove-symbolic",
                Gtk.IconSize.MENU)
            self.__action_button.set_tooltip_text(
                _("Remove from playlist"))
        elif self.__album.storage_type & StorageType.EPHEMERAL:
            self.__action_button = Gtk.Button.new_from_icon_name(
                "document-save-symbolic",
                Gtk.IconSize.MENU)
            self.__action_button.set_tooltip_text(_("Save in collection"))
        elif self.__view_type & ViewType.SEARCH:
            self.__action_button = Gtk.Button.new_from_icon_name(
                    'avatar-default-symbolic',
                    Gtk.IconSize.MENU)
            self.__action_button.set_tooltip_text(_("Go to artist view"))
        else:
            self.__action_button = Gtk.Button.new_from_icon_name(
                "view-more-symbolic",
                Gtk.IconSize.MENU)
        if self.__action_button is not None:
            self.__action_button.set_margin_end(MARGIN_SMALL)
            self.__action_button.set_relief(Gtk.ReliefStyle.NONE)
            self.__action_button.get_style_context().add_class("menu-button")
            self.__action_button.set_property("valign", Gtk.Align.CENTER)
            self.__gesture_helper = GesturesHelper(
                self.__action_button,
                primary_press_callback=self._on_action_button_press)
        grid.attach(self.__artwork, 0, 0, 1, 2)
        grid.attach(self.__artist_label, 1, 0, 1, 1)
        grid.attach(self.__title_label, 1, 1, 1, 1)
        if self.__action_button is not None:
            grid.attach(self.__action_button, 2, 0, 1, 2)
        self.__revealer = Gtk.Revealer.new()
        self.__revealer.show()
        grid.attach(self.__revealer, 0, 2, 3, 1)
        self.__revealer.add(self.__tracks_view)
        self.add(grid)
        self.set_playing_indicator()
        self.set_artwork()

    def append_rows(self, tracks):
        """
            Add track rows
            @param tracks as [Track]
        """
        if self.__tracks_view.is_populated:
            self.__tracks_view.append_rows(tracks)

    def reveal(self, reveal=None):
        """
            Reveal/Unreveal tracks
            @param reveal as bool or None to just change state
        """
        if self.__revealer.get_reveal_child() and reveal is not True:
            self.__revealer.set_reveal_child(False)
            if self.album.id == App().player.current_track.album.id:
                self.set_state_flags(Gtk.StateFlags.VISITED, True)
        else:
            if not self.__tracks_view.is_populated:
                self.__tracks_view.populate()
            self.__revealer.set_reveal_child(True)
            self.unset_state_flags(Gtk.StateFlags.VISITED)

    def set_playing_indicator(self):
        """
            Show play indicator
        """
        if self.__artwork is None:
            return
        selected = self.album.id == App().player.current_track.album.id and\
            App().player.current_track.id in self.album.track_ids
        if self.__revealer.get_reveal_child():
            self.__tracks_view.set_playing_indicator()
            self.set_state_flags(Gtk.StateFlags.NORMAL, True)
        elif selected:
            self.set_state_flags(Gtk.StateFlags.VISITED, True)
        else:
            self.set_state_flags(Gtk.StateFlags.NORMAL, True)

    def stop(self):
        """
            Stop view loading
        """
        self.__artwork = None
        if self.__tracks_view.is_populated:
            self.__tracks_view.stop()

    def set_artwork(self):
        """
            Set album artwork
        """
        if self.__artwork is None:
            return
        App().art_helper.set_album_artwork(self.__album,
                                           ArtSize.SMALL,
                                           ArtSize.SMALL,
                                           self.__artwork.get_scale_factor(),
                                           ArtBehaviour.CACHE |
                                           ArtBehaviour.CROP_SQUARE,
                                           self.__on_album_artwork)

    @property
    def revealed(self):
        """
            True if revealed
            @return bool
        """
        return self.__revealer is not None and\
            self.__revealer.get_reveal_child()

    @property
    def listbox(self):
        """
            Get listbox
            @return Gtk.ListBox
        """
        return self.__tracks_view.boxes[0]

    @property
    def children(self):
        """
            Get track rows
            @return [TrackRow]
        """
        return self.__tracks_view.boxes[0].get_children()

    @property
    def is_populated(self):
        """
            Return True if populated
            @return bool
        """
        return not self.revealed or self.__tracks_view.is_populated

    @property
    def name(self):
        """
            Get row name
            @return str
        """
        return self.__title_label.get_text() + self.__artist_label.get_text()

    @property
    def album(self):
        """
            Get album
            @return row id as int
        """
        return self.__album

#######################
# PROTECTED           #
#######################
    def _on_action_button_press(self, x, y, event):
        """
            Show row menu
            @param x as int
            @param y as int
            @param event as Gdk.EventButton
        """
        if not self.get_state_flags() & Gtk.StateFlags.PRELIGHT:
            return True
        if self.__view_type & ViewType.PLAYBACK:
            App().player.remove_album(self.__album)
            self.destroy()
            App().player.update_next_prev()
        elif self.__album.storage_type & StorageType.EPHEMERAL:
            App().art.copy_from_web_to_store(self.__album.id)
            App().art.cache_artists_artwork()
            self.__album.save(True)
            self.__action_button.hide()
        elif self.__view_type & ViewType.SEARCH:
            popover = self.get_ancestor(Gtk.Popover)
            if popover is not None:
                popover.popdown()
            App().window.container.show_view([Type.ARTISTS],
                                             self.__album.artist_ids)
        elif self.__view_type & ViewType.PLAYLISTS:
            if App().player.current_track.album.id == self.__album.id:
                # Stop playback or loop for last album
                # Else skip current
                if len(App().player.albums) == 1:
                    App().player.remove_album(self.__album)
                    App().player.next()
                else:
                    App().player.skip_album()
                    App().player.remove_album(self.__album)
            else:
                App().player.remove_album(self.__album)
            App().player.update_next_prev()
            from lollypop.view_playlists import PlaylistsView
            view = self.get_ancestor(PlaylistsView)
            if view is not None:
                view.remove_from_playlist(self.__album)
            self.destroy()
        else:
            self.__popup_menu(self.__action_button)

#######################
# PRIVATE             #
#######################
    def __popup_menu(self, widget):
        """
            Popup menu for album
            @param widget as Gtk.Widget
        """
        def on_closed(popover):
            self.unset_state_flags(Gtk.StateFlags.FOCUSED)

        from lollypop.menu_objects import AlbumMenu
        from lollypop.widgets_menu import MenuBuilder
        menu = AlbumMenu(self.__album, ViewType.ALBUM,
                         App().window.is_adaptive)
        menu_widget = MenuBuilder(menu)
        menu_widget.show()
        self.set_state_flags(Gtk.StateFlags.FOCUSED, True)
        popover = popup_widget(menu_widget, widget)
        if popover is not None:
            popover.connect("closed", on_closed)

    def __on_album_artwork(self, surface):
        """
            Set album artwork
            @param surface as str
        """
        if self.__artwork is None:
            return
        if surface is None:
            self.__artwork.set_from_icon_name("folder-music-symbolic",
                                              Gtk.IconSize.BUTTON)
        else:
            self.__artwork.set_from_surface(surface)
        self.show_all()
        # TracksView will not emit populated
        if not self.revealed:
            self.emit("populated")

    def __on_query_tooltip(self, widget, x, y, keyboard, tooltip):
        """
            Show tooltip if needed
            @param widget as Gtk.Widget
            @param x as int
            @param y as int
            @param keyboard as bool
            @param tooltip as Gtk.Tooltip
        """
        layout_title = self.__title_label.get_layout()
        layout_artist = self.__artist_label.get_layout()
        if layout_title.is_ellipsized() or layout_artist.is_ellipsized():
            artist = GLib.markup_escape_text(self.__artist_label.get_text())
            title = GLib.markup_escape_text(self.__title_label.get_text())
            self.set_tooltip_markup("<b>%s</b>\n%s" % (artist, title))
        else:
            self.set_tooltip_text("")

    def __on_destroy(self, widget):
        """
            Destroyed widget
            @param widget as Gtk.Widget
        """
        self.__cancellable.cancel()
        self.__artwork = None

    def __on_tracks_populated(self, view, disc_number):
        """
            Populate remaining discs
            @param view as TracksView
            @param disc_number as int
        """
        if self.revealed and not self.__tracks_view.is_populated:
            self.__tracks_view.populate()
        else:
            self.emit("populated")
