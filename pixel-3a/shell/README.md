# Piercing Shell for Pixel 3a

This is the first operational shell layer for the Pixel 3a target. It is a Mobian-first GTK4/libadwaita launcher shell that borrows the PiercingXX Launcher design language: text-first layout, low visual noise, fast search, large type, pinned shortcuts, and a shallow home/apps/settings flow.

## Base OS choice

Use Mobian as the base for the Pixel 3a build.

Why Mobian first:

- Debian userland makes packaging, iteration, and debugging straightforward.
- GTK4/libadwaita is a natural fit for a GNOME/mobile stack.
- Ubuntu Touch artifacts remain useful as reference for mobile service behavior and packaging ideas.
- postmarketOS artifacts remain useful for kernel, firmware, and device-specific fallback work if Pixel 3a hardware support needs driver comparison or extraction.

## What this project is right now

- A fullscreen GTK shell app with three primary surfaces: Home, Apps, and Settings.
- Text-first home view with time/date, direct search, and pinned app slots.
- Searchable app drawer that launches desktop apps from the live system index.
- Settings surface for theme preset, font family, and pinned-home reset.
- Meson packaging with a desktop entry and launcher wrapper.

## What it is not yet

- Not yet a full compositor or Phosh replacement.
- Not yet a lock screen, notification shade, quick settings stack, or telephony UI.
- Not yet integrated into a rebuilt Pixel 3a image.

The correct sequence is:

1. Run this as the first custom shell app on Mobian.
2. Expand it into the daily-driver launcher surface.
3. Replace or deeply integrate with the session shell/compositor layer only after the launcher behavior is solid.

## Local build

Required packages on a Debian/Mobian host:

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 meson ninja-build
```

Configure and validate:

```bash
meson setup build
python3 -m py_compile src/*.py
PYTHONPATH=src python3 -c "import main; print('ok')"
```

Run directly for iteration:

```bash
PYTHONPATH=src python3 src/main.py
```

Install system-wide:

```bash
meson install -C build
```

## Pixel 3a deployment target

Primary target OS image:

- `pixel-3a/downloads/mobian/mobian-sdm670-phosh-20260607.tar.xz`

Reference images kept on hand:

- Mobian Plasma build for comparison
- Ubuntu Touch components for service and UX reference
- postmarketOS builds for kernel and device-support reference
- Droidian image for Android-device adaptation reference

## Immediate next engineering steps

1. Add pinned-app editing and persistent ordering from inside the UI.
2. Add quick actions for lock, settings, power, brightness, audio, and network state.
3. Add a notification view and mobile-friendly system-status model.
4. Package this onto a Mobian rootfs overlay for Pixel 3a testing.
5. Decide whether the long-term shell should stay app-level on top of Phosh/phoc or move to a deeper shell/compositor stack.