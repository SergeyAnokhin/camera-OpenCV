import cv2, logging, itertools, os, time, cv2
import numpy as np
from Pipeline.Model.CamShot import CamShot
from Pipeline.Model.ProcessingResult import ProcessingResult
from Processors.Yolo.YoloContext import YoloContext
from Processors.Yolo.YoloDetection import YoloDetection


class YoloResultBoxes:
    boxes = []
    indexes = []

    def __init__(self, shot, layerOutputs, minConfidence, threshold):
        detections = [YoloDetection(d, shot) for d in itertools.chain(*layerOutputs)]
        self.boxes = [d for d in detections if d.GetConfidence() > minConfidence]
        boxes = [b.GetBoxCoordinates() for b in self.boxes]
        confidences = [b.GetConfidence() for b in self.boxes]
        self.indexes = cv2.dnn.NMSBoxes(boxes, confidences, minConfidence, threshold)

    def IsEmpty(self):
        return len(self.indexes) == 0

class YoloCamShot: 
    detections = []

    def __init__(self, shot: CamShot, yolo: YoloContext):
        self.shot = shot.Copy()
        self.log = logging.getLogger(f"PROC:YOLO:{self.shot.filename}")
        self.boxes = []
        self.yolo = yolo

    def Detect(self):
        #self.log.debug("start detect objects on: {}".format(self.shot.filename))
        blob = cv2.dnn.blobFromImage(self.shot.image, 1 / 255.0, (416, 416), swapRB=True, crop=False)
        self.yolo.net.setInput(blob)
        start = time.time()
        layerOutputs = self.yolo.net.forward(self.yolo.layers)
        self.log.debug("detection took {:.3f} seconds".format(time.time() - start))
        return layerOutputs

    def ProcessOutput(self, layerOutputs, minConfidence, threshold):
        self.ResultsBoxes = YoloResultBoxes(self.shot, layerOutputs, minConfidence, threshold)

    def Draw(self):
        if self.ResultsBoxes.IsEmpty():
            return

        for i in self.ResultsBoxes.indexes.flatten():
            box = self.ResultsBoxes.boxes[i]
            (x, y, w, h) = box.GetBoxCoordinates()
            color = [int(c) for c in self.yolo.COLORS[box.GetClassId()]]
            text = "{}: {:.1f}".format(self.yolo.LABELS[box.GetClassId()], box.GetConfidence())

            cv2.rectangle(self.shot.image, (x, y), (x + w, y + h), color, 2)
            cv2.putText(self.shot.image, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX,
                0.5, color, 2)

    def GetProcessResult(self):
        # ensure at least one detection exists
        if self.ResultsBoxes.IsEmpty():
            return

        results = []
        for i in self.ResultsBoxes.indexes.flatten():
            result = {}
            box = self.ResultsBoxes.boxes[i]
            (x, y, w, h) = box.GetBoxCoordinates()

            (center_x, center_y) = (x + w//2,y + h//2)
            
            result['area'] = w * h
            result['profile_proportion'] = round(h / w, 2)
            result['center_coordinate'] = [center_x, center_y]
            result['confidence'] = round(box.GetConfidence(), 2)
            result['label'] = self.yolo.labels[box.GetClassId()]
            results.append(result)

        return results
    
class YoloObjDetectionProcessor:
    confidence = 0.4
    threshold = 0.3
    yolo: YoloContext

    def __init__(self):
        self.Result = ProcessingResult()
        self.log = logging.getLogger("PROC:YOLO")
        self.Shots = []
        self.yolo = YoloContext('..\\camera-OpenCV-data\\weights\\yolo-coco')
        self.yolo.PreLoad()
        self.log.debug("Confidence: %s", self.confidence)
        self.log.debug("Threshold: %s", self.threshold)

    def Process(self):
        for shot in self.Shots:
            yolo = YoloCamShot(shot, self.yolo)
            layerOutputs = yolo.Detect()
            yolo.ProcessOutput(layerOutputs, self.confidence, self.threshold)

        return self.Result
