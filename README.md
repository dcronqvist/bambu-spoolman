# bambu-spoolman

BambuLab integration for Spoolman.

This program will monitor a Bambulab printer and synchronize filament usage automatically to [Spoolman](https://github.com/Donkie/Spoolman). It listens for print events, parses gcode to estimate filament usage per layer, and automatically consumes filament from configured Spoolman locations as layers complete.

## Key Features

- **Location-based mapping**: Map physical AMS positions (AMS1-Slot1, AMS2-Slot3, External) to Spoolman location names
- **Automatic consumption**: Filament usage is automatically tracked and consumed from the mapped location
- **Multi-spool locations**: If multiple spools exist at a location, the system automatically consumes from the spool with the lowest ID first
- **Web UI configuration**: Simple web interface for setting up location mappings
- **RFID tray locking**: Lock specific AMS trays to prevent accidental changes
- **Multi-AMS support**: Works with multiple AMS units and external spools

## Quickstart

```sh
curl -o .env https://raw.githubusercontent.com/mrkirby153/bambu-spoolman/main/.env.example
curl -o docker-compose.yml https://raw.githubusercontent.com/mrkirby153/bambu-spoolman/main/docker-compose.yml
```

Update `.env` with the appropriate settings. See below for a list of configuration options.

Once the `.env` file is updated, start the app with `docker compose up -d`

## Configuration

Set the following environment variables:

* `SPOOLMAN_URL` -- The base URL for your Spoolman instance (i.e. `http://localhost:7912`)
  * `SPOOLMAN_VERIFY` -- Set to `false` to disable SSL verification for Spoolman requests (useful for self-signed certificates)
* `PRINTER_IP` -- The IP address of your printer
* `PRINTER_SERIAL` -- The serial number of your printer
* `PRINTER_ACCESS_CODE` -- The access code for your printer
* `BAMBU_SPOOLMAN_CONFIG` -- A directory to store the configuration file
* `SPOOLMAN_AUTO_CREATE_SPOOLS` -- Create spools when detected (legacy setting, not used with location-based mapping)
* `SPOOLMAN_AMS_FIELD_NAME` -- Spoolman field to store which AMS a spool is in (legacy setting)
* `SPOOLMAN_AMS_TRAY_NAME` -- Spoolman field to store which tray a spool is in (legacy setting)

## Usage

Once deployed, the web UI can be used to configure the mapping between physical AMS positions and Spoolman locations:

1. **AMS Configuration**: From the home page, navigate to each AMS unit and its trays
2. **Tray Configuration**: Click on an individual tray (e.g., AMS1-Slot1) to configure its mapping
3. **Location Mapping**: Select which Spoolman location (e.g., "Shelf A", "Support Materials") this physical position should use
4. **External Spool**: Click "Configure External Spool" on the home page to map the external spool position
5. **Automatic Consumption**: Once configured, filament usage is tracked automatically during prints

### Design Rationale: Location-Based Mapping

This integration uses a location-based mapping model rather than individual spool ID assignment. Here's why:

- **Physical Organization**: Your Spoolman locations correspond directly to your physical storage locations. You likely have one Spoolman location per AMS tray, one for external spools, etc.
- **Simplified Configuration**: Instead of manually assigning each filament to a specific spool ID (which requires knowing the ID before printing), you simply tell the system "when this AMS tray is used, consume from this location"
- **Resilience to Spool Changes**: If you swap out a spool at a location, the mapping still works — it will automatically consume from whichever spool is there (starting with the lowest ID if multiple exist)
- **Location Renames**: Your physical locations are stable and unlikely to change, making the mapping more reliable than spool IDs (which can be deleted or recreated in Spoolman)
- **Scalability**: Works seamlessly whether you have 1 AMS or multiple units, plus external spools — all managed through the same location-based system

### Mapping Logic

- Physical positions are identified as: `AMS{n}-Slot{n}` for tray positions (n starts at 1) or `External` for the external spool position
- Each physical position can be mapped to a Spoolman location (a string name like "Shelf A")
- When a layer is completed during a print, the system:
  1. Identifies which AMS tray was used
  2. Looks up the mapped Spoolman location
  3. Queries Spoolman for all spools at that location
  4. Consumes from the first spool (lowest ID) to ensure deterministic behavior
  5. If the location is unmapped or empty, a warning is logged and the layer continues without consuming

## Untested Things

* LAN-only prints
* Custom filament/layer change gcode (uses `M620` for filament changes and `M730` for layer changes)
* More than 2 AMS units (tested with single and dual AMS configurations)
