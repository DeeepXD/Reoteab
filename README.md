# Reoteab

Reoteab is an unofficial community-maintained continuation of Coteab, which itself is a fork of Noteab.

The goal is to keep the macro working, fix broken functionality, maintain compatibility with current game and client changes, and gradually improve the project.

Reoteab is not affiliated with or endorsed by the Noteab or Coteab developers.

## About

This repository is based on the complete Coteab v2.2.0 source snapshot. It includes the Python backend, React frontend, built frontend used by the desktop application, build scripts, and runtime assets.

Internal Coteab names, paths, endpoints, and behavior remain unchanged in this baseline so future maintenance can start from the released implementation.

## Installation

Install the Python dependencies:

```powershell
pip install -r requirements.txt
```

To work on the frontend:

```powershell
cd frontend
npm install
npm run build
```

The application loads the built frontend from `lib/dist/`. See the inherited developer note and build script for the original build process.

## Requirements

- Windows
- Python and the packages listed in `requirements.txt`
- Node.js and npm when rebuilding the frontend

The development setup and build have not yet been independently verified as Reoteab.

## Usage

For development, start the inherited application with:

```powershell
python main.py
```

Review the configuration and calibrations before enabling automation. Reoteab does not yet publish its own executable release.

## Project status

Reoteab is currently in the early maintenance stage. This baseline imports the complete Coteab v2.2.0 source before further fixes and features are added.

The inherited publishing scripts still refer to Coteab repositories and must not be used to publish Reoteab without review.

## Credits

Reoteab is based on Coteab, which is based on Noteab.

Noteab was created by the original Noteab developers. Coteab was maintained by Vapure (`@criticize.`), Akito, ManasAarohi, Matt, spacedev0572, and other contributors credited in the application. See `NOTICE` for the preserved lineage and third-party notices.

## License

Apache License 2.0 applies to the inherited Apache-covered material. Bundled third-party components and fonts retain their separate licenses. See `LICENSE`, `NOTICE`, and `LICENSES/`.
