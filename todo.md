# Piercing Shell — Pixel 3a: Path to Fully Functional

Architecture target: phoc (forked) as Wayland compositor backend + custom GTK4/libadwaita shell surfaces (Python + gtk4-layer-shell) using the PiercingXX design language. Minimal, gesture-driven, text-first.

---

## Phase 0 — Research & Foundation Decisions

- [ ] **Audit PiercingXX Android launcher** (`github.com/piercingxx/piercingxx-launcher`) — extract gesture model, layout logic, quick-action panel spec, and any interaction patterns not yet in the GTK shell. Document what maps directly and what needs rethinking for a Wayland compositor context.
- [ ] **OS comparison: Mobian vs postmarketOS for Pixel 3a (sargo/sdm670)**
  - Boot both Mobian phosh (`mobian-sdm670-phosh-20260607.tar.xz`) and postmarketOS phosh (`20260605-0025-postmarketOS-v25.12-phosh-25-google-sargo`) on the device
  - Test: cellular modem, WiFi, touch, display, audio, camera init, suspend/resume
  - Decide primary OS based on which has more complete hardware support on sargo out of the box
  - Ubuntu Touch and Droidian images kept as device-support reference only (not a target)
- [ ] **Pin dependency versions**: document GTK4, libadwaita, phoc, wlroots, and gtk4-layer-shell versions present on the chosen OS image so shell dev targets exactly that stack
- [ ] **Set up cross-compile or on-device dev workflow** — decide between: build on device (slow but exact), cross-compile for aarch64 on host, or QEMU/chroot for Python-only layers

---

## Phase 1 — Build & Deploy Pipeline

- [ ] **Fork phoc** into `pixel-3a/compositor/` — tag the base upstream commit for reference diffs
- [ ] **Verify phoc builds on chosen OS** — confirm wlroots version compatibility with the Pixel 3a kernel
- [ ] **Write deploy script** (`pixel-3a/deploy.sh`) — rsync or scp shell source + compositor onto device, restart session, tail logs. One command for iteration.
- [ ] **Establish session entry point** — write a `.desktop` session file that launches forked phoc + Piercing Shell instead of phoc + phosh; register it with the display manager so it can be selected on login
- [ ] **Add gtk4-layer-shell dependency** to meson.build — required for all shell surfaces to anchor to screen edges using `wlr-layer-shell-unstable-v1`

---

## Phase 2 — Core Shell Surfaces (Layer Shell)

Each surface is a separate GTK4 `Gtk.Window` configured via gtk4-layer-shell to anchor to the correct screen zone. They communicate via a lightweight IPC bus (GDBus or a simple Unix socket).

### 2a — Home & Launcher (extend existing shell)
- [ ] Port existing `window.py` / `main.py` to use `gtk4-layer-shell` instead of a plain `Adw.ApplicationWindow` — anchor to full screen, set layer to `BOTTOM` so apps render above it
- [ ] Remove the three-button nav row — replace with gesture-only navigation (buttons are a fallback in settings only)
- [ ] Keep Home / Apps / Settings page stack but driven by swipe gestures, not buttons
- [ ] Add pinned app editing: long-press on home row enters edit mode, drag to reorder, tap X to unpin, tap any app in drawer to pin

### 2b — Lock Screen
- [ ] New surface: `src/lock_screen.py` — layer `OVERLAY`, exclusive keyboard grab, rendered above all other surfaces
- [ ] PIN entry: 6-digit keypad (large touch targets, minimal chrome), matching PiercingXX style (monochrome, large type)
- [ ] Show clock + date (reuse `_refresh_clock` logic) on lock surface
- [ ] Show incoming call UI on lock screen (see Phase 5)
- [ ] Unlock: correct PIN dismisses layer, emits `unlocked` signal on IPC bus
- [ ] Auto-lock: idle timer in session manager triggers lock surface; configurable timeout in Settings

### 2c — Notification Shade (swipe down)
- [ ] New surface: `src/notification_shade.py` — layer `TOP`, anchored top, slides down on swipe-down gesture from top edge
- [ ] Connects to `org.freedesktop.Notifications` via DBus, renders a list of active notifications in the PiercingXX text-list style (title + body, app name dim, dismiss button)
- [ ] Tap to open app, swipe left/right on individual notification to dismiss
- [ ] Pull-down gesture drives the reveal animation (Gtk.Gesture + manual translation via `set_margin_top`)
- [ ] Quick settings row at top of shade (see Phase 3) — visible as soon as shade opens
- [ ] Second pull-down expands to full quick-settings grid

### 2d — App Switcher (swipe up)
- [ ] New surface: `src/app_switcher.py` — layer `TOP`, anchored bottom, slides up on swipe-up from bottom edge
- [ ] Query running Wayland clients via phoc IPC or `wlr-foreign-toplevel-management-unstable-v1` protocol
- [ ] Render as horizontal card strip (app name + last-known screenshot/thumbnail if available, else icon/name card)
- [ ] Swipe card up to close, tap to focus
- [ ] Home gesture (short swipe up) collapses switcher back; long swipe up enters full switcher view
- [ ] Swipe left on a card to force-kill the app

---

## Phase 3 — Quick Actions Panel

Accessible from notification shade (top strip always visible, expand for full grid).

