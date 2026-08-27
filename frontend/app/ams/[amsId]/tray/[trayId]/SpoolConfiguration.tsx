import { TrayConfigForm } from "@/components/tray-config/TrayConfigForm";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { getSettings, getLocationForTray, isLocked } from "@/lib/settings";
import { trayIndexToLocationName } from "@/lib/client/settings";
import { grpcClient } from "@/lib/grpc";
import { AlertCircle } from "lucide-react";

type Props = {
  trayId: number;
};

export async function SpoolConfiguration(props: Props) {
  const settings = await getSettings();
  const currentMapping = await getLocationForTray(props.trayId);
  const physicalLocation = trayIndexToLocationName(props.trayId);

  // Fetch locations with their spools from gRPC
  const locationsWithSpoolsResponse = await grpcClient.getLocationsWithSpools(
    {},
  );
  const locationsWithSpools = locationsWithSpoolsResponse.locations || [];

  if (await isLocked(props.trayId)) {
    return (
      <Alert>
        <AlertCircle />
        <AlertDescription>
          The spool in this tray is automatically selected and cannot be
          changed.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <TrayConfigForm
      key={physicalLocation}
      physicalLocation={physicalLocation}
      currentMapping={currentMapping}
      locationsWithSpools={locationsWithSpools}
    />
  );
}
