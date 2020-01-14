import logging
from datetime import datetime

from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile

from ..models import DataFileInfo, Device

class DataFileService:
    def __init__(self, storage_service):
        self.logger = logging.getLogger(__name__)
        self.storage_service = storage_service

    def create_data_file(self, file_data, device, start_date, file_type):
        assert (type(file_data) is InMemoryUploadedFile or type(file_data) is TemporaryUploadedFile) and type(device) is Device and (type(start_date) is str or type(start_date) is datetime)
        assert file_type == 'S' or file_type == 'E'

        data_file = DataFileInfo(device = device, start_date = start_date, file_type = file_type)
        sensor_filename = f'{device.id}_{file_data.name}'
        file_uri = self.storage_service.save_form_file(file_data, device.id, sensor_filename)
        data_file.file_uri = file_uri
        data_file.save()
        return data_file

    def get_data_file_list(self):
        return DataFileInfo.objects.order_by('-start_date', 'device_id')

    def get_data_file(self, id):
        assert type(id) is int

        try:
            data_file = DataFileInfo.objects.get(id = id)
            return data_file
        except DataFileInfo.DoesNotExist:
            return None

    def get_event_files_for_device(self, device_id):
        assert type(device_id) is str
        
        try:
            device = Device.objects.get(id = device_id)
            return device.datafile_set.filter(file_type = 'E').order_by('start_date')
        except DataFileInfo.DoesNotExist:
            return None

    def get_sensor_files_for_device(self, device_id):
        assert type(device_id) is str
        
        try:
            device = Device.objects.get(id = device_id)
            return device.datafile_set.filter(file_type = 'S').order_by('start_date')
        except DataFileInfo.DoesNotExist:
            return None