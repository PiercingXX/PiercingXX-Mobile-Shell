# Phase 0 Research Findings — Pixel 3a Shell

## 1. PiercingXX Android Launcher Audit

Source: `github.com/piercingxx/piercingxx-launcher`

### Gesture System

Two listener classes handle all gestures:

**`OnSwipeTouchListener`** — applied to the home screen background (full-screen catch-all):
- Uses `GestureDetector.SimpleOnGestureListener.onFling()`
- Threshold: **100px displacement AND 100px/s velocity** to trigger a swipe (axis with greater delta wins)
- Callbacks: `onSwipeUp`, `onSwipeDown`, `onSwipeLeft`, `onSwipeRight`, `onLongClick`, `onDoubleClick`, `onClick`

**`ViewSwipeTouchListener`** — applied per pinned-app text item (same thresholds, handles `isPressed` state):
- Identical gesture recognition but scoped to individual app slots

**What each gesture does on the home screen (current defaults):**

| Gesture | Default Action | Configurable? |
|---|---|---|
| Swipe up | Open app drawer | No (fixed) |
| Swipe down | Expand notification shade | Yes — can switch to search |
| Swipe left | Launch assigned app (default: camera) | Yes — any app |
| Swipe right | Launch assigned app (default: dialer) | Yes — any app |
| Long press background | Open settings | No (fixed) |
| Double tap background | Lock device (requires device admin) | Conditional on `lockModeOn` pref |
| Tap app slot (empty) | Show "long press to assign" hint | No |
| Long press app slot | Open app picker to assign/rename/clear | No |
| Swipe on app slot | Passes through to home gestures | Yes |

**Translation note for Wayland/GTK4:** `onFling()` → `Gtk.GestureSwipe`. Threshold equivalent: 100 logical px at Pixel 3a's density (~441 PPI, scale factor ~2.75) ≈ 36 device-independent units. Start with `min-velocity=200 px/s` and `min-distance=80 px` in GTK4 and tune on device.

---

### Home Screen Layout

- Up to **8 pinned app slots** (text-only, no icons)
- Widget row above pinned apps (reorderable): Clock, Date, Battery %, Weather
- Text alignment: left / center / right (user preference, default left)
- Vertical alignment: center or bottom (configurable)
- Status bar: show or hide (user preference)
- Battery widget hidden if status bar is shown (avoids duplication)
- Font options: JetBrains Mono Nerd, JetBrains Mono Regular, Space Mono — same fonts already in the Linux shell

### App Drawer (`AppDrawerFragment`)

- Alphabetical list with character-jump indicator on the right edge (A–Z, tap to jump)
- Usage-stats-based sort option (`AppUsageStats` via `UsageStatsManager`)
- Hidden apps list (apps excluded from drawer, accessible only via long-press shortcut)
- Search: prefix-first, falls through to substring

### Settings Surface

- Theme presets (stored as `APP_THEME` pref)
- Text size scale (stored as `TEXT_SIZE_SCALE` float, applied globally)
- Swipe down action: search (DuckDuckGo URL) or notifications
- Swipe left/right app assignment
- Clock app override (long press on clock to pick)
- Calendar app override (long press on date to pick)
- Lock mode on/off (double-tap to lock)
- Date/time widget visibility (on/off/date-only)
- Auto-show keyboard on drawer open

### Config persistence

All settings stored in `SharedPreferences`. Keys exactly parallel our `config.json` structure. Direct mapping:

| Android Pref key | Linux shell equivalent |
|---|---|
| `APP_THEME` | `config.theme` |
| `LAUNCHER_FONT` | `config.font_family` |
| `APP_NAME_1..8` / `APP_PACKAGE_1..8` | `config.pinned` |
| `SWIPE_DOWN_ACTION` | `gestures.swipe_down` |
| `APP_PACKAGE_SWIPE_LEFT/RIGHT` | `gestures.swipe_left/right` |
| `HOME_ALIGNMENT` | (not yet in Linux shell) |
| `STATUS_BAR` | (not yet in Linux shell) |
| `TEXT_SIZE_SCALE` | (not yet in Linux shell) |
| `DATE_TIME_VISIBILITY` | (implicit in clock widget) |

### What the Android launcher does NOT have (we're adding)

