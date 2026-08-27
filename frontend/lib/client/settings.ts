export function getTrayIndex(ams: number | undefined, tray: number) {
  if (ams === undefined) {
    return tray;
  }
  return ams * 4 + tray;
}

/**
 * Convert a tray index to a physical location name.
 * Format: "AMS{ams_index+1}-Slot{slot_index+1}"
 * For external spool (tray_id 255), returns "External"
 */
export function trayIndexToLocationName(trayIndex: number): string {
  const EXTERNAL_SPOOL_ID = 255;
  if (trayIndex === EXTERNAL_SPOOL_ID) {
    return "External";
  }
  const amsIndex = Math.floor(trayIndex / 4);
  const slotIndex = trayIndex % 4;
  return `AMS${amsIndex + 1}-Slot${slotIndex + 1}`;
}
