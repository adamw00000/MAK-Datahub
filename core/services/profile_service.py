import logging, json, joblib, os, sys

from django.db import connection

from ..models import ProfileInfo, Device, ProfileCreationRun

class ProfileService:
    def __init__(self, ml_service, storage_service, data_extraction_service, device_service):
        self.logger = logging.getLogger(__name__)
        self.ml_service = ml_service
        self.storage_service = storage_service
        self.data_extraction_service = data_extraction_service
        self.device_service = device_service

        self.MIN_SAMPLES_TO_CREATE_PROFILE = 100
        self.MIN_SAMPLES_TO_UPDATE_PROFILE = 100
    
    def authorize(self, device, profile_type, sensor_data_string):
        sensor_data = json.loads(sensor_data_string)

        df = self.data_extraction_service.create_df_from_json_data(sensor_data)
        aggregated_df = self.data_extraction_service.aggregate_df_with_stats_functions(df)
        profile_info, profile = self.get_latest_profile_for_device(device, profile_type, self.__is_execution_64bit())

        if profile_info is None or profile is None:
            return None
        
        return self.ml_service.predict(profile, aggregated_df, device.id)

    def get_last_profile_creation_run(self):
        return ProfileCreationRun.objects\
            .filter(is_64bit = self.__is_execution_64bit())\
            .order_by('-run_date')\
            .first()

    def get_latest_profile_for_device(self, device, profile_type, is_64bit):
        latest_profile = self.__get_latest_profile_info_for_device(device, profile_type, is_64bit)
        if latest_profile is None:
            return None, None
        profile = joblib.load(latest_profile.profile_file.open('rb'))
        return latest_profile, profile

    def __get_latest_profile_info_for_device(self, device, profile_type, is_64bit):
        return device.profileinfo_set\
            .filter(run__is_64bit = is_64bit)\
            .filter(profile_type = profile_type)\
            .order_by('-run__run_date').first()

    def serialize_profile(self, profile):
        return self.ml_service.serialize(profile)

    def create_profile_creation_run(self, run_date, parsed_event_files, unlock_data, checkpoint_data):
        run = ProfileCreationRun(run_date = run_date, unlock_data = unlock_data, \
            parsed_event_files = parsed_event_files, checkpoint_data = checkpoint_data, \
            is_64bit = self.__is_execution_64bit())
        connection.close()
        run.save()
        return run
    
    def __is_execution_64bit(self):
        return sys.maxsize > 2**32

    def create_profiles(self, run, profile_data, profile_type):
        X, y = profile_data.iloc[:, 0:-1], profile_data.iloc[:, -1]

        classes = y.unique()
        if len(classes) < 2:
            self.logger.info(f'Profile creation: not enough classes ({len(classes)}), aborting')
            return
        
        for device_id in classes:
            connection.close()
            device = self.device_service.get_device(device_id)
            if device is None:
                continue

            sample_count = self.data_extraction_service.get_class_sample_count(y, device_id)
            if sample_count < self.MIN_SAMPLES_TO_CREATE_PROFILE:
                self.logger.info(f'Profile creation: device {device.id} ({device.user.username}@{device.android_id}), not enough data ({sample_count}/{self.MIN_SAMPLES_TO_CREATE_PROFILE} samples) to create profile')
                continue

            # connection.close()
            # current_profile_info = self.__get_latest_profile_info_for_device(self.device_service.get_device(device_id), profile_type, self.__is_execution_64bit())
            # new_sample_count = sample_count
            # if current_profile_info is not None:
            #     new_sample_count -= current_profile_info.used_class_samples

            # if new_sample_count < self.MIN_SAMPLES_TO_UPDATE_PROFILE:
            #     self.logger.info(f'Profile creation: device {device.id} ({device.user.username}@{device.android_id}), skipping updating profile (progress: {new_sample_count}/{self.MIN_SAMPLES_TO_UPDATE_PROFILE} new samples)')
            #     continue

            connection.close()
            user_device_ids = [device.id for device in Device.objects.filter(user = device.user)]

            profile, score, precision, recall, fscore, description = self.ml_service.train(X, y, device, user_device_ids)
            tmp_file = self.storage_service.create_joblib_file(profile, run.run_date, device_id, profile_type)
            
            connection.close()
            profile_file = ProfileInfo(device = device, \
                profile_file = tmp_file, run = run, profile_type = profile_type, \
                score = score, precision = precision, recall = recall, fscore = fscore, \
                used_class_samples = sample_count, description = description)
            profile_file.save()
            
            self.storage_service.dispose(tmp_file)