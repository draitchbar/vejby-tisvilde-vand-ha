# Vejby Tisvilde Vand Integration for Home Assistant

This custom integration allows you to monitor your water consumption from Vejby Tisvilde Vand's customer portal in Home Assistant.

## Features

- **Daily Consumption Sensor**: Track your daily water usage in real-time
- **Multiple Devices**: Support for multiple water meters/locations
- **Automatic Updates**: Data refreshes every 30 minutes
- **Easy Setup**: Simple configuration through Home Assistant UI

## Installation

### Manual Installation

1. Copy the `custom_components/vejby_tisvilde_vand` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Go to **Settings** → **Devices & Services**
4. Click **Add Integration**
5. Search for "Vejby Tisvilde Vand"

### HACS Installation (if published)

1. Open HACS
2. Go to Integrations
3. Click the three dots in the top right
4. Select "Custom repositories"
5. Add the repository URL
6. Install "Vejby Tisvilde Vand"
7. Restart Home Assistant

## Configuration

1. After installation, add the integration through the UI
2. Enter your Vejby Tisvilde Vand customer portal credentials:
   - **Email**: Your login email
   - **Password**: Your password
3. Click Submit

The integration will automatically discover your devices and create sensors for each water meter.

## Sensors

### Daily Consumption Sensor

- **Entity ID**: `sensor.{location}_{device}_daily_consumption`
- **Unit**: Cubic meters (m³)
- **Device Class**: Water
- **State Class**: Total Increasing
- **Update Interval**: 30 minutes

The sensor shows water consumption from midnight (00:00) until the current time, updated every 30 minutes.

**Example**: If the sensor shows `0.145`, this means 0.145 m³ (145 liters) have been consumed today.

**Attributes**:
- `device_id`: The unique device identifier
- `location`: Location name

## Example Usage

### Display Daily Consumption

```yaml
type: entity
entity: sensor.your_location_water_meter_daily_consumption
name: Today's Water Usage
icon: mdi:water
```

### Create Automation for High Usage

```yaml
automation:
  - alias: "High Water Usage Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.your_location_water_meter_daily_consumption
        above: 1.0  # 1 cubic meter
    action:
      - service: notify.mobile_app
        data:
          message: "High water usage detected today!"
```

### Track Weekly Consumption with Utility Meter

```yaml
utility_meter:
  weekly_water_consumption:
    source: sensor.your_location_water_meter_daily_consumption
    cycle: weekly
```

## Troubleshooting

### Authentication Errors

If you receive authentication errors:
1. Verify your credentials are correct
2. Check that you can log in to the customer portal at https://vejbytisvildevand.bdforsyning.dk
3. The integration will prompt for re-authentication if credentials expire

### No Devices Found

If no sensors appear after setup:
1. Ensure you have active water meters registered in your customer portal
2. Check Home Assistant logs for any error messages
3. Try reloading the integration

### Data Not Updating

If sensor data isn't updating:
1. Check your internet connection
2. Verify the API is accessible
3. Check Home Assistant logs for connection errors
4. The integration updates every 30 minutes by default

## API Information

This integration uses the Vejby Tisvilde Vand Customer Portal API:
- **Base URL**: `https://vejbytisvildevand.bdforsyning.dk`
- **Authentication**: Token-based (Bearer)
- **Update Frequency**: 30 minutes (configurable in code)

## Privacy & Security

- Your credentials are stored securely in Home Assistant's configuration
- All communication with the API uses HTTPS
- No data is sent to third parties

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

## Credits

Developed for the Home Assistant community to integrate with Vejby Tisvilde Vand's water monitoring system.

## License

MIT License - See LICENSE file for details
