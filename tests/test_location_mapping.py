"""
Tests for location-based spool mapping.
Tests the conversion of physical AMS positions to Spoolman locations
and spool consumption logic.
"""

import pytest
from bambu_spoolman.settings import (
    tray_id_to_location_name,
    get_location_for_tray_id,
    EXTERNAL_SPOOL_ID,
)


class TestTrayIdToLocationName:
    """Test conversion of tray ID to physical location name."""

    def test_external_spool_id(self):
        """External spool should map to 'External'."""
        assert tray_id_to_location_name(EXTERNAL_SPOOL_ID) == "External"

    def test_ams1_slot1(self):
        """Tray ID 0 should map to AMS1-Slot1."""
        assert tray_id_to_location_name(0) == "AMS1-Slot1"

    def test_ams1_slot4(self):
        """Tray ID 3 should map to AMS1-Slot4."""
        assert tray_id_to_location_name(3) == "AMS1-Slot4"

    def test_ams2_slot1(self):
        """Tray ID 4 should map to AMS2-Slot1."""
        assert tray_id_to_location_name(4) == "AMS2-Slot1"

    def test_ams2_slot4(self):
        """Tray ID 7 should map to AMS2-Slot4."""
        assert tray_id_to_location_name(7) == "AMS2-Slot4"

    def test_ams3_slot2(self):
        """Tray ID 9 should map to AMS3-Slot2."""
        assert tray_id_to_location_name(9) == "AMS3-Slot2"


class TestGetLocationForTrayId:
    """Test retrieving Spoolman location from settings."""

    def test_mapped_location(self):
        """Should return mapped Spoolman location."""
        settings = {
            "location_mapping": {
                "AMS1-Slot1": "Shelf A",
                "AMS1-Slot2": "Support Materials",
            }
        }
        # Tray ID 0 -> AMS1-Slot1 -> "Shelf A"
        assert get_location_for_tray_id(settings, 0) == "Shelf A"
        # Tray ID 1 -> AMS1-Slot2 -> "Support Materials"
        assert get_location_for_tray_id(settings, 1) == "Support Materials"

    def test_unmapped_location(self):
        """Should return None if location not mapped."""
        settings = {
            "location_mapping": {
                "AMS1-Slot1": "Shelf A",
            }
        }
        # Tray ID 1 (AMS1-Slot2) is not in mapping
        assert get_location_for_tray_id(settings, 1) is None

    def test_empty_location_mapping(self):
        """Should return None if location_mapping is empty."""
        settings = {"location_mapping": {}}
        assert get_location_for_tray_id(settings, 0) is None

    def test_no_location_mapping_key(self):
        """Should return None if location_mapping key doesn't exist."""
        settings = {}
        assert get_location_for_tray_id(settings, 0) is None

    def test_external_spool_mapping(self):
        """Should work with external spool location."""
        settings = {
            "location_mapping": {
                "External": "External Spool Holder",
            }
        }
        assert get_location_for_tray_id(settings, EXTERNAL_SPOOL_ID) == "External Spool Holder"
