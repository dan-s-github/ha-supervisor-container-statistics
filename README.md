# Supervisor Container Statistics

[![HACS][hacsbadge]][hacs]
[![GitHub Release][releases-shield]][releases]
[![Integration Usage][downloads-shield]][downloads]

[![Home Assistant][ha-shield]][ha]
[![Python Version][python-shield]][python]
[![License][license-shield]](LICENSE)

[![Tests][tests-shield]][tests]
[![Code Style: Ruff][ruff-shield]][ruff]
[![GitHub Activity][commits-shield]][commits]

Home Assistant custom integration that exposes per-container CPU, memory, network,
and disk I/O statistics for every Supervisor container: add-ons, Home Assistant Core,
and the Supervisor itself.

It reuses the `hassio` integration's own coordinator instead of polling the Supervisor
API a second time, and attaches its sensors to the devices `hassio` already created for
each add-on/Core/Supervisor, so they show up next to Home Assistant's built-in
CPU/memory-percent sensors on the same device page. This only works on Supervised/HAOS
installations: `hassio` refuses to run anywhere else, so the config entry fails to set
up (retrying, not crashing) on a plain `hass --script develop` checkout with no
Supervisor present.

## Features

- One set of sensors per container: Memory usage, CPU usage, Network received,
  Network transmitted, Disk read, Disk write
- No extra Supervisor API polling
- Config flow with a name-based unique id
- Test suite for the config flow, setup/unload, and the sensor platform

## Notes

This integration relies on `hassio`'s internal (undocumented) coordinator and data
structures, so it may need updates if Home Assistant's `hassio` implementation changes.

## Installation

### HACS (recommended)

1. Add this repository as a custom repository in HACS.
2. Install `Supervisor Container Statistics`.
3. Restart Home Assistant.
4. Add the integration from Settings -> Devices & Services.

### Manual

1. Copy `custom_components/supervisor_container_statistics` into your Home Assistant `custom_components` directory.
2. Restart Home Assistant.
3. Add the integration from Settings -> Devices & Services.

## Development

```bash
./scripts/setup
./scripts/lint
pytest
```

[releases-shield]: https://img.shields.io/github/release/dan-s-github/ha-supervisor-container-statistics.svg?style=flat&logo=github
[releases]: https://github.com/dan-s-github/ha-supervisor-container-statistics/releases
[downloads-shield]: https://img.shields.io/badge/dynamic/json?color=41BDF5&logo=home-assistant&label=integration%20usage&suffix=%20installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=%24.supervisor_container_statistics.total
[downloads]: https://analytics.home-assistant.io/custom_integrations/supervisor_container_statistics
[commits-shield]: https://img.shields.io/github/commit-activity/y/dan-s-github/ha-supervisor-container-statistics.svg?style=flat&logo=github
[commits]: https://github.com/dan-s-github/ha-supervisor-container-statistics/commits/main
[license-shield]: https://img.shields.io/github/license/dan-s-github/ha-supervisor-container-statistics.svg?style=flat
[python-shield]: https://img.shields.io/badge/python-3.14+-blue.svg?style=flat&logo=python&logoColor=white
[python]: https://www.python.org/
[ha-shield]: https://img.shields.io/badge/Home%20Assistant-2026.3.0+-blue.svg?style=flat&logo=homeassistant&logoColor=white
[ha]: https://www.home-assistant.io/
[tests-shield]: https://img.shields.io/github/actions/workflow/status/dan-s-github/ha-supervisor-container-statistics/ci.yml?branch=main&style=flat&logo=github
[tests]: https://github.com/dan-s-github/ha-supervisor-container-statistics/actions/workflows/ci.yml
[ruff-shield]: https://img.shields.io/badge/code%20style-ruff-000000.svg?style=flat&logo=ruff&logoColor=white
[ruff]: https://github.com/astral-sh/ruff
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=flat&logo=homeassistant&logoColor=white
[issues]: https://github.com/dan-s-github/ha-supervisor-container-statistics/issues
