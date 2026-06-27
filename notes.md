# Piercing Shell — Linux Phone Project

## What this project is

A fully custom Linux phone OS shell for the **Pixel 3a (google/sargo, sdm670)**. The goal is a daily-driver phone that looks and feels like a Pixel running Android — same gesture model, same UX expectations — but built entirely on Linux.

Architecture:
- **Compositor**: Fork of phoc (Phosh's wlroots-based Wayland compositor) — handles all hardware, touch, display
- **Shell surfaces**: GTK4/libadwaita Python, using `gtk4-layer-shell` to anchor surfaces to screen edges
- **Design language**: PiercingXX — text-first, minimal chrome, monochrome, large type, gesture-driven

The shell in `pixel-3a/shell/` is the working starting point. It currently runs as a plain GTK4 app (not a compositor). It needs to be ported to a layer-shell surface and expanded into a full compositor + shell stack.

## Repo layout

```
pixel-3a/
  shell/          ← working GTK4/libadwaita launcher shell (Python, meson build)
    src/          ← main.py, window.py, app_index.py, config.py, style.css
    data/         ← desktop entry, launcher wrapper
    build/        ← meson build output (gitignored)
  downloads/      ← OS images (gitignored), kept as reference:
    mobian/       ← PRIMARY target: mobian-sdm670-phosh-20260607.tar.xz
    postmarketos/ ← Alternative target: 20260605 phosh build
    ubuntu-touch/ ← Reference only (service/UX patterns)
    droidian/     ← Reference only (Android device adaptation)
  research.md     ← Phase 0 research findings (READ THIS FIRST)
fairphone-5/      ← Separate device target, not active yet
todo.md           ← Full phased plan (8 phases) — the source of truth for what to build
```

## Read these files first

1. **`todo.md`** — 8-phase plan from research through packaging. Phases 0–1 are immediate.
2. **`pixel-3a/research.md`** — Phase 0 findings: Android launcher audit, Pixel gesture reference, hardware capabilities of the 3a, open questions before Phase 1.
3. **`pixel-3a/shell/README.md`** — Current shell state and local build instructions.

## Where we are right now

Phase 0 (research) is partially complete:
- [x] PiercingXX Android launcher audited (`github.com/piercingxx/piercingxx-launcher`)
- [x] Pixel gesture model documented (see `pixel-3a/research.md`)
- [ ] OS boot test not done yet — need to boot Mobian and postmarketOS on the device and compare hardware support (modem, WiFi, touch, Active Edge sensor)

Phase 1 (build pipeline) has not started.

## Key decisions already made

| Decision | Choice | Reason |
|---|---|---|
| Compositor | Fork phoc | wlroots-based, phone-optimized, faster than from-scratch |
| Shell language | Python + GTK4/libadwaita | Existing codebase, fits the stack |
| Layer shell | gtk4-layer-shell | Required for lock screen, shade, app switcher surfaces |
| Base OS | Undecided (Mobian vs postmarketOS) | Boot test required first |
| Gesture model | Pixel-default (familiar to users) | Swipe up=home/switcher, swipe down=shade, edge swipe=back |
| Shell depth | Full compositor replacement | Not an app on top of Phosh — we own the session |

## Gesture model (summary)

From `pixel-3a/research.md`:

| Gesture | Action | Handled by |
|---|---|---|
| Short swipe up from bottom | Home | phoc |
| Long swipe up / swipe up + hold | App switcher | shell `app_switcher.py` |
| Swipe in from left or right edge | Back | phoc |
| Swipe left/right along bottom bar | Quick-switch last 2 apps | phoc |
| Single-finger swipe down from top | Notification shade | shell `notification_shade.py` |
| Two-finger swipe down from top | Quick Settings direct | shell `notification_shade.py` |
| Long press home background | Settings | shell `window.py` |
| Double-tap home background | Lock screen | shell → `lock_screen.py` |
| Swipe left/right on home | Configurable app (default: camera/dialer) | shell `gesture_config.py` |
| Squeeze (Active Edge) | Configurable action | phoc or shell via evdev |
| Fingerprint sensor swipe down | Notification shade | shell via evdev |
| Double-press power | Camera | phoc / logind |

**Gesture thresholds** (from Android launcher source, tune on device):
- 100px displacement + 100px/s velocity to fire a swipe
- 500ms long press delay
- 20–24dp edge inset for compositor back-gesture zone

## Shell surfaces to build

Six layer-shell surfaces, each a separate GTK4 window:

1. **Home/Launcher** (`window.py`) — existing, needs layer-shell port + gesture navigation
2. **Lock Screen** (`lock_screen.py`) — OVERLAY layer, exclusive keyboard grab, PIN entry
3. **Notification Shade** (`notification_shade.py`) — TOP layer, slides down from top edge
4. **App Switcher** (`app_switcher.py`) — TOP layer, slides up from bottom edge
5. **Quick Actions** — embedded in top of notification shade surface
6. **Call UI** (`call_ui.py`) — OVERLAY layer, appears on lock screen for incoming calls

IPC between surfaces: GDBus or lightweight Unix socket.

## Android launcher → Linux shell mapping

The Android launcher has these gesture-configurable slots we need to replicate:

- `swipe_down` → `NOTIFICATIONS` or `SEARCH` (configurable in `gesture_config.py`)
- `swipe_left` → any app (default: camera)
- `swipe_right` → any app (default: dialer)
- `double_tap` → lock
- `long_press` → settings

The app drawer character-jump index (A–Z sidebar), hidden apps list, and text-size-scale setting are in the Android launcher but not yet in the Linux shell.

## Open questions (must resolve in Phase 0 before Phase 1)

1. Which OS — Mobian or postmarketOS — has better hardware support on sargo? (Boot test required)
2. Does Active Edge (squeeze) appear as a standard evdev device on Linux?
3. Does the rear fingerprint sensor expose a swipe gesture separately from auth?
4. Is `wlr-foreign-toplevel-management-unstable-v1` in the phoc version on the target OS? (Required for app switcher)
5. PipeWire or PulseAudio on the target OS? (Affects volume in quick actions)

## Running the current shell locally

```bash
# Install deps (Debian/Mobian host)
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 meson ninja-build

# Run directly
cd pixel-3a/shell
PYTHONPATH=src python3 src/main.py

# Or build + install
meson setup build
meson install -C build
```

## Style conventions

- Python, GTK4/libadwaita, meson build system
- No icon grids — text-first throughout
- Monochrome surfaces, themed via `config.py` THEME_PRESETS
- Fonts: Space Mono (default), JetBrains Mono, Sans Light
- No comments unless the WHY is non-obvious
