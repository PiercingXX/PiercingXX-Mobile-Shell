from __future__ import annotations

from datetime import datetime
from pathlib import Path

from gi.repository import Adw, Gdk, GLib, Gtk

from app_index import AppEntry, AppIndex
from config import FONT_FAMILIES, THEME_PRESETS, ShellConfig


class ShellWindow(Adw.ApplicationWindow):
    def __init__(self, application: Adw.Application) -> None:
        super().__init__(application=application, title='Piercing Shell')
        self.set_default_size(420, 860)
        self.fullscreen()

        self.config = ShellConfig()
        self.app_index = AppIndex()
        self.app_index.refresh()

        self.base_provider = Gtk.CssProvider()
        self.theme_provider = Gtk.CssProvider()
        self._load_css()

        self.home_rows: list[Gtk.Widget] = []
        self.drawer_rows: list[Gtk.Widget] = []

        self.stack = Gtk.Stack(
            hexpand=True,
            vexpand=True,
            transition_duration=180,
            transition_type=Gtk.StackTransitionType.CROSSFADE,
        )

        self.home_search = Gtk.SearchEntry(placeholder_text='Search or launch')
        self.home_search.connect('activate', self._on_home_search_activate)
        self.home_search.connect('search-changed', self._on_home_search_changed)

        self.apps_search = Gtk.SearchEntry(placeholder_text='Filter apps')
        self.apps_search.connect('search-changed', self._on_apps_search_changed)
        self.apps_search.connect('activate', self._on_apps_search_activate)

        self.theme_dropdown = Gtk.DropDown.new_from_strings([preset.name for preset in THEME_PRESETS.values()])
        self.theme_dropdown.connect('notify::selected', self._on_theme_changed)

        self.font_dropdown = Gtk.DropDown.new_from_strings(['Sans Light', 'Space Mono', 'JetBrains Mono'])
        self.font_dropdown.connect('notify::selected', self._on_font_changed)

        self.dark_mode_switch = Gtk.Switch(active=self.config.prefer_dark)
        self.dark_mode_switch.connect('notify::active', self._on_dark_mode_toggled)

        self.status_label = Gtk.Label(xalign=0)
        self.status_label.add_css_class('dim-label')

        self.app_count_label = Gtk.Label(xalign=0)
        self.app_count_label.add_css_class('dim-label')

        self.clock_label = Gtk.Label(xalign=0)
        self.clock_label.add_css_class('display-clock')

        self.date_label = Gtk.Label(xalign=0)
        self.date_label.add_css_class('display-date')

        self.home_list = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        self.home_list.add_css_class('text-list')

        self.apps_list = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        self.apps_list.add_css_class('text-list')

        self.toast_overlay = Adw.ToastOverlay()
        self.toast_overlay.set_child(self._build_root())
        self.set_content(self.toast_overlay)

        self._sync_controls_from_config()
        self._apply_theme()
        self._refresh_clock()
        self._populate_home()
        self._populate_apps()
        GLib.timeout_add_seconds(30, self._tick_clock)

    def _load_css(self) -> None:
        style_path = Path(__file__).with_name('style.css')
        self.base_provider.load_from_path(str(style_path))
        display = Gdk.Display.get_default()
        Gtk.StyleContext.add_provider_for_display(display, self.base_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        Gtk.StyleContext.add_provider_for_display(display, self.theme_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1)

    def _build_root(self) -> Gtk.Widget:
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        root.add_css_class('shell-root')

        self.stack.add_titled(self._build_home_page(), 'home', 'Home')
        self.stack.add_titled(self._build_apps_page(), 'apps', 'Apps')
        self.stack.add_titled(self._build_settings_page(), 'settings', 'Settings')

        nav_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        nav_row.add_css_class('nav-row')
        nav_row.set_margin_start(24)
        nav_row.set_margin_end(24)
        nav_row.set_margin_bottom(20)

        for name, title in [('home', 'Home'), ('apps', 'Apps'), ('settings', 'Settings')]:
            button = Gtk.Button(label=title)
            button.add_css_class('nav-button')
            button.connect('clicked', lambda _button, page=name: self.stack.set_visible_child_name(page))
            nav_row.append(button)

        root.append(self.stack)
        root.append(nav_row)
        return root

    def _build_home_page(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        box.set_margin_top(36)
        box.set_margin_bottom(24)
        box.set_margin_start(24)
        box.set_margin_end(24)

        identity = Gtk.Label(
            label='PIERCING SHELL',
            xalign=0,
        )
        identity.add_css_class('eyebrow')

        prompt = Gtk.Label(
            label='Pixel 3a shell built on a Mobian-first stack.',
            xalign=0,
            wrap=True,
        )
        prompt.add_css_class('dim-label')

        shortcuts_title = Gtk.Label(label='Pinned apps', xalign=0)
        shortcuts_title.add_css_class('section-title')

        open_apps = Gtk.Button(label='Open full app list')
        open_apps.add_css_class('flat')
        open_apps.add_css_class('action-link')
        open_apps.connect('clicked', lambda _button: self.stack.set_visible_child_name('apps'))

        launcher_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        launcher_row.append(open_apps)

        list_scroll = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
        list_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        list_scroll.set_child(self.home_list)

        box.append(identity)
        box.append(self.clock_label)
        box.append(self.date_label)
        box.append(prompt)
        box.append(self.home_search)
        box.append(shortcuts_title)
        box.append(launcher_row)
        box.append(list_scroll)
        return box

    def _build_apps_page(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_top(36)
        box.set_margin_bottom(24)
        box.set_margin_start(24)
        box.set_margin_end(24)

        title = Gtk.Label(label='All apps', xalign=0)
        title.add_css_class('section-title')

        subtitle = Gtk.Label(
            label='Text-first launcher index with quick search and direct launch.',
            xalign=0,
            wrap=True,
        )
        subtitle.add_css_class('dim-label')

        scroller = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.set_child(self.apps_list)

        box.append(title)
        box.append(subtitle)
        box.append(self.apps_search)
        box.append(self.app_count_label)
        box.append(scroller)
        return box

    def _build_settings_page(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        box.set_margin_top(36)
        box.set_margin_bottom(24)
        box.set_margin_start(24)
        box.set_margin_end(24)

        title = Gtk.Label(label='Shell settings', xalign=0)
        title.add_css_class('section-title')

        subtitle = Gtk.Label(
            label='Launcher-inspired defaults: monochrome surfaces, large type, fast search, no icon grid.',
            xalign=0,
            wrap=True,
        )
        subtitle.add_css_class('dim-label')

        rows = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        rows.add_css_class('settings-card')

        rows.append(self._settings_row('Theme preset', self.theme_dropdown))
        rows.append(self._settings_row('Font family', self.font_dropdown))
        rows.append(self._settings_row('Prefer dark surfaces', self.dark_mode_switch))

        top_apps_button = Gtk.Button(label='Use top 8 apps on home')
        top_apps_button.add_css_class('flat')
        top_apps_button.add_css_class('action-link')
        top_apps_button.connect('clicked', self._use_top_apps_for_home)

        refresh_button = Gtk.Button(label='Rebuild application index')
        refresh_button.add_css_class('flat')
        refresh_button.add_css_class('action-link')
        refresh_button.connect('clicked', self._refresh_index)

        rows.append(top_apps_button)
        rows.append(refresh_button)
        rows.append(self.status_label)

        box.append(title)
        box.append(subtitle)
        box.append(rows)
        return box

    def _settings_row(self, title: str, control: Gtk.Widget) -> Gtk.Widget:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        label = Gtk.Label(label=title, xalign=0)
        label.set_hexpand(True)
        row.append(label)
        row.append(control)
        return row

    def _sync_controls_from_config(self) -> None:
        theme_keys = list(THEME_PRESETS)
        font_keys = list(FONT_FAMILIES)
        self.theme_dropdown.set_selected(theme_keys.index(self.config.theme.key))
        self.font_dropdown.set_selected(font_keys.index(next(key for key, value in FONT_FAMILIES.items() if value == self.config.font_family)))
        self.dark_mode_switch.set_active(self.config.prefer_dark)

    def _apply_theme(self) -> None:
        theme = self.config.theme
        style_manager = Adw.StyleManager.get_default()
        if self.config.prefer_dark:
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        else:
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)

        css = f"""
        .shell-root {{
            background: {theme.background};
            color: {theme.foreground};
            font-family: '{self.config.font_family}';
        }}

        .shell-root entry,
        .shell-root text,
        .shell-root list,
        .shell-root row,
        .shell-root button,
        .shell-root box,
        .shell-root scrolledwindow,
        .shell-root label {{
            color: {theme.foreground};
        }}

        .shell-root entry,
        .shell-root list,
        .shell-root row,
        .shell-root scrolledwindow,
        .settings-card {{
            background: {theme.surface};
            border-color: {theme.border};
        }}

        .shell-root button:hover,
        .shell-root button:focus {{
            background: {theme.surface_alt};
        }}

        .dim-label,
        .eyebrow {{
            color: {theme.muted};
        }}

        .action-link {{
            color: {theme.accent};
        }}
        """
        self.theme_provider.load_from_data(css.encode('utf-8'))

    def _refresh_clock(self) -> None:
        now = datetime.now()
        self.clock_label.set_text(now.strftime('%H:%M'))
        self.date_label.set_text(now.strftime('%A, %d %b').replace(' 0', ' '))

    def _tick_clock(self) -> bool:
        self._refresh_clock()
        return True

    def _refresh_index(self, _button: Gtk.Button | None = None) -> None:
        self.app_index.refresh()
        self._populate_home()
        self._populate_apps(self.apps_search.get_text())
        self._show_status('Application index rebuilt.')

    def _use_top_apps_for_home(self, _button: Gtk.Button) -> None:
        top_ids = [entry.app_id for entry in self.app_index.top(8)]
        self.config.set_pinned(top_ids)
        self._populate_home()
        self._show_status('Pinned home list reset to the first 8 visible apps.')

    def _populate_home(self) -> None:
        pinned = self.app_index.resolve(self.config.pinned)
        if not pinned:
            pinned = self.app_index.top(8)
        self._replace_rows(self.home_list, pinned, empty_message='No launchable apps were indexed.')

    def _populate_apps(self, query: str = '') -> None:
        results = self.app_index.search(query)
        self._replace_rows(self.apps_list, results, empty_message='No apps matched this search.')
        if query.strip():
            self.app_count_label.set_text(f'{len(results)} matches')
        else:
            self.app_count_label.set_text(f'{len(results)} apps indexed')

    def _replace_rows(self, list_box: Gtk.ListBox, entries: list[AppEntry], empty_message: str) -> None:
        child = list_box.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            list_box.remove(child)
            child = next_child

        if not entries:
            label = Gtk.Label(label=empty_message, xalign=0)
            label.add_css_class('dim-label')
            row = Gtk.ListBoxRow(selectable=False, activatable=False)
            row.set_child(label)
            list_box.append(row)
            return

        for entry in entries:
            list_box.append(self._make_app_row(entry))

    def _make_app_row(self, entry: AppEntry) -> Gtk.ListBoxRow:
        title = Gtk.Label(label=entry.name, xalign=0)
        title.add_css_class('app-name')

        subtitle_text = entry.description or entry.app_id
        subtitle = Gtk.Label(label=subtitle_text, xalign=0, wrap=True)
        subtitle.add_css_class('app-subtitle')
        subtitle.add_css_class('dim-label')

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        content.append(title)
        content.append(subtitle)

        button = Gtk.Button()
        button.add_css_class('flat')
        button.add_css_class('app-entry')
        button.set_child(content)
        button.connect('clicked', lambda _button, app_entry=entry: self._launch_entry(app_entry))

        row = Gtk.ListBoxRow(selectable=False, activatable=False)
        row.set_child(button)
        return row

    def _launch_entry(self, entry: AppEntry) -> None:
        ok, error = self.app_index.launch(entry)
        if ok:
            self._show_status(f'Launching {entry.name}...')
        else:
            self._show_status(f'Failed to launch {entry.name}: {error}')

    def _on_home_search_changed(self, entry: Gtk.SearchEntry) -> None:
        text = entry.get_text().strip()
        if not text:
            return
        self._populate_apps(text)

    def _on_home_search_activate(self, entry: Gtk.SearchEntry) -> None:
        query = entry.get_text().strip()
        if not query:
            return

        results = self.app_index.search(query)
        if len(results) == 1 or (results and results[0].name.casefold() == query.casefold()):
            self._launch_entry(results[0])
            return

        self.apps_search.set_text(query)
        self._populate_apps(query)
        self.stack.set_visible_child_name('apps')

    def _on_apps_search_changed(self, entry: Gtk.SearchEntry) -> None:
        self._populate_apps(entry.get_text())

    def _on_apps_search_activate(self, entry: Gtk.SearchEntry) -> None:
        results = self.app_index.search(entry.get_text())
        if results:
            self._launch_entry(results[0])

    def _on_theme_changed(self, dropdown: Gtk.DropDown, _paramspec: object) -> None:
        theme_key = list(THEME_PRESETS)[dropdown.get_selected()]
        self.config.set_theme(theme_key)
        self._apply_theme()
        self._show_status(f'Theme set to {THEME_PRESETS[theme_key].name}.')

    def _on_font_changed(self, dropdown: Gtk.DropDown, _paramspec: object) -> None:
        font_key = list(FONT_FAMILIES)[dropdown.get_selected()]
        self.config.set_font(font_key)
        self._apply_theme()
        self._show_status('Font family updated.')

    def _on_dark_mode_toggled(self, switch: Gtk.Switch, _paramspec: object) -> None:
        self.config.set_prefer_dark(switch.get_active())
        self._apply_theme()
        self._show_status('Surface mode updated.')

    def _show_status(self, message: str) -> None:
        self.status_label.set_text(message)
        self.toast_overlay.add_toast(Adw.Toast.new(message))