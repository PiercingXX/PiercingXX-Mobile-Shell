#!/usr/bin/env python3

import sys

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Adw, Gio

from window import ShellWindow


class PiercingShellApplication(Adw.Application):
    def __init__(self) -> None:
        super().__init__(
            application_id='io.piercingxx.PiercingShell',
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )

    def do_activate(self) -> None:
        window = self.props.active_window
        if window is None:
            window = ShellWindow(self)
        window.present()


def main(argv: list[str] | None = None) -> int:
    app = PiercingShellApplication()
    return app.run(argv or sys.argv)


if __name__ == '__main__':
    raise SystemExit(main())