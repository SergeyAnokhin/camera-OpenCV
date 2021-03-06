import re, datetime, cv2, os
from copy import copy, deepcopy
from Common.CommonHelper import CommonHelper
from Pipeline.Model.FileImage import FileImage

class CamShot(FileImage):
    
    def __init__(self, *args, **kwargs):
        self.helper = CommonHelper()
        return super().__init__(*args, **kwargs)

    def GetDatetime(self, is_raise_exception = True):
        return self.helper.get_datetime(self.filename, is_raise_exception)

    def GetId(self, camera: str):
        timestamp = self.helper.ToTimeStampStr(self.GetDatetime())
        return f'{camera}@{timestamp}'

    def GetIdUtc(self, camera: str):
        dt = self.GetDatetime()
        dt = self.helper.ToUtcTime(dt)
        return f'{camera}@{dt:%Y%m%d_%H%M%S}'

    def GrayImage(self):
        return cv2.cvtColor(self.GetImage(), cv2.COLOR_BGR2GRAY)

    def Clone(self):
        copy = CamShot(self.fullname)
        if len(self.image):
            copy.image = deepcopy(self.image)
        return copy

