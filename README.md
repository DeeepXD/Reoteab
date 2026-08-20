<p align="center">
  <img src="assets/reoteab-icon.png" width="140" alt="Reoteab">
</p>

<h1 align="center">Reoteab</h1>

<p align="center">
  <b>A maintained continuation of the Noteab → Coteab Sol's RNG macro.</b>
</p>

<p align="center">
  <a href="https://github.com/DeeepXD/Reoteab/releases">
    <img src="https://img.shields.io/github/v/release/DeeepXD/Reoteab?style=flat-square&label=release">
  </a>
  <a href="https://github.com/DeeepXD/Reoteab/releases">
    <img src="https://img.shields.io/github/downloads/DeeepXD/Reoteab/total?style=flat-square&label=downloads">
  </a>
  <img src="https://img.shields.io/badge/platform-Windows%2010%20%2F%2011-0078D4?style=flat-square&logo=windows11&logoColor=white">
  <img src="https://img.shields.io/badge/license-Apache--2.0-blue?style=flat-square">
  <a href="https://github.com/DeeepXD/Reoteab/stargazers">
    <img src="https://img.shields.io/github/stars/DeeepXD/Reoteab?style=flat-square&label=stars">
  </a>
</p>

<p align="center">
  <a href="https://github.com/DeeepXD/Reoteab/releases"><b>Download</b></a>
  ·
  <a href="https://github.com/DeeepXD/Reoteab/issues"><b>Report a bug</b></a>
  ·
  <a href="https://discord.gg/bQNSU3pfPF"><b>Discord</b></a>
</p>

---

## What is Reoteab?

Reoteab is a community-maintained continuation of the Sol's RNG macro lineage that started with **Noteab** and later continued through **Coteab**.

The project exists because the old macro was still useful even after active development slowed down. Instead of throwing everything away and starting from zero, Reoteab keeps the parts that already work and focuses on fixing bugs, improving reliability, and keeping the macro usable as Roblox and Sol's RNG change.

The goal is pretty simple: keep the macro practical, keep changes understandable, and avoid rewriting working systems for no reason.

---

## Features

Reoteab currently includes support for:

- Fishing automation
- Merchant checks
- Merchant Teleporter handling
- Mari, Jester, and Rin interaction
- Configurable merchant purchases
- Item-name OCR
- Biome detection
- Discord webhook notifications
- Discord remote control
- Route and movement automation
- Obby-related movement
- Calibration presets
- Calibration import/export
- Recovery and failsafe behavior
- Configurable timings and macro settings
- Automatic update support

Some features rely heavily on screen position, OCR, and Roblox UI state, so calibration matters a lot.

---

## Download

The latest public build can be found on the Releases page:

### [Download Reoteab →](https://github.com/DeeepXD/Reoteab/releases)

The normal release file is:

```text
Reoteab.exe
```

> [!IMPORTANT]
> Download Reoteab from this repository or another source officially linked by the project.
>
> Random reuploads, modified executables, and unofficial mirrors cannot be verified.

Testing builds may be available before a normal release. If you are not actively testing a new fix, use the latest normal release.

---

## Requirements

Reoteab is intended for:

- Windows 10 or Windows 11
- Roblox
- Microsoft Edge WebView2 Runtime
- Windows OCR/language components for OCR-based features

For the most predictable calibration behavior:

```text
Windows display scaling: 100%
```

Other scaling values may work, but screen positions and OCR regions can differ.

---

## Getting started

1. Download `Reoteab.exe` from Releases.
2. Put it inside its own folder.
3. Launch Reoteab.
4. Configure the features you actually want to use.
5. Import or create a calibration matching your setup.
6. Configure webhooks or remote control if you want them.
7. Start the macro.

You do not need to enable every feature.

If something clicks in the wrong place or OCR reads the wrong part of the screen, check calibration before assuming the macro itself is broken.

---

## Calibration

A lot of Reoteab works by interacting with visible Roblox UI elements.

That means a calibration made for one setup may not behave correctly on another.

When sharing or downloading a calibration, pay attention to:

- Resolution
- Windows scaling
- Fullscreen or windowed Roblox
- Windows version
- Reoteab version

A useful calibration label looks like:

```text
1920x1080
100% Scaling
Fullscreen
Windows 11
TESTED
```

If the macro:

- clicks beside buttons
- cannot read merchant names
- cannot find item names
- opens the wrong menu
- misses fishing UI elements

then calibration is one of the first things worth checking.

Community-tested calibrations may also be shared through the Reoteab Discord.

---

## Merchant automation

Merchant handling is one of the more timing-sensitive parts of the macro.

Reoteab can:

