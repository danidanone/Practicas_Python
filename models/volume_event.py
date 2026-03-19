from datetime import datetime

class VolumeEvent:
    def __init__(self, session_id, old_volume, new_volume, finger_distance, timestamp=None):
        self.session_id = session_id
        self.old_volume = old_volume
        self.new_volume = new_volume
        self.finger_distance = finger_distance
        self.timestamp = timestamp or datetime.utcnow()

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "old_volume": self.old_volume,
            "new_volume": self.new_volume,
            "finger_distance": self.finger_distance
        }
