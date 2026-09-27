# Native UI migration checklist

This branch develops a PySide6 Qt Widgets interface alongside the existing React/pywebview application. The WebView entry point, frontend source, compiled frontend, and public build remain the working fallback until the acceptance checks below pass. A rendering-only native window is not a replacement for a functional page.

## Recovery and reference

- Original branch: `main`; original HEAD: `648f53fda60de9451b5a26e9f99721f8098a6944`.
- Original working tree contained unreleased biome/webhook reliability changes in ten tracked files and three untracked tests. These were carried intact onto `feature/native-pyside6-ui`.
- A timestamped, verified full checkout copy, complete Git bundle, file-hash manifest, original Git status and diffs, and separate private AppData configuration/preset backup are stored outside the repository in `Reoteab-native-ui-backups/native-ui-20260927-223235`. Private files and screenshots must not be committed.
- The private `ui-reference` directory contains 100%-scale captures of all 17 active navigation pages in Solar, Notice and Fishing in the nine built-in themes and the saved Custom theme. The user configuration was restored from the backup after capture.
- Original reference window: 1920 × 1032 at 100% Windows scaling. CSS sidebar: 220 px. Main content padding: 24 px. Body font: Sarpanch, 13 px; page title: 20 px. Cards have four thin accent corner brackets and square default corners. Header holds Start/Stop, status, pin, filter, Import Config, and theme selector. Higher-DPI captures and interactive state screenshots remain to be made.
- The first native Solar Notice screenshot is saved beside the original reference as `native-solar-notice-100.png`. Manual comparison found the overall geometry, Sarpanch face, Solar colors, sidebar width, and Notice wording close. Remaining differences include native text rendering and line spacing, a solid rather than gradient brand title, generic rather than SVG preset icon, missing pin control, disabled header controls, and simpler corner/hover effects. These are not accepted as final parity.

## Current interface and native parity

`frontend/src/App.tsx` owns the active page map. `frontend/src/components/Sidebar.tsx` owns navigation. `main.py:Api` exposes backend operations through pywebview. Every row below requires both screenshot and control/API regression checks before completion.

| Current page | React source | Native status | Important interactions |
| --- | --- | --- | --- |
| Notice | `NoticePage.tsx` | Pending | Bundled release notes, Discord/GitHub links |
| Webhook | `WebhookPage.tsx` | Pending | URL/config, test/status send, embed options |
| Stats | `StatsPage.tsx` | Pending | Live counters and resets |
| Status | `StatusPage.tsx` | Pending | Active modules, logs/activity, runtime status |
| Automated actions | `MiscPage.tsx` | Pending | All action settings, OCR status, keybind test, calibration |
| Macro Calibrations | `CalibrationPage.tsx` | Pending | Point/region selection, import/export, auto-calibration |
| Macro Presets | `PresetsPage.tsx` | Pending | Save/load/delete, images, current preset, compatibility |
| Remote Control | `RemoteAccessPage.tsx` | Pending | Bot settings, status, controls |
| Fishing | `FishingPage.tsx` | Pending | All fishing controls, path multiplier, calibration display |
| Merchant | `MerchantPage.tsx` | Pending | Detection and purchase settings |
| Auto Pop Buff | `AutoPopBuffPage.tsx` | Pending | Buff selection/settings |
| Auras | `AurasPage.tsx` | Pending | Aura settings and keybind test |
| Movements | `MovementsPage.tsx` | Pending | Routes, recorder, replay |
| Potion Crafting | `PotionCraftPage.tsx` | Pending | Recipes, recording and replay |
| Other Features | `OtherFeaturesPage.tsx` | Pending | Remaining feature settings |
| Customizations | `CustomizationPage.tsx` | Pending | Notification/text/appearance settings |
| Theme Design | `ThemeDesignPage.tsx` | Pending | Live preview, custom theme data, import/export |
| Calibration overlay | `CalibrationOverlay.tsx` | Pending | Full-screen point/region selection and result delivery |
| Recorder window | `RecorderWindow.tsx` | Pending | Start/stop/replay and camera alignment |
| Biome confirmation | `BiomeConfirmWindow.tsx` | Pending | Time-bounded rare-biome decision |

`CreditsPage.tsx`, `DonationsPage.tsx`, `PuzzlePage.tsx`, and `PathingPage.tsx` exist but are not in the active page map/navigation. Their presence alone is not a reason to expose new functionality.

## Theme parity

