# Changelog <!-- omit from toc -->

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- Refactor code for requests.
- Use a proper logging module.
- Use proper argument conventions (-h, --help, case) and maybe an argument parser.
- Maybe use a different way to `sys.exit()` known errors.

## [1.1.0] - 2023-08-07

### Added

- This CHANGELOG.md file.
- GitHub Templates for Bug Reports and Feature Requests.
- Syncing behavior section in the README.md file.
- More info for the `-PlexUser` argument in the README.md file and when using the `-h` argument.

### Fixed

- Sync collections now correctly works.
- Sentences in README.md file now go correctly to the next line and grammar mistakes.
- Syncing collections now correctly works.
- Now correctly log the arguments passed before calling `subprocess.check_output()`.
- Fixed some puctuation mistakes.

### Changed

- Argument for the recently added in the README.md file.
- Syncing collection can now either find the owner username, sync all users found in the env, or sync a list of users.
- Sorted imports.
- Now gets `HEADERS` from a function in utilities.py for less redundancy.

### Removed

- Unused import os in scrobble.py.
- Unused `arguments_string` variable in the TautulliPython2Trakt.py file.

## [1.0.0] - 2023-05-27

### Added

- Initial release of TautulliPython2Trakt v1.0.0.

[unreleased]: https://github.com/TheGeeKing/TautulliPython2Trakt/compare/v1.1.0...main
[1.1.0]: https://github.com/TheGeeKing/TautulliPython2Trakt/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/TheGeeKing/TautulliPython2Trakt/releases/tag/v1.0.0
