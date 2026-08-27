import grpc
from google.protobuf.empty_pb2 import Empty
from google.protobuf.json_format import ParseDict
from grpc.aio import ServicerContext
from loguru import logger

import bambu_spoolman.grpc.bambu_spoolman_pb2 as pb2
import bambu_spoolman.grpc.spoolman_pb2 as spoolman_pb2
from bambu_spoolman.bambu_mqtt import stateful_printer_info
from bambu_spoolman.broker.automatic_spool_switch import AutomaticSpoolSwitch
from bambu_spoolman.grpc import bambu_spoolman_pb2_grpc
from bambu_spoolman.settings import load_settings, save_settings
from bambu_spoolman.spoolman import instance as spoolman_instance


class BambuSpoolmanServicer(bambu_spoolman_pb2_grpc.BambuSpoolmanServicer):
    def __init__(self):
        pass

    async def GetTrayCount(self, request: Empty, context: ServicerContext):
        if stateful_printer_info.connected:
            if ams := stateful_printer_info.get_info().get("print", {}).get("ams"):
                tray_count = len(ams.get("ams", [])) * 4
            else:
                tray_count = 0
        else:
            tray_count = 0
        return pb2.TrayCountResponse(count=tray_count)

    async def GetPrinterStatus(self, request: Empty, context: ServicerContext):
        return pb2.PrinterStatusResponse(
            last_updated=stateful_printer_info.last_update,
            connected=stateful_printer_info.connected,
            status=stateful_printer_info.get_info(),
        )

    async def Info(self, request: Empty, context: ServicerContext):
        features = pb2.Features(
            tray_locking=spoolman_instance().supports_tray_locking()
        )
        return pb2.InfoResponse(
            spoolman_url=spoolman_instance().endpoint,
            spoolman_valid=spoolman_instance().validate(),
            features=features,
        )

    async def GetSpools(self, request: pb2.GetSpoolsRequest, context: ServicerContext):
        if len(request.spool_id) == 0:
            # Retrieve all spools
            spools = spoolman_instance().get_spools()
        else:
            # Retrieve specific spools by ID
            spools = [
                spoolman_instance().get_spool(spool_id) for spool_id in request.spool_id
            ]
        return pb2.GetSpoolsResponse(
            spools=[
                ParseDict(spool, spoolman_pb2.Spool(), ignore_unknown_fields=True)
                for spool in spools
            ]
        )

    async def GetSettings(self, request: Empty, context: ServicerContext):
        settings = load_settings()
        spoolman_locations = spoolman_instance().get_locations()
        return pb2.SettingsResponse(
            trays=settings.get("trays", {}),
            tray_count=settings.get("tray_count", 0),
            locked_trays=settings.get("locked_trays", []),
            location_mapping=settings.get("location_mapping", {}),
            available_locations=spoolman_locations,
        )

    async def UpdateTray(
        self, request: pb2.UpdateTrayRequest, context: ServicerContext
    ):
        settings = load_settings()

        # Handle location-based mapping
        if request.physical_location and request.spoolman_location:
            location_mapping = settings.get("location_mapping", {})
            
            # Validate that the Spoolman location exists
            available_locations = spoolman_instance().get_locations()
            if request.spoolman_location not in available_locations:
                await context.abort(
                    grpc.StatusCode.INVALID_ARGUMENT,
                    f"Spoolman location '{request.spoolman_location}' does not exist",
                )
            
            # Update the mapping
            location_mapping[request.physical_location] = request.spoolman_location
            settings["location_mapping"] = location_mapping
            save_settings(settings)
            logger.info(
                f"Updated location mapping: {request.physical_location} -> {request.spoolman_location}"
            )
            return Empty()

        # If neither location-based nor legacy fields are provided, abort
        await context.abort(
            grpc.StatusCode.INVALID_ARGUMENT,
            "Must provide physical_location and spoolman_location"
        )
        return Empty()

    async def GetSpoolByUUID(
        self, request: pb2.GetSpoolbyUUIDRequest, context: ServicerContext
    ):
        spool = spoolman_instance().lookup_by_tray_uuid(request.uuid)
        if spool is None:
            await context.abort(grpc.StatusCode.NOT_FOUND, "Spool not found")
        return ParseDict(spool, spoolman_pb2.Spool(), ignore_unknown_fields=True)

    async def SetTrayUUID(
        self, request: pb2.SetSpoolUUIDRequest, context: ServicerContext
    ):
        tray_uuid = request.uuid
        spool_id = request.spool_id

        spool = spoolman_instance().get_spool(spool_id)

        logger.debug(f"spool: {spool}")

        if spool is None:
            await context.abort(grpc.StatusCode.NOT_FOUND, "Spool not found")

        if not spoolman_instance().supports_tray_locking():
            await context.abort(
                grpc.StatusCode.UNIMPLEMENTED,
                "Spoolman instance does not support tray locking",
            )

        success = spoolman_instance().set_tray_uuid(spool_id, tray_uuid)

        AutomaticSpoolSwitch.get_instance().sync()

        if not success:
            await context.abort(
                grpc.StatusCode.INTERNAL, "Failed to set tray UUID for spool"
            )
        return Empty()

    async def GetLocationsWithSpools(
        self, request: Empty, context: ServicerContext
    ):
        """Get all Spoolman locations with their spools"""
        locations = spoolman_instance().get_locations()
        result = []
        
        for location in locations:
            spools = spoolman_instance().get_spools_by_location(location)
            location_with_spools = pb2.LocationWithSpools(
                location=location,
                spools=[
                    ParseDict(spool, spoolman_pb2.Spool(), ignore_unknown_fields=True)
                    for spool in spools
                ],
            )
            result.append(location_with_spools)
        
        return pb2.GetLocationsWithSpoolsResponse(locations=result)


async def serve(host: str = "0.0.0.0", port: int = 50051):
    server = grpc.aio.server()
    bambu_spoolman_pb2_grpc.add_BambuSpoolmanServicer_to_server(
        BambuSpoolmanServicer(), server
    )
    server.add_insecure_port(f"{host}:{port}")
    await server.start()
    logger.info(f"gRPC server started on {host}:{port}")

    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down gRPC server...")
        await server.stop(grace=5)