The built-in themes are Midnight, Solar, Arctic, Neon, Sunset, Ocean, Forest, Cyberpunk, and Lavender. Their source tokens are in `frontend/src/App.css`: root/sidebar/main/card/input colors, accent and glow, text, border, corner color, radii, and shadow. The saved Custom theme is selected with `selected_theme = "custom"` and data in `custom_theme_data` plus related config keys.

Custom data includes CSS variable overrides, `custom_css`/`raw_custom_css`, embedded custom font, font weight/style, sidebar labels/icons, title/version, solid/image/animated-gradient background, and gradient colors. Config/theme import and export must keep the existing format. Arbitrary CSS rules cannot be directly executed by Qt Widgets; a faithful mapping needs explicit tests, with unavoidable differences reported rather than silently ignored.

| Theme | 100% reference | Native visual check | Theme persistence |
| --- | --- | --- | --- |
| Midnight | Notice, Fishing, Theme Design | Pending | Pending |
| Solar | All 17 pages, Fishing | Pending | Pending |
| Arctic | Notice, Fishing | Pending | Pending |
| Neon | Notice, Fishing | Pending | Pending |
| Sunset | Notice, Fishing | Pending | Pending |
| Ocean | Notice, Fishing | Pending | Pending |
| Forest | Notice, Fishing | Pending | Pending |
| Cyberpunk | Notice, Fishing | Pending | Pending |
| Lavender | Notice, Fishing | Pending | Pending |
| Custom | Notice, Fishing | Pending | Pending |

## Backend boundaries and risks

- `main.py:main()` creates the WebView and starts the tracker in `_background_init`. The native entry point must avoid importing `main.py` just to construct a window because that imports pywebview.
- `Api.set_biome_detection()` starts/stops biome detection and fishing. Tracker callbacks currently call `_safe_eval_js()` for status, config, biome, shortcuts, and failsafe warnings. This is a synchronous UI call from backend work and must be replaced at the boundary with bounded, non-blocking publication before native automation is enabled.
- `_request_biome_confirm()` creates a separate WebView and waits for a response (with timeout). The native equivalent must retain the timeout and never stall detection/webhooks indefinitely.
- `_open_recorder()` and Tk calibration windows are other UI-specific paths. `CalibrationManager` currently uses a WebView window for hide/show. Keep algorithms and config data, adapt only presentation.
- A same-process Qt shell is not crash isolation. A separate backend process would provide stronger protection, but input/focus/hotkeys, tracker lifetime, and shutdown need explicit IPC tests. Do not claim isolation until process-failure tests pass.
- The development shell runs from `native_main.py`; it imports Qt Widgets, not `main.py` or pywebview. Its Start control and unmigrated pages are inactive. `build-native-dev.ps1` writes `dist/native-dev/Reoteab-Native-Dev.exe`, never the public EXE. A first package attempt failed to import QtCore because ambient `PATH` caused PyInstaller to collect an incompatible ICU DLL from a separate Poppler runtime. A process-local clean `PATH` removed that DLL; the rebuilt one-file Qt shell launched. Do not reuse the ambient build command without this isolation.
- Existing reliability work in the dirty tree includes bounded transition queues, webhook/screenshot timeouts and worker lifecycle changes. Do not replace these files wholesale while moving the UI boundary.
- Preserve one shared config store (`biome_tracker/config.py`), AppData location, presets, and legacy import behavior. Avoid separate native-only config state.

## Migration gates

1. Capture and audit the old UI, themes, API surface, and private backup. **Reference capture complete at 100%; 125%/150% and secondary states pending.**
2. Build an independent native development shell and compare its frame, navigation, header, Notice page, font and colors. **Initial shell and Solar Notice comparison complete; visual differences remain.** Keep automation controls inactive until safely connected.
3. Connect configuration/status via a bounded worker-to-Qt signal boundary; test a blocked/closed UI while backend jobs continue. Assess separate-process backend before claiming crash isolation.
4. Migrate pages in groups; check every visible control, saved value, theme, visual reference, and backend call after each group.
5. Replace calibration, recorder, and rare-biome popups without changing their algorithms or timeouts.
6. Run full Python and UI regression suites, DPI/theme screenshot comparisons, repeated Start/Stop/reconnect/failure tests, packaged smoke test, and extended idle/active soak measurements.
7. Only after full acceptance, switch the production entry/build and remove WebView dependency. Keep the old source/history recoverable.
