import logging
from Archiver.CameraArchiveConfig import CameraArchiveConfig
from Archiver.CameraArchiveHelper import CameraArchiveHelper
from Pipeline.Model.PipelineShot import PipelineShot
from Pipeline.Pipeline import Pipeline
from Processors.PipelineShotProcessor import PipelineShotProcessor

class ShotsPipeline(Pipeline):

    def __init__(self, camera: str, isSimulation=False):
        super().__init__(isSimulation)
        self.archiver = CameraArchiveHelper()
        self.config = self.archiver.load_configs("configs", [ camera ])[0]

    def PreLoadProtected(self, processor: PipelineShotProcessor):
        processor.config = self.config

    def GetShots(self):
        shots = []
        for provider in self.providers:
            provider.config = self.config
            shots = provider.GetShots(shots)
        return shots

    def Process(self, pShots: []):
        pipelineContext = { 'items': pShots }
        for processor in self.processors:
            processor.Process(pipelineContext)
            PostProcess = getattr(processor, "PostProcess", None)
            if callable(PostProcess):
                processor.PostProcess(pShots)

        return pShots

    def Show(self):
        pass
