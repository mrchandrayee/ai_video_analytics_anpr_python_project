
from __future__ import annotations
import re
from pathlib import Path
import cv2
import numpy as np
import easyocr
from ultralytics import YOLO

class PlateDetector:
    """License plate bounding-box detector. A plate-trained YOLO model is recommended."""
    def __init__(self, weights=None, conf=0.25):
        self.model=None; self.conf=conf
        if weights and Path(weights).exists():
            self.model=YOLO(weights)
            print(f"Loaded plate detector: {weights}")
        else:
            print("No plate detector weights supplied. Using full-frame OCR fallback.")
    def detect(self, frame):
        h,w=frame.shape[:2]
        if self.model is None:
            # Fallback: OCR the full frame; useful for demos, less reliable than a plate detector.
            return [((0,0,w,h),1.0)]
        result=self.model.predict(frame,conf=self.conf,verbose=False)[0]
        out=[]
        if result.boxes is not None:
            for b in result.boxes:
                x1,y1,x2,y2=map(int,b.xyxy[0].cpu().numpy())
                out.append(((max(0,x1),max(0,y1),min(w,x2),min(h,y2)),float(b.conf[0].cpu())))
        return out

class PlateRecognizer:
    def __init__(self,languages=None,gpu=False,allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-"):
        self.reader=easyocr.Reader(languages or ["en"],gpu=gpu)
        self.allowlist=allowlist
    @staticmethod
    def preprocess(image):
        if image is None or image.size==0: return None
        gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY) if image.ndim==3 else image
        h,w=gray.shape[:2]
        if w<240: gray=cv2.resize(gray,(int(w*2.5),int(h*2.5)),interpolation=cv2.INTER_CUBIC)
        clahe=cv2.createCLAHE(clipLimit=2.0,tileGridSize=(8,8))
        gray=clahe.apply(gray)
        gray=cv2.bilateralFilter(gray,7,45,45)
        return gray
    def read(self,image):
        prep=self.preprocess(image)
        if prep is None: return "",0.0
        results=self.reader.readtext(prep,detail=1,paragraph=False,
                                     allowlist=self.allowlist,
                                     text_threshold=0.45,low_text=0.25)
        if not results: return "",0.0
        # OCR can return plate text in multiple boxes; join in spatial order.
        results=sorted(results,key=lambda r:(min(p[1] for p in r[0]),min(p[0] for p in r[0])))
        text="".join(r[1] for r in results)
        conf=float(np.mean([r[2] for r in results]))
        return text,conf
    @staticmethod
    def normalize(text):
        if not text: return ""
        s=text.upper().replace(" ","")
        s=re.sub(r"[^A-Z0-9.-]","",s)
        # Common OCR confusions only in mixed alphanumeric strings.
        # Keep raw digits/letters mostly intact to avoid inventing characters.
        s=s.replace("—","-").replace("_","-")
        return s.strip(".-")


def extract_digits(text):
    return re.sub(r"\D","",text or "")

def blacklist_match(ocr_text, targets):
    """Exact match or suffix-digit match to tolerate partially read plate strings."""
    if not ocr_text or not targets: return None
    ocr=extract_digits(ocr_text)
    if not ocr: return None
    suffix=ocr[-5:] if len(ocr)>=5 else ocr
    for target in targets:
        target_digits=extract_digits(target)
        if not target_digits: continue
        target_suffix=target_digits[-5:] if len(target_digits)>=5 else target_digits
        if ocr==target_digits or suffix==target_suffix:
            return target
    return None
