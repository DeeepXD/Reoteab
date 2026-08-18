# Reoteab

Reoteab is an unofficial community-maintained continuation of Coteab, which itself is a fork of Noteab.

The goal is to keep the macro working, fix broken functionality, maintain compatibility with current game and client changes, and gradually improve the project.

Reoteab is not affiliated with or endorsed by the Noteab or Coteab developers.

## About

This repository begins with the files distributed for Coteab v2.2.0. The supplied baseline contains Coteab's Python bootstrapper and supporting runtime data; it does not contain the full macro implementation from Coteab's separate `Coteab-Migrated` source branch.

The current bootstrapper still retrieves `CoteabMacro.exe` from the archived Coteab releases. That behavior is preserved for baseline comparison and has not yet been converted into a Reoteab release process.

## Installation

There is no Reoteab release package yet. Clone or download the repository to inspect and work on the baseline.

Do not treat executables downloaded by the inherited bootstrapper as Reoteab builds. Review the script and the upstream release before running it.

## Requirements

- Windows
- Python 3 for the inherited bootstrapper
- An internet connection for the bootstrapper's GitHub release lookup

The broader Python package list inherited from Coteab is recorded in `requirements.txt`, but the full application source is not part of this baseline and the list has not yet been validated for Reoteab.

## Usage

The initial repository is intended as a maintenance baseline. Normal Reoteab usage instructions will be added after the application source and build process have been verified.

## Project status

Reoteab is currently in the early maintenance stage. The initial release establishes a clean baseline from Coteab v2.2.0 before further fixes and features are added.

## Credits

Reoteab is based on Coteab, which is based on Noteab.

Noteab was created by the original Noteab developers. Coteab was maintained by Vapure (also credited upstream as xVapure, criticize., or C), Akito/Akitosama, and other Coteab contributors. See `NOTICE` and the inherited attribution files for details.

## License

Apache License 2.0 applies to the inherited Apache-covered material. Some referenced or bundled third-party material has separate terms, and some upstream assets were excluded because their redistribution status could not be established. See `LICENSE` and `NOTICE`.
