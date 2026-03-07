# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Home Assistant custom integration for Vejby Tisvilde Vand water utility. It polls the customer portal API every 30 minutes and exposes water consumption sensors.

## Installation / Deployment

There is no build step. To deploy, copy all files into `<HA config dir>/custom_components/vejby_tisvilde_vand/` and restart Home Assistant.

There are no automated tests. Manual testing requires a live Home Assistant instance with valid credentials.

## Architecture

The integration follows the standard HA coordinator pattern:

- **`__init__.py`** — Entry point. Sets up `VejbyTisvildeVandDataUpdateCoordinator`, which fetches all usage data (daily, yesterday, monthly, yearly) for all devices on each 30-minute poll. Passes timezone from HA config to the API client.
- **`api.py`** — `VejbyTisvildeVandApi`: async HTTP client using `aiohttp`. Handles token-based auth (Bearer), auto-reauthenticates on 401. All date ranges are computed in the local timezone (via `ZoneInfo`) then converted to UTC before sending to the API.
- **`sensor.py`** — Creates 4 `CoordinatorEntity` sensor subclasses per device: daily, yesterday, monthly, yearly consumption. All read from `coordinator.data` dict.
- **`config_flow.py`** — UI config flow with reauth support. Validates credentials on setup.
- **`const.py`** — Central place for `DOMAIN`, `API_BASE_URL`, `API_TIMEOUT`, `UPDATE_INTERVAL`.

## API details

Base URL: `https://vejbytisvildevand.bdforsyning.dk`

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/Customer/login` | POST | Get `AuthToken` |
| `/api/Customer` | GET | Get device list (JSON keys are PascalCase: `Locations`, `Devices`, `Id`, `Address`, `DeviceType`) |
| `/api/Stats/usage/{locationId}/devices` | POST | Get usage data |

The `locationId` in the usage URL comes from `Locations[].LocationId` in the `/api/Customer` response (not the top-level `Id`). The coordinator groups devices by location and makes one usage call per location.

Usage request body fields to be aware of:
- `QuantityType`: `"WaterVolume"` (singular — not "WaterVolumes")
- `Unit`: `"KubicMeter"` (not "CubicMeter")
- `Interval`: `"Hourly"` / `"Daily"` / `"Monthly"`
- `From` / `To`: UTC ISO 8601 strings
- Response: `{ "TotalUsage": float, "Buckets": [...], ... }` — returns a single aggregate (not per-device), so the total is assigned to `device_ids[0]`.
