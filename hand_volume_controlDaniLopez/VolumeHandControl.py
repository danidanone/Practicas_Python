from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import numpy as np

class VolumeController:
    def __init__(self):
        devices = AudioUtilities.GetSpeakers()
        self.volume = devices.EndpointVolume
        
        # Get volume range
        vol_range = self.volume.GetVolumeRange()
        self.min_vol = vol_range[0]
        self.max_vol = vol_range[1]
        
    def get_current_volume(self):
        # Returns volume in percentage (scalar between 0.0 and 1.0)
        return self.volume.GetMasterVolumeLevelScalar() * 100
        
    def set_volume_from_distance(self, distance, min_dist=50, max_dist=300):
        # Mapeo de distancia al rango de volumen (decibelios)
        vol_db = np.interp(distance, [min_dist, max_dist], [self.min_vol, self.max_vol])
        
        # Mapeo para visualizaciones (porcentajes)
        vol_bar = np.interp(distance, [min_dist, max_dist], [400, 150])
        vol_per = np.interp(distance, [min_dist, max_dist], [0, 100])
        
        # Actualiza el volumen del sistema
        self.volume.SetMasterVolumeLevel(vol_db, None)
        
        return vol_bar, vol_per

    def set_volume_db(self, vol_db):
        self.volume.SetMasterVolumeLevel(vol_db, None)
