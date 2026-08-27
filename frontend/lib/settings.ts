import { cacheLife, cacheTag, revalidateTag } from "next/cache";
import { grpcClient } from "./grpc";
import { getSpool } from "./spool";
import { trayIndexToLocationName } from "./client/settings";

export async function revalidateSettings() {
  "use server";
  revalidateTag("settings", "max");
}

export async function getSettings() {
  "use cache";
  cacheLife("seconds");
  cacheTag("settings");

  const response = await grpcClient.getSettings({});
  return response;
}

/**
 * Gets the spool locked to a tray (for RFID tray locking feature)
 * @param tray The tray to get
 * @returns The Spool in a tray, if any
 */
export async function getSpoolInTray(tray: number) {
  const settings = await getSettings();

  const spoolId = settings.trays[tray];
  if (!spoolId) {
    return null;
  }
  return getSpool(spoolId.toString());
}

/**
 * Gets the Spoolman location mapped to a physical tray position.
 * @param tray The tray index
 * @returns The Spoolman location name, if any
 */
export async function getLocationForTray(tray: number) {
  const settings = await getSettings();
  const physicalLocation = trayIndexToLocationName(tray);
  return settings.locationMapping?.[physicalLocation] ?? null;
}

export async function isLocked(tray: number) {
  const settings = await getSettings();
  return settings.lockedTrays.includes(tray);
}
