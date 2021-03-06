import dependency_injector.containers as containers
import dependency_injector.providers as providers

from ProfileCreator.parsers.event_parser import EventParser
from ProfileCreator.parsers.sensors_parser import SensorParser

import os
app_home = os.path.dirname(__file__)

class Parsers(containers.DeclarativeContainer):
    """IoC container of parser providers."""
    event_parser = providers.Factory(EventParser)
    sensor_parser = providers.Factory(SensorParser, config_json_path = os.path.join(app_home, 'ProfileCreator', 'parsers', 'sensor_config.json'))

from core.services.data_extraction_service import DataExtractionService
from core.services.data_file_service import DataFileService
from core.services.device_service import DeviceService
from core.services.storage_service import StorageService
from core.services.ml_service import RFE20step005_RF100_SMOTETomek_MLService
from core.services.profile_service import ProfileService

class Services(containers.DeclarativeContainer):
    """IoC container of service providers."""
    device_service = providers.Factory(DeviceService)
    ml_service = providers.Factory(RFE20step005_RF100_SMOTETomek_MLService)
    storage_service = providers.Factory(StorageService)
    data_file_service = providers.Factory(DataFileService)

    data_extraction_service = providers.Factory(DataExtractionService, event_parser = Parsers.event_parser, sensor_parser = Parsers.sensor_parser)
    profile_service = providers.Factory(ProfileService, ml_service = ml_service, storage_service = storage_service, \
        data_extraction_service = data_extraction_service, device_service = device_service)