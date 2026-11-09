
import argparse
from registry import VehicleRegistry

def main():
    p=argparse.ArgumentParser(description="Add or list vehicle registry entries")
    sub=p.add_subparsers(dest="cmd",required=True)
    a=sub.add_parser("add"); a.add_argument("--plate",required=True); a.add_argument("--type",default="")
    a.add_argument("--brand",default=""); a.add_argument("--owner",default="")
    a.add_argument("--color",default=""); a.add_argument("--blacklist",action="store_true")
    a.add_argument("--notes",default="")
    sub.add_parser("list")
    args=p.parse_args(); db=VehicleRegistry("data/vehicles.db")
    if args.cmd=="add":
        db.add_vehicle(args.plate,args.type,args.brand,args.owner,args.color,args.blacklist,args.notes)
        print("Vehicle saved.")
    else:
        for row in db.db.execute("SELECT * FROM vehicles ORDER BY plate"):
            print(dict(row))
    db.close()
if __name__=="__main__": main()
