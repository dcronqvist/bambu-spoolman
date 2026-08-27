"""
Tests for consumption logic with location-based mapping.
Tests that spools are correctly selected and consumed based on location.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from bambu_spoolman.broker.filament_usage_tracker import FilamentUsageTracker
from bambu_spoolman.settings import get_location_for_tray_id


class TestFilamentConsumptionWithLocations:
    """Test spool consumption using location-based mapping."""

    @patch("bambu_spoolman.broker.filament_usage_tracker.new_client")
    @patch("bambu_spoolman.broker.filament_usage_tracker.load_settings")
    def test_consume_from_first_spool_at_location(self, mock_load_settings, mock_new_client):
        """Should consume from the first (lowest ID) spool at a location."""
        # Setup
        tracker = FilamentUsageTracker()
        
        # Configure mock settings
        mock_load_settings.return_value = {
            "location_mapping": {
                "AMS1-Slot1": "Shelf A",
            }
        }
        
        # Configure mock spoolman client
        mock_client = Mock()
        mock_new_client.return_value = mock_client
        tracker.spoolman_client = mock_client
        
        # Configure spools at location (unsorted, should be sorted by ID)
        spools = [
            {"id": 10, "filament": {"material": "PLA"}},
            {"id": 5, "filament": {"material": "PLA"}},
            {"id": 15, "filament": {"material": "PLA"}},
        ]
        mock_client.get_spools_by_location.return_value = [
            {"id": 5, "filament": {"material": "PLA"}},  # Already sorted
            {"id": 10, "filament": {"material": "PLA"}},
            {"id": 15, "filament": {"material": "PLA"}},
        ]
        
        # Setup tracker state
        tracker.active_model = {0: {0: 100}}  # Layer 0, filament 0: 100mm
        tracker.using_ams = True
        tracker.ams_mapping = [0]  # Filament 0 uses tray 0 (AMS1-Slot1)
        
        # Execute
        tracker._spend_filament_for_layer(0)
        
        # Verify: should consume from spool ID 5 (lowest ID)
        mock_client.get_spools_by_location.assert_called_once_with("Shelf A")
        mock_client.consume_spool.assert_called_once_with(5, length=100)

    @patch("bambu_spoolman.broker.filament_usage_tracker.new_client")
    @patch("bambu_spoolman.broker.filament_usage_tracker.load_settings")
    def test_skip_consumption_when_location_unmapped(self, mock_load_settings, mock_new_client):
        """Should skip consumption if location is not mapped."""
        # Setup
        tracker = FilamentUsageTracker()
        
        # Configure mock settings with empty location_mapping
        mock_load_settings.return_value = {
            "location_mapping": {}
        }
        
        # Configure mock spoolman client
        mock_client = Mock()
        mock_new_client.return_value = mock_client
        tracker.spoolman_client = mock_client
        
        # Setup tracker state
        tracker.active_model = {0: {0: 100}}  # Layer 0, filament 0: 100mm
        tracker.using_ams = True
        tracker.ams_mapping = [0]  # Filament 0 uses tray 0 (AMS1-Slot1)
        
        # Execute
        tracker._spend_filament_for_layer(0)
        
        # Verify: should NOT call get_spools_by_location or consume_spool
        mock_client.get_spools_by_location.assert_not_called()
        mock_client.consume_spool.assert_not_called()

    @patch("bambu_spoolman.broker.filament_usage_tracker.new_client")
    @patch("bambu_spoolman.broker.filament_usage_tracker.load_settings")
    def test_skip_consumption_when_location_has_no_spools(self, mock_load_settings, mock_new_client):
        """Should skip consumption if location has no spools."""
        # Setup
        tracker = FilamentUsageTracker()
        
        # Configure mock settings
        mock_load_settings.return_value = {
            "location_mapping": {
                "AMS1-Slot1": "Shelf A",
            }
        }
        
        # Configure mock spoolman client with empty location
        mock_client = Mock()
        mock_new_client.return_value = mock_client
        tracker.spoolman_client = mock_client
        mock_client.get_spools_by_location.return_value = []  # No spools at location
        
        # Setup tracker state
        tracker.active_model = {0: {0: 100}}  # Layer 0, filament 0: 100mm
        tracker.using_ams = True
        tracker.ams_mapping = [0]  # Filament 0 uses tray 0 (AMS1-Slot1)
        
        # Execute
        tracker._spend_filament_for_layer(0)
        
        # Verify: should call get_spools_by_location but NOT consume_spool
        mock_client.get_spools_by_location.assert_called_once_with("Shelf A")
        mock_client.consume_spool.assert_not_called()

    @patch("bambu_spoolman.broker.filament_usage_tracker.new_client")
    @patch("bambu_spoolman.broker.filament_usage_tracker.load_settings")
    def test_consume_multiple_filaments_from_different_locations(
        self, mock_load_settings, mock_new_client
    ):
        """Should consume from correct locations for multi-filament prints."""
        # Setup
        tracker = FilamentUsageTracker()
        
        # Configure mock settings with multiple location mappings
        mock_load_settings.return_value = {
            "location_mapping": {
                "AMS1-Slot1": "Shelf A",
                "AMS1-Slot2": "Shelf B",
            }
        }
        
        # Configure mock spoolman client
        mock_client = Mock()
        mock_new_client.return_value = mock_client
        tracker.spoolman_client = mock_client
        
        # Setup multiple locations with spools
        def get_spools_by_location(location):
            if location == "Shelf A":
                return [{"id": 1, "filament": {"material": "PLA"}}]
            elif location == "Shelf B":
                return [{"id": 2, "filament": {"material": "ABS"}}]
            return []
        
        mock_client.get_spools_by_location.side_effect = get_spools_by_location
        
        # Setup tracker state for 2-filament print
        tracker.active_model = {0: {0: 50, 1: 30}}  # Layer 0: filament 0: 50mm, filament 1: 30mm
        tracker.using_ams = True
        tracker.ams_mapping = [0, 1]  # Filament 0 -> tray 0, filament 1 -> tray 1
        
        # Execute
        tracker._spend_filament_for_layer(0)
        
        # Verify: should consume from correct spools
        assert mock_client.consume_spool.call_count == 2
        calls = mock_client.consume_spool.call_args_list
        
        # Check the calls (order may vary, so check both are present)
        spool_ids = [call[0][0] for call in calls]
        lengths = [call[1]["length"] for call in calls]
        
        assert 1 in spool_ids  # Spool 1 at Shelf A
        assert 2 in spool_ids  # Spool 2 at Shelf B
        assert 50 in lengths   # 50mm for filament 0
        assert 30 in lengths   # 30mm for filament 1