- Lock screen (it calls `DevicePolicyManager.lockNow()` to hand off to Android's lock screen)
- Notification shade (it calls `expandNotificationDrawer()`, a system API)
- App switcher / recents (calls system recents)
- Compositor-level gestures (system handles those; launcher only sees app-level touch events)
- Quick settings panel
- Telephony UI

These are all things we own in the Linux compositor stack.

---

## 2. Pixel Phone Gesture Reference

### Core Navigation Gestures (always-on, Pixel-default)

These are what users already know from their Pixel phones. We replicate this behavior at the Wayland compositor + shell layer level.

| Gesture | Motion | Action | Where handled |
|---|---|---|---|
| **Home** | Short swipe up from bottom edge | Return to home screen | phoc compositor |
| **App switcher** | Swipe up from bottom + hold (or longer swipe up) | Show recent apps | shell — `app_switcher.py` |
| **Back** | Swipe inward from left or right screen edge | Go back in current app | phoc compositor |
| **Quick app switch** | Swipe left/right along the bottom edge without lifting | Cycle through last 2 apps | phoc compositor |
| **Notification shade** | Single-finger swipe down from top edge | Reveal notification shade | shell — `notification_shade.py` |
| **Quick Settings (direct)** | Two-finger swipe down from top edge | Skip shade, open QS tiles | shell — `notification_shade.py` |
| **Quick Settings (expand)** | Second pull-down on open shade | Expand to full QS grid | shell — `notification_shade.py` |

### Pixel 3a Specific Hardware Gestures

The Pixel 3a (2019) hardware feature set is more limited than newer Pixels. Map what's actually present:

| Gesture | Hardware required | On Pixel 3a? | Action | Notes |
|---|---|---|---|---|
| **Fingerprint swipe down** | Rear fingerprint sensor | YES | Open notification shade | Pixel 3a has rear sensor; `INPUT_PROP_POINTER` via `/dev/input/event*` |
| **Double-press power** | Power button | YES | Open camera | Configurable; hook `KEY_POWER` double-press in compositor |
| **Flip to Shhh** | Accelerometer | YES | Toggle Do Not Disturb | Optional; read accel via `iio` or `sensorfw` |
| **Active Edge (squeeze)** | Pressure-sensitive sides | YES | Open assistant/action | Pixel 3a has Active Edge; `input_event` from `synaptics_dsx_htc`; map to search or assistant |
| **Quick Tap (double back-tap)** | Tap sensor / ML | NO | — | Pixel 4a 5G and later only |
| **Camera twist** | Gyroscope | YES | Switch front/rear camera | Only relevant while camera app is open |
| **Corner swipe for assistant** | Software gesture | YES | Google Assistant / search | Configurable corner zone in phoc |

### Gesture Timing Constants (from Android source, replicate in phoc/GTK4)

These are values from AOSP gesture recognizer that make gestures feel "right":

| Parameter | Value | Notes |
|---|---|---|
| Swipe threshold | 100px (logical) | Minimum displacement to count as a swipe |
| Swipe velocity threshold | 100px/s (logical) | Minimum peak velocity |
| Long press delay | 500ms | Standard Android long press |
| Double tap window | 300ms | Max gap between taps to count as double |
| Edge gesture inset (back) | 20–24dp from screen edge | Back gesture trigger zone width |
| Bottom bar height (home/switch) | ~32dp | Touch zone for home/switch gestures |

For GTK4 `Gtk.GestureSwipe`:
- Set `min-velocity` ≈ 200 logical px/s (GTK works in logical px, not physical)
- Filter by `get_velocity()` direction axis dominance same as `abs(diffX) > abs(diffY)` check in the Android listener

### Gesture Conflict Rules (from AOSP)

- Home and quick-switch gestures from the bottom are **not overridable** by apps (in Android). In our stack, phoc owns this — the compositor intercepts the touch event before the shell surface sees it.
- Back gesture trigger zones can be excluded per-region. We'll need this for the app switcher card swipe-to-close (swipe-up on a card shouldn't trigger back).
- Edge gestures only fire if touch **starts within the inset zone**. Interior swipes that happen to move toward an edge do not count.

---

## 3. What to Carry Forward

### Directly port from Android launcher

| Feature | Port as-is? | Notes |
|---|---|---|
| Gesture thresholds (100px / 100px/s) | Translate to GTK4 equivalents | Tune on device |
| 8 pinned text slots | Yes | Already in Linux shell |
| Long-press on slot → assign/rename/clear | Yes | Not yet in Linux shell |
| Swipe left/right → configurable app | Yes | Map to gesture_config.py |
| Swipe down → notifications or search (configurable) | Yes | Add to gesture_config.py |
| Double-tap → lock | Yes | Map to lock screen trigger |
| Long-press background → settings | Yes | Already planned |
| Widget row (clock, date, battery, weather) | Partial | Clock/date exist; battery/weather not yet |
| Character jump indicator in drawer | Yes | Add to apps page |
| Hidden apps list | Yes | Add to settings |
| Text size scale setting | Yes | Not yet in Linux shell |
| Home alignment (left/center/right) | Yes | Not yet in Linux shell |
| Usage-stats sort for drawer | Yes | Linux has `/proc` + `org.freedesktop.usage` or parse `.local/share/recently-used.xbel` |

### New for the Linux compositor layer (no Android equivalent)

| Feature | Source |
|---|---|
| Compositor-level back swipe | phoc — wlr-gestures or touch grab |
| Home swipe (bottom edge) | phoc |
| App switcher (hold-swipe-up) | shell — `app_switcher.py` + `wlr-foreign-toplevel-management-unstable-v1` |
| Notification shade surface | shell — `notification_shade.py` + gtk4-layer-shell |
| Lock screen surface | shell — `lock_screen.py` + gtk4-layer-shell exclusive grab |
| Two-finger QS shortcut | shell — detect at notification_shade surface level |
| Fingerprint swipe to open shade | Read `/dev/input/eventN` for `EV_REL` from fingerprint sensor; fire shade open |
| Active Edge squeeze action | Read squeeze sensor input; fire configurable action |
| Power button double-press | phoc or logind `HandlePowerKey` override |

---

## 4. Open Questions Before Phase 1

1. **OS decision**: Which has better Pixel 3a hardware support — Mobian or postmarketOS? Must boot both and test modem, WiFi, touch, Active Edge sensor access.
2. **Active Edge on Linux**: Does the squeeze sensor appear as a standard `evdev` input device on the chosen OS? Check `evtest` on device.
3. **Fingerprint reader on Linux**: Does `fprintd` or a raw `evdev` device expose the fingerprint sensor swipe gesture separately from auth? Need to test.
4. **`wlr-foreign-toplevel-management`**: Is this protocol supported in the version of phoc available on the target OS? Required for the app switcher to list running windows.
5. **PipeWire vs PulseAudio**: Which audio stack is on the target OS? Affects volume control in quick actions.
