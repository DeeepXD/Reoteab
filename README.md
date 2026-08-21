# Reoteab

![Reoteab icon](assets/reoteab-icon.png)

Reoteab is an unofficial community-maintained continuation of Coteab, which itself is a fork of Noteab.

The goal is to keep the macro working, fix broken functionality, maintain compatibility with current game and client changes, and gradually improve the project.

Reoteab is not affiliated with or endorsed by the Noteab or Coteab developers.

Current pre-release: Reoteab Beta 5 (`0.1.0-beta.5`).

## About

This repository is based on the complete Coteab v2.2.0 source snapshot. It includes the Python backend, React frontend, built frontend used by the desktop application, build scripts, and runtime assets.

The application and build now use the Reoteab identity while preserving the upstream source lineage and compatibility with existing user data.

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

Build the complete application with:

```powershell
.\build.ps1
```

The application loads the built frontend from `lib/dist/`, and the packaged executable is written to `dist/Reoteab.exe`.

## Requirements

- Windows
- Python and the packages listed in `requirements.txt`
- Node.js and npm when rebuilding the frontend

## Usage

For development, start the application with:

```powershell
python main.py
```

Review the configuration and calibrations before enabling automation.

## Project status

Reoteab Beta 5 is the first public pre-release. It is based on the complete Coteab v2.2.0 source and is being updated through focused maintenance changes.

## Community

- [Join the Reoteab Discord](https://discord.gg/bQNSU3pfPF)
- [Reoteab on GitHub](https://github.com/DeeepXD/Reoteab)
- [Releases](https://github.com/DeeepXD/Reoteab/releases)
- [Issues](https://github.com/DeeepXD/Reoteab/issues)

## Credits

Reoteab is based on Coteab, which is based on Noteab.

Noteab was created by the original Noteab developers. Coteab was maintained by Vapure (`@criticize.`), Akito, ManasAarohi, Matt, spacedev0572, and other contributors credited in the application. See `NOTICE` for the preserved lineage and third-party notices.

## License

Apache License 2.0 applies to the inherited Apache-covered material. Bundled third-party components and fonts retain their separate licenses. See [LICENSE](LICENSE), [NOTICE](NOTICE), and `LICENSES/`.
