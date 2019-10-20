import os
from Providers.Provider import Provider
from Common.CommonHelper import CommonHelper
from datetime import datetime
from elasticsearch import Elasticsearch
from Pipeline.Model.CamShot import CamShot
from Pipeline.Model.PipelineShot import PipelineShot

class ElasticSearchProvider(Provider):

    def __init__(self, camera: str, datetime: datetime, isSimulation = False):
        super().__init__("ELSE")
        self.camera = camera
        self.datetime = datetime
        self.helper = CommonHelper()

    def GetShotsProtected(self, pShots: []):
        es = Elasticsearch([{'host': '192.168.1.31', 'port': 9200}])
        dtUtc = self.helper.ToUtcTime(self.datetime)
        index = self.helper.GetEsCameraArchiveIndex(dtUtc)
        id = self.helper.GetEsShotId(self.camera, dtUtc)

        #res = es.get(index="cameraarchive-2019.10", doc_type='doc', id='Foscam@2019-10-20T15:18:08.000Z')
        res = es.get(index=index, doc_type='doc', id=id)
        path_cv = print(res['_source']['path_cv']) # /CameraArchive/Foscam/2019-10/20/20191020_171808_Foscam_cv.jpeg
        path_cv = os.path.join("\\\\diskstation", path_cv)
        shot = CamShot(path_cv)
        return [PipelineShot(shot)]