
import cv2
GREEN=(40,220,90); RED=(30,40,245); WHITE=(245,245,245); DARK=(18,20,28); CYAN=(255,220,0)
def draw_result(frame,results,frame_no):
    img=frame.copy(); h,w=img.shape[:2]
    for r in results:
        x1,y1,x2,y2=r["box"]
        color=RED if r["blacklisted"] else GREEN
        cv2.rectangle(img,(x1,y1),(x2,y2),color,2,cv2.LINE_AA)
        label=f'{r["plate"]}  OCR {r["ocr_conf"]:.2f}'
        if r["blacklisted"]: label="BLACKLIST: "+label
        fs=max(.42,min(w,h)/950)
        (tw,th),_=cv2.getTextSize(label,cv2.FONT_HERSHEY_SIMPLEX,fs,1)
        top=max(0,y1-th-9)
        cv2.rectangle(img,(x1,top),(min(w-1,x1+tw+8),top+th+7),color,-1)
        cv2.putText(img,label,(x1+4,top+th+2),cv2.FONT_HERSHEY_SIMPLEX,fs,DARK,1,cv2.LINE_AA)
    ph=max(42,int(h*.08)); ov=img.copy()
    cv2.rectangle(ov,(0,0),(w,ph),DARK,-1); cv2.addWeighted(ov,.82,img,.18,0,img)
    cv2.putText(img,"AI VIDEO ANALYTICS | VEHICLE / PLATE OCR",(10,26),
                cv2.FONT_HERSHEY_SIMPLEX,max(.4,min(w,h)/900),CYAN,1,cv2.LINE_AA)
    cv2.putText(img,f"FRAME {frame_no}   PLATES READ: {len(results)}   BLACKLIST: {sum(r['blacklisted'] for r in results)}",
                (10,ph+22),cv2.FONT_HERSHEY_SIMPLEX,max(.38,min(w,h)/1000),WHITE,1,cv2.LINE_AA)
    return img
