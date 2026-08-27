import json
import os
from loguru import logger

EXTERNAL_SPOOL_ID = 255


def get_configuration_path(path):
    configuration_directory = os.environ.get("BAMBU_SPOOLMAN_CONFIG")
    if configuration_directory is None:
        return path
    return os.path.join(configuration_directory, path)


def _settings_file():
    return get_configuration_path("settings.json")


def save_settings(settings):
    with open(_settings_file(), "w") as f:
        json.dump(settings, f)


def load_settings():
    settings_file_path = _settings_file()
    if os.path.exists(settings_file_path):
        with open(settings_file_path) as f:
            data = json.load(f)

            if os.environ.get("SPOOLMAN_SPOOL_FIELD_NAME") is None:
                data["locked_trays"] = []
            return data
    return {"trays": {}, "tray_count": 0, "location_mapping": {}}


def tray_id_to_location_name(tray_id):
    """
    Convert a tray_id to a physical location name.
    Format: "AMS{ams_index+1}-Slot{slot_index+1}"
    
    Args:
        tray_id: 0-indexed tray ID or 255 for external spool
        
    Returns:
        Location name string (e.g., "AMS1-Slot1") or "External" for external spool
    """
    if tray_id == EXTERNAL_SPOOL_ID:
        return "External"
    
    ams_index = tray_id // 4
    slot_index = tray_id % 4
    return f"AMS{ams_index + 1}-Slot{slot_index + 1}"


def get_location_for_tray_id(settings, tray_id):
    """
    Get the Spoolman location name mapped to a physical tray position.
    
    Args:
        settings: Settings dict
        tray_id: 0-indexed tray ID
        
    Returns:
        Location name string or None if not mapped
    """
    location_mapping = settings.get("location_mapping", {})
    physical_location = tray_id_to_location_name(tray_id)
    return location_mapping.get(physical_location)
