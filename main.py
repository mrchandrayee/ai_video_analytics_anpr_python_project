
import argparse, json, time
from pathlib import Path
import cv2
from anpr import PlateRecognizer, PlateDetector
from registry import VehicleRegistry
from visualizer import draw_result

def source_value(s): return int(s) if s.isdigit() else s

def main():
    ap=argparse.ArgumentParser(description="AI Video Analytics - Vehicle/License Plate OCR")
    ap.add_argument("--source",default="0",help="Camera index or video file")
    ap.add_argument("--plate-weights",default=None,help="YOLO license-plate detector weights")
    ap.add_argument("--ocr-gpu",action="store_true")
    ap.add_argument("--no-display",action="store_true")
    ap.add_argument("--output",default="output/anpr_annotated.mp4")
    args=ap.parse_args()
    cfg=json.load(open("config/settings.json",encoding="utf-8"))
    if args.plate_weights: cfg["plate_weights"]=args.plate_weights
    detector=PlateDetector(cfg.get("plate_weights"),float(cfg["plate_confidence"]))
    recognizer=PlateRecognizer(cfg["ocr_languages"],args.ocr_gpu,cfg["ocr_allowlist"])
    registry=VehicleRegistry(cfg["database"])
    cap=cv2.VideoCapture(source_value(args.source))
    if not cap.isOpened(): raise SystemExit(f"Cannot open source: {args.source}")
    fps=cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps<1 or fps>120: fps=25.0
    w=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
    h=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True)
    writer=cv2.VideoWriter(str(out),cv2.VideoWriter_fourcc(*"mp4v"),fps,(w,h))
    frame_no=0; t0=time.time(); seen={}
    try:
        while True:
            ok,frame=cap.read()
            if not ok: break
            frame_no+=1
            boxes=detector.detect(frame)
            results=[]
            for box,det_conf in boxes:
                x1,y1,x2,y2=box
                crop=frame[max(0,y1):min(h,y2),max(0,x1):min(w,x2)]
                text,ocr_conf=recognizer.read(crop)
                plate=recognizer.normalize(text)
                if plate and len(plate)>=5:
                    now=time.time()
                    # De-duplicate the same plate within the configured cooldown.
                    cooldown=float(cfg["alert_cooldown_seconds"])
                    if now-seen.get(plate,0)>=cooldown:
                        seen[plate]=now
                        match=registry.match_blacklist(plate)
                        registry.log_detection(plate,ocr_conf,det_conf,args.source,frame_no,match)
                    else:
                        match=registry.match_blacklist(plate)
                    results.append({"box":box,"plate":plate,"ocr_conf":ocr_conf,
                                    "det_conf":det_conf,"blacklisted":bool(match),"match":match})
            annotated=draw_result(frame,results,frame_no)
            writer.write(annotated)
            if not args.no_display:
                cv2.imshow("AI Video Analytics | ANPR",annotated)
                if cv2.waitKey(1)&0xff in (ord("q"),27): break
            if frame_no%100==0: print(f"Processed {frame_no} frames")
    finally:
        cap.release(); writer.release(); cv2.destroyAllWindows(); registry.close()
    print(f"Saved annotated video: {out.resolve()}")
    print(f"Detection database: {cfg['database']}")

if __name__=="__main__": main()
