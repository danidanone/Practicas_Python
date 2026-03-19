from datetime import datetime
import uuid

class Session:
    def __init__(self, session_id=None, start_time=None, end_time=None):
        self.session_id = session_id or str(uuid.uuid4())
        self.start_time = start_time or datetime.utcnow()
        self.end_time = end_time

    def end_session(self):
        self.end_time = datetime.utcnow()

    def get_duration(self):
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.utcnow() - self.start_time).total_seconds()

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.get_duration()
        }
