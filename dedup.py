"""Remove duplicate fbLoad trigger from flyToNode."""
import pathlib

f = pathlib.Path("static/index.html")
h = f.read_text(encoding="utf-8")

trigger = "    if(nd.id==='files'){fbHistory=[];fbDepth=0;setTimeout(()=>fbLoad('~',false),200);}"
count = h.count(trigger)
print(f"trigger count: {count}")
if count > 1:
    # Keep only the first occurrence
    first = h.find(trigger)
    after_first = h[first + len(trigger):]
    after_first = after_first.replace(trigger, "", count - 1)
    h = h[:first + len(trigger)] + after_first
    f.write_text(h, encoding="utf-8")
    print(f"Removed {count-1} duplicate(s). Now: {h.count(trigger)}")
else:
    print("No duplicates found")
