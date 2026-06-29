import argparse, os, time
import cv2
from ultralytics import YOLO
from utils.io_utils import write_csv

DEFAULT_CLASSES = ["person","bicycle","car","motorcycle","bus","truck"]

def parse_args():
    ap = argparse.ArgumentParser(description="Tracking YOLOv8 + ByteTrack -> CSV")
    ap.add_argument("--video", required=True)
    ap.add_argument("--out", default="outputs/tracks.csv")
    ap.add_argument("--model", default="yolov8n.pt")
    ap.add_argument("--imgsz", type=int, default=960)
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--classes", nargs="*", default=DEFAULT_CLASSES, help="nomi classi da tenere")
    return ap.parse_args()

def main():
    args = parse_args()
    model = YOLO(args.model)
    # Usa tracker ByteTrack interno di Ultralytics
    results = model.track(source=args.video, imgsz=args.imgsz, conf=args.conf, stream=True, persist=True, tracker="bytetrack.yaml")
    class_names = model.model.names if hasattr(model.model, 'names') else {}

    rows = []
    frame_idx = -1
    t0 = time.time()
    for r in results:
        frame_idx += 1
        if r.boxes is None or r.boxes.id is None:
            continue
        boxes = r.boxes
        ids = boxes.id.int().tolist()
        xyxy = boxes.xyxy.cpu().tolist()
        confs = boxes.conf.cpu().tolist() if boxes.conf is not None else [1.0]*len(ids)
        clss = boxes.cls.int().tolist() if boxes.cls is not None else [0]*len(ids)

        for i, (tid, bb, cf, c) in enumerate(zip(ids, xyxy, confs, clss)):
            cname = class_names.get(int(c), str(int(c)))
            if args.classes and cname not in args.classes:
                continue
            x1,y1,x2,y2 = bb
            rows.append([frame_idx, tid, cname, cf, int(x1), int(y1), int(x2), int(y2)])

    write_csv(rows, header=["frame","track_id","class","conf","x1","y1","x2","y2"], path=args.out)
    dt = time.time()-t0
    print(f"[OK] Salvato {len(rows)} detection/track in {args.out} (elapsed {dt:.1f}s)")

if __name__ == "__main__":
    main()
