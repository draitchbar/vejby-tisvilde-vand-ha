# Vejby Tisvilde Vand Integration for Home Assistant

This custom integration allows you to monitor your water consumption from Vejby Tisvilde Vand's customer portal in Home Assistant.

## Features

- **4 sensors per water meter**: latest (today so far), daily (yesterday), month-to-date, year-to-date consumption
- **Multiple locations**: supports multiple water meters/locations
- **Automatic updates**: data refreshes every 30 minutes
- **Easy setup**: configured through the Home Assistant UI

## Installation

### Manual Installation

1. Copy all files from the repo root into `<HA config dir>/custom_components/vejby_tisvilde_vand/`
2. Restart Home Assistant
3. Go to **Settings** → **Devices & Services**
4. Click **Add Integration**
5. Search for "Vejby Tisvilde Vand"

### HACS Installation (if published)

1. Open HACS
2. Go to Integrations → three dots → Custom repositories
3. Add the repository URL
4. Install "Vejby Tisvilde Vand"
5. Restart Home Assistant

## Configuration

After installation, add the integration through the UI and enter your Vejby Tisvilde Vand customer portal credentials (email and password). The integration will automatically discover your devices and create sensors for each water meter.

## Sensors

Four sensors are created per water meter:

| Sensor | Unique ID suffix | State Class | Description |
|---|---|---|---|
| Latest Consumption | `latest_consumption` | `measurement` | Midnight → now (today) |
| Daily Consumption | `daily_consumption` | `total` (`last_reset` = midnight today) | Full previous day |
| Monthly Consumption | `monthly_consumption` | `total` (`last_reset` = 1st of month) | 1st of month → now |
| Yearly Consumption | `yearly_consumption` | `total` (`last_reset` = Jan 1st) | Jan 1st → now |

All sensors use **cubic meters (m³)** and device class **Water**.

**Common attributes** (all sensors):
- `device_id`: unique device identifier
- `location`: location/address name
- `device_type`: type of water meter

## Example Usage

### Display today's consumption

```yaml
type: entity
entity: sensor.your_location_water_meter_latest_consumption
name: Today's Water Usage
icon: mdi:water
```

### Alert on high daily usage

```yaml
automation:
  - alias: "High Water Usage Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.your_location_water_meter_latest_consumption
        above: 1.0  # 1 cubic meter
    action:
      - service: notify.mobile_app
        data:
          message: "High water usage detected today!"
```

### Track weekly consumption with Utility Meter

```yaml
utility_meter:
  weekly_water_consumption:
    source: sensor.your_location_water_meter_latest_consumption
    cycle: weekly
```

## Troubleshooting

**Authentication errors**: verify credentials at https://vejbytisvildevand.bdforsyning.dk. The integration will prompt for re-authentication if the token expires.

**No sensors after setup**: check that you have active water meters in the customer portal, and review Home Assistant logs for errors.

**Data not updating**: the integration polls every 30 minutes. Check logs for connection errors.

## API Information

- **Base URL**: `https://vejbytisvildevand.bdforsyning.dk`
- **Authentication**: Bearer token (auto-refreshed)
- **Update interval**: 30 minutes

## Development

### Architecture

- `api.py` — `VejbyTisvildeVandApi`: async HTTP client, injectable `HttpClient` and `DateRangeProvider`
- `http_client.py` — `HttpClient` protocol + `AioHttpClient` implementation
- `date_ranges.py` — `DateRangeProvider` protocol + `TimezoneAwareDateRangeProvider`
- `models.py` — `Device` and `CoordinatorData` dataclasses
- `__init__.py` — coordinator, wires everything together
- `sensor.py` — four `CoordinatorEntity` sensor subclasses
- `config_flow.py` — UI config flow with reauth support

### Running tests

```bash
# Create venv and install test dependencies (first time only)
python3 -m venv .venv
.venv/bin/pip install -r requirements-test.txt

# Run mocked unit tests (no credentials needed)
cd tests && ../.venv/bin/pytest -v -k "not live"

# Run functional tests against the real API
cp .env.example .env          # then fill in your credentials
cd tests && ../.venv/bin/pytest test_live_api.py -v
```

> **Note:** `pytest` must be run from the `tests/` directory. Running it from the repo root will fail because the repo root is also the integration package (`__init__.py` is there), which conflicts with pytest's package import machinery.

## Privacy & Security

- Credentials are stored securely in Home Assistant's configuration store
- All API communication uses HTTPS
- No data is sent to third parties

## License

MIT License — see LICENSE file for details