- use the Merchant Teleporter
- position the camera before teleporting
- detect supported merchants
- interact with merchant dialogue
- read item names with OCR
- purchase configured items
- interrupt fishing for a merchant check
- return to fishing afterward

Merchant bugs can sometimes look like fishing bugs because the two systems interact.

If you report a merchant issue, include whether it happened during a normal merchant check or while fishing.

---

## Fishing

Fishing is designed to work for longer sessions and alongside the rest of Reoteab.

The fishing loop handles things such as:

- casting
- catch detection
- post-catch handling
- restarting the next attempt
- merchant interruptions
- returning from merchant checks
- failsafe recovery

For this type of automation, automated tests are useful but they are not the whole story.

Roblox UI behavior, timing, focus, mouse movement, and loading delays can behave differently in a real session, so important fishing and merchant changes are also tested in Roblox whenever possible.

---

## Discord integration

Reoteab supports Discord webhooks for supported notifications such as biome events.

Optional Discord-based remote control is also available.

Never share private credentials when asking for help.

Before uploading a config, log, screenshot, or video, check that it does not contain:

```text
Discord bot tokens
Webhook URLs
Private links
Authentication information
Anything else you do not want public
```

If a token or webhook URL is accidentally exposed, replace it instead of continuing to use the same one.

---

## Logs

Logs are useful when something behaves differently from what you expected.

If a bug happens repeatedly, try to save the section of the log around the time it occurred.

For UI issues, a short video is often even more useful because it can show:

- which menu was open
- where the mouse clicked
- what the camera was doing
- whether Roblox had focus
- what happened immediately before the bug

A good report usually needs less guessing and more reproduction.

---

## Reporting a bug

Please include enough information for someone else to reproduce the problem.

A useful report looks like:

```text
Reoteab version:
Feature:
Resolution:
Windows scaling:
Roblox mode:
Windows version:

What I was doing:

What happened:

What should have happened:

Does it happen every time?

Relevant logs:

Screenshot / video:
```

Example:

```text
Version: Private Beta 5
Feature: Fishing -> Merchant
Resolution: 1920x1080
Scaling: 100%
Mode: Fullscreen

What happened:
The merchant wasn't found and the macro reopened inventory before
returning to fishing.

Expected:
Finish the merchant check and resume fishing normally.

Reproduced:
3/3 attempts
```

Reports like this are much easier to work with than:

```text
merchant broken
```

GitHub issues:

### [Report an issue →](https://github.com/DeeepXD/Reoteab/issues)

---

## Building from source

The repository is roughly structured like this:

```text
Reoteab/
├─ biome_tracker/      Core automation logic
├─ frontend/           Reoteab interface
├─ assets/             Runtime assets
├─ tests/              Automated tests
├─ main.py             Application entry point
├─ build.ps1           Windows build script
├─ LICENSE
└─ NOTICE
```

On Windows, the normal build command is:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

A successful build should create:

```text
dist\Reoteab.exe
```

If you are testing a freshly built executable, check that you are actually launching the new file and not an older copy from somewhere else.

---

## Contributing

Contributions, useful bug reports, and tested calibration presets are welcome.

For code changes, the preferred approach is:

```text
Reproduce the problem
        ↓
Trace the actual code path
        ↓
Find the cause
        ↓
Make the smallest practical fix
        ↓
Run relevant tests
        ↓
Test in Roblox when needed
```

A fix for one bad click should usually stay a fix for one bad click.

Avoid turning small bugs into large rewrites unless the existing design genuinely requires it.

Focused commits are easier to review, test, and revert if something behaves differently in-game.

---

## Antivirus detections

Reoteab is automation software packaged as a Windows executable.

Programs that:

- simulate keyboard input
- move/click the mouse
- inspect windows
- automate another application

can sometimes trigger antivirus heuristics.

The source code is available in this repository so users can inspect the project and build it themselves.

This does not mean every antivirus warning should automatically be ignored. Make sure the file came from the official Reoteab project before running it.

---

## Project history

Reoteab is not a from-scratch rewrite.

It continues work from the:

```text
Noteab → Coteab → Reoteab
```

lineage.

Original licensing, copyright notices, attribution, and other required upstream information remain preserved.

Reoteab being the current project name does not remove the history of the code it came from.

For the actual legal information, see:

- [`LICENSE`](LICENSE)
- [`NOTICE`](NOTICE)

---

## Links

**Releases**  
https://github.com/DeeepXD/Reoteab/releases

**Issues**  
https://github.com/DeeepXD/Reoteab/issues

**Source**  
https://github.com/DeeepXD/Reoteab

**Discord**  
https://discord.gg/bQNSU3pfPF

---

<p align="center">
  <b>Reoteab</b><br>
  <sub>Community maintained. Not affiliated with Roblox or the Sol's RNG developers.</sub>
</p>
