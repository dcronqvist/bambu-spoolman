"use client";

import { useState, useTransition } from "react";
import { updateLocationMapping } from "./actions";
import { Alert } from "../ui/alert";
import { AlertCircle } from "lucide-react";
import { useRouter } from "next/navigation";

type Filament = {
  color_hex?: string;
  material?: string;
  vendor?: {
    name?: string;
  };
  name?: string;
};

type Spool = {
  id?: number;
  filament?: Filament;
};

type LocationWithSpools = {
  location: string;
  spools: Spool[];
};

type Props = {
  physicalLocation: string;
  currentMapping: string | null;
  locationsWithSpools: LocationWithSpools[];
};

function getSpoolDisplay(spool: Spool): string {
  const parts = [];
  if (spool.id) parts.push(`#${spool.id}`);
  if (spool.filament?.vendor?.name) parts.push(spool.filament.vendor.name);
  if (spool.filament?.material) parts.push(spool.filament.material);
  if (spool.filament?.name) parts.push(spool.filament.name);

  return parts.length > 0 ? parts.join(" ") : `Spool #${spool.id}`;
}

function getColorFromHex(hex?: string): string {
  return hex || "#e5e7eb"; // default gray if no color
}

export function TrayConfigForm(props: Props) {
  const [selectedLocation, setSelectedLocation] = useState(
    props.currentMapping,
  );
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const router = useRouter();

  const handleSelectLocation = (location: string) => {
    setSelectedLocation(location);
    setError(null);

    startTransition(async () => {
      const result = await updateLocationMapping(
        props.physicalLocation,
        location,
      );
      if (result.error) {
        setError(result.error);
      } else {
        router.refresh();
      }
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">{props.physicalLocation}</h2>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle />
          {error}
        </Alert>
      )}

      <div>
        <h3 className="text-sm font-medium text-gray-600 mb-4">
          Map to Spoolman location
        </h3>

        <div className="space-y-3">
          {props.locationsWithSpools.length === 0 ? (
            <p className="text-gray-500">No locations available in Spoolman</p>
          ) : (
            props.locationsWithSpools.map((locationData) => {
              const location = locationData.location;
              const spools = locationData.spools;
              const isSelected = selectedLocation === location;

              return (
                <button
                  key={location}
                  onClick={() => handleSelectLocation(location)}
                  disabled={isPending}
                  className={`w-full p-4 text-left border-2 rounded-lg transition-all ${
                    isSelected
                      ? "border-blue-500 bg-blue-50"
                      : "border-gray-200 bg-white hover:border-gray-300"
                  } ${isPending ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
                >
                  <div className="flex justify-between items-start gap-4">
                    <div className="flex-1">
                      <h4 className="font-semibold text-base mb-3">
                        {location}
                      </h4>

                      {spools.length === 0 ? (
                        <p className="text-sm text-gray-500 italic">
                          No spools in this location
                        </p>
                      ) : (
                        <div className="flex flex-wrap gap-2">
                          {spools.map((spool, idx) => (
                            <div
                              key={spool.id}
                              className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
                                idx === 0
                                  ? "bg-blue-500 text-white border-2 border-blue-600"
                                  : "bg-gray-100 text-gray-800 border border-gray-300"
                              }`}
                              style={
                                idx === 0
                                  ? {}
                                  : {
                                      backgroundColor: getColorFromHex(
                                        spool.filament?.color_hex,
                                      ),
                                    }
                              }
                            >
                              {getSpoolDisplay(spool)}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Radio button indicator */}
                    <div
                      className={`w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 mt-1 ${
                        isSelected
                          ? "border-blue-500 bg-blue-500"
                          : "border-gray-300"
                      }`}
                    >
                      {isSelected && (
                        <div className="w-2 h-2 rounded-full bg-white"></div>
                      )}
                    </div>
                  </div>
                </button>
              );
            })
          )}
        </div>
      </div>

      {isPending && (
        <p className="text-sm text-gray-500 text-center">Updating...</p>
      )}
    </div>
  );
}
