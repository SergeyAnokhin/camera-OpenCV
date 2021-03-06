import logging, cv2
import numpy as np
from scipy.spatial import distance
from Common.CommonHelper import CommonHelper

class TrackingBox:
    ''' Or "TrackingLine" '''
    point_size = 10

    def __init__(self, yolo_data):
        self.log = logging.getLogger(f"PROC:TRAC:TBox")
        self.helper = CommonHelper()
        self.image = []
        self.object_id = None
        (self.w, self.h) = yolo_data['size']
        self.center = yolo_data['center_coordinate']
        self.yolo_label = yolo_data['label']
        self.id = f"{self.center[0]}x{self.center[1]}"
        (self.x, self.y) = self.center
        (self.point_left_top, self.point_right_bottom) = self.TransformCenterToLimits(self.x, self.y, self.point_size, self.point_size)
        (self.box_left_top, self.box_right_bottom) = self.TransformCenterToLimits(self.x, self.y, self.h, self.w)
        self.pos_text = (self.x, self.y - 5)

    def GetShape(self):
        if len(self.image) == 0:
            return self.PointToStr(0,0)
        return self.PointToStr(len(self.image), len(self.image[0]))

    def GetCenter(self):
        return self.PointToStr(self.x, self.y)

    def ExtractBox(self, image):
        # self.log.debug(f"ExtractBox: Box center_coordinate {self.PointToStr(self.x, self.y)} size {self.PointToStr(self.w, self.h)}")
        # self.log.debug(f"ExtractBox: Box Y {self.box_left_top[1]}:{self.box_right_bottom[1]} " + \
        #                                 f"X {self.box_left_top[0]}:{self.box_right_bottom[0]}")
        # self.log.debug(f"ExtractBox: Image size {(len(image), len(image[0]))}")
        result = image[
                self.box_left_top[1]:self.box_right_bottom[1],
                self.box_left_top[0]:self.box_right_bottom[0]]
        self.image = result
        # self.log.debug(f"ExtractBox: Result size {self.GetShape()}")

    def PointToStr(self, x, y):
        return f'{x}x{y}'

    def TransformCenterToLimits(self, center_x, center_y, size_height, size_width):
        ''' Transform (Center & Size) => (LeftTop & RightBottom) '''
        pos_left_top_x = center_x - size_width // 2
        pos_left_top_y = center_y - size_height // 2
        pos_left_top_x = max(pos_left_top_x, 0) # value or 0
        pos_left_top_y = max(pos_left_top_y, 0) # value or 0
        pos_left_top = (pos_left_top_x, pos_left_top_y)
        pos_right_bottom = (center_x + size_width // 2, center_y + size_height // 2)
        return (pos_left_top, pos_right_bottom)

    def CompareBox(self, boxes_last: []) -> 'TrackingBox':
        if len(boxes_last) == 0:
            return

        coeffs = []
        for box_last in boxes_last:
            compCoeff = self.GetMatchingCoeff(box_last)
            coeffs.append(compCoeff)

        maxValue = max(coeffs)
        maxIndex = coeffs.index(maxValue)
        return boxes_last[maxIndex]

    def GetMatchingCoeff(self, box: 'TrackingBox') -> float:
        box_resized = self.ResizeForBiggerThanTemplate(box.image, self.image)
        # self.log.debug(f'Resize: {box_last.GetShape()} => {box_resized.shape[0:1]}')
        # self.log.debug(f'Template size: {self.GetShape()}')
        # self.log.debug(f' corrsize.height <= img.rows + templ.rows - 1 && corrsize.width <= img.cols + templ.cols ')
        matchTempArr = cv2.matchTemplate(box_resized, self.image, cv2.TM_CCOEFF_NORMED)
        matchTemp = max(map(max, matchTempArr))

        hist1 = cv2.calcHist([box.image],[0],None,[256],[0,256])
        hist2 = cv2.calcHist([self.image],[0],None,[256],[0,256])
        hist = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)

        compCoeff = matchTemp * 0.2 + hist * 0.8
        # report = f'- MATCH: B{box.id} vs B{self.id} = T:{matchTemp:.2f} = H:{hist:.2f} = C:{compCoeff:.2f} {self.helper.Progress(compCoeff)}'
        # self.log.debug(report)
        return compCoeff

    def ResizeForBiggerThanTemplate(self, img, template):
        factors = [x/y for x, y in zip(template.shape[0:2], img.shape[0:2])]
        zoom = max(factors)
        zoom = zoom if zoom > 1 else 1
        imageResized = cv2.resize(img, None, fx=zoom, fy=zoom, interpolation=cv2.INTER_CUBIC)
        return imageResized

    def DrawLine(self, img, box: 'TrackingBox'):
        cv2.line(img,self.center,box.center,(255,0,0),3)

    def DrawStartPoint(self, img):
        color = (128, 50, 50)
        color_bg = (255, 200, 200)
        cv2.rectangle(img, self.point_left_top, self.point_right_bottom, color, 1)
        cv2.putText(img, f'ID{self.object_id}', self.pos_text, cv2.FONT_HERSHEY_SIMPLEX, \
            0.5, color_bg, 2)
        cv2.putText(img, f'ID{self.object_id}', self.pos_text, cv2.FONT_HERSHEY_SIMPLEX, \
            0.5, color, 1)

    def angle(self, box: 'TrackingBox'):
        ''' compute angle (in degrees) for p0p1p2 corner
        Inputs:
            p0,p1,p2 - points in the form of [x,y]
        '''
        p0 = self.center
        p1 = box.center
        p2 = p1 + np.array([1, 0])

        v0 = np.array(p0) - np.array(p1)
        v1 = np.array(p2) - np.array(p1)

        angle = np.math.atan2(np.linalg.det([v0,v1]),np.dot(v0,v1))
        return np.degrees(angle)

    def Distance(self, box: 'TrackingBox'):
        return distance.euclidean(self.center, box.center)

    def __str__(self):
        return f'<BOX id="{self.id}"{f" (obj:{self.object_id} {self.yolo_label})" if self.object_id!=None else ""}>'

    def ToStringShort(self):
        return f'{self.id}{f"=o{self.object_id}" if self.object_id!=None else ""}'