- [ ] **Tile layout**: 4-across grid, PiercingXX style — text label + icon glyph (symbolic), no color fills except active state
- [ ] **Tier 1 tiles (always on strip)**: WiFi toggle, Bluetooth toggle, Mobile Data toggle, Airplane Mode toggle
- [ ] **Tier 2 tiles (expanded grid)**: Flashlight, Do Not Disturb, Auto-rotate, Location, Hotspot
- [ ] **Sliders below grid**: Brightness (via `/sys/class/backlight`), Volume (via PulseAudio/PipeWire GObject bindings)
- [ ] Each toggle fires the appropriate DBus method (NetworkManager for WiFi/data, BlueZ for BT, ofono/ModemManager for airplane mode)
- [ ] Active tile state persists from DBus property subscriptions — tiles reflect live system state, not last tap

---

## Phase 4 — Gesture System

- [ ] **Define gesture map** in `src/gesture_config.py` — configurable dict mapping gesture actions to handler names; stored in `~/.config/piercing-shell/gestures.json`
- [ ] **Default gesture set** (Pixel-familiar defaults):
  - Swipe down from top edge → open notification shade
  - Swipe up from bottom edge → open app switcher (short) / home (very short)
  - Swipe left from right edge → back
  - Long-press bottom edge → assistant/search trigger (placeholder for now)
- [ ] **Gesture recognizers**: use `Gtk.GestureSwipe` + `Gtk.GesturePan` on each surface; for edge gestures, phoc provides the raw pointer/touch events at the compositor level — add a phoc plugin or use the `input-method` / grab approach to intercept edge swipes before surfaces get them
- [ ] **Settings page addition**: gesture editor — list each gesture slot, show current binding, allow rebinding to any registered action
- [ ] **Gesture feedback**: subtle spring animation on gesture begin/cancel (interpolate surface translation, snap back if threshold not met)

---

## Phase 5 — Telephony & SMS

- [ ] **Modem stack**: confirm ofono or ModemManager is present on chosen OS image; if ofono, add `python-dbus` bindings; if ModemManager, use `gi.repository.ModemManager`
- [ ] **Call UI surface**: `src/call_ui.py` — full-screen overlay, shows caller ID, accept/decline buttons (large, thumb-reachable), mute, speaker, keypad
  - Incoming call: surface appears over lock screen
  - Active call: persistent bar at top of home (like Android) with tap-to-expand
  - End call returns to previous surface
- [ ] **Dialer page**: add 'Phone' tab or standalone app entry that opens numeric keypad + contact search (read contacts from Evolution Data Server or local vCard store)
- [ ] **SMS/Messages**: lightweight message list surface — conversation view, send field at bottom; backend via ofono SMS DBus API or mmcli; no third-party messenger integration in scope yet
- [ ] **Mobile data**: integrate APN configuration into Settings page; NetworkManager DBus for connection management

---

## Phase 6 — System Integration

- [ ] **Battery**: read `/sys/class/power_supply/` and display in status area on home and lock screen; low battery toast notification
- [ ] **Network status**: show WiFi SSID or signal bars + mobile signal strength in a minimal status strip at top of home screen (not a full status bar — just inline text in the header zone)
- [ ] **Audio routing**: PipeWire/PulseAudio GObject bindings for volume control; auto-switch to earpiece on call, speaker toggle, headset detection
- [ ] **Display**: auto-brightness option (read ambient light sensor if available); forced rotation lock toggle in quick actions
- [ ] **Suspend/wake**: handle `logind` `PrepareForSleep` signal — lock screen before suspend, unlock on resume (correct PIN required)
- [ ] **Notification daemon**: if no system notification daemon is running, start a minimal one as part of the shell session that implements `org.freedesktop.Notifications`; bridge to the shade surface

---

## Phase 7 — Packaging & Image Build

- [ ] **Meson install targets**: update `meson.build` to install all new surface modules, session `.desktop`, and systemd user service for the shell
- [ ] **Session file**: `data/io.piercingxx.PiercingShell.session` — registers the full compositor+shell combo as a selectable session
- [ ] **OS image overlay**: write a `rootfs-overlay/` directory under `pixel-3a/` that can be extracted on top of the chosen base image — includes all installed shell files, session config, and any patched phoc binary
- [ ] **Flash script**: `pixel-3a/flash.sh` — takes the base image, applies the overlay, and flashes via fastboot/heimdall in one step; documents unlock + flash steps for Pixel 3a bootloader
- [ ] **First-boot setup**: minimal first-run wizard surface (before lock screen is configured) — set PIN, pick theme, confirm timezone

---

## Phase 8 — Polish & Hardening

- [ ] **Touch target audit**: every interactive element must be >= 48px tall; review all surfaces on 2160×1080 (Pixel 3a) at 420dpi
- [ ] **Theme propagation**: phoc + gtk4 theme should be consistent — dark/light preference in config propagates to GTK_THEME env var and libadwaita color scheme at session start
- [ ] **Font installation**: ensure Space Mono and JetBrains Mono are present in the OS image overlay; fall back gracefully to system monospace
- [ ] **Performance baseline**: measure shell startup time, gesture latency, and app launch latency on device; target <300ms home-to-app-open
- [ ] **Crash recovery**: phoc should restart the shell surface if it exits unexpectedly; add a `Restart=on-failure` systemd unit
- [ ] **Logging**: structured log output to `~/.local/share/piercing-shell/shell.log` with rotation; accessible from Settings page

---

## Deferred / Out of Scope for Now

- Camera app
- Web browser integration
- OTA update mechanism
- Third-party messenger support (Signal, WhatsApp, etc.)
- Multi-user / guest mode
- Accessibility (screen reader, large-text mode)
- App sandboxing / Flatpak integration
