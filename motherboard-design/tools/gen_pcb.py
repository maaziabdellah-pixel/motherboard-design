# -*- coding: utf-8 -*-
"""
Generator for motherboard-design.kicad_pcb  (Smart Earbuds Charging PCB)

2-layer board.
  GND   : copper pours F.Cu + B.Cu joined by stitching vias.
  others: routed by a 3D maze router (Dijkstra over F/B with via jumps and
          turn penalties). Power nets use wide tracks.
Clearance budgets fold in the widest track half-width + grid quantisation so
the produced geometry passes a 0.2 mm DRC clearance rule.
"""
import os, math, heapq, pcbnew
from pcbnew import VECTOR2I, FromMM, ToMM

FPROOT = r"C:\Program Files\KiCad\10.0\share\kicad\footprints"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "motherboard-design.kicad_pcb")

DO_ZONES = True
DO_SILK  = True

BW, BH    = 56.0, 30.0
RES       = 0.1                    # maze grid resolution (mm)
CLR       = 0.2                    # copper clearance rule
WMAX_HALF = 0.25                   # widest track half-width (0.5 mm power net)
QUANT     = 0.06                   # grid quantisation slack
POWER     = {"+5V", "+BATT", "BATT-"}
def wid(n): return 0.5 if n in POWER else 0.3

board = pcbnew.CreateEmptyBoard()

# ---------- nets ----------
NETW = {}
def net(name):
    if name not in NETW:
        ni = pcbnew.NETINFO_ITEM(board, name); board.Add(ni); NETW[name] = ni
    return NETW[name]
NETLIST = ["+5V","GND","+BATT","BATT-","CHRG","STDBY","D_RED","D_GRN","PROG",
           "CC1","CC2","DW_VCC","DW_CS","OD","OC","FDRAIN"]
for n in NETLIST: net(n)
NID = {n:i+1 for i,n in enumerate(NETLIST)}
BLOCK = -2

# ---------- placement ----------
PLACE = {
 "J1": ("Connector_USB","USB_C_Receptacle_HRO_TYPE-C-31-M-12","USB-C", 6.0, 15, 270),
 "C1": ("Capacitor_SMD","C_0805_2012Metric","10uF", 16, 7, 0),
 "R6": ("Resistor_SMD","R_0805_2012Metric","5.1k", 14, 23, 0),
 "R7": ("Resistor_SMD","R_0805_2012Metric","5.1k", 18, 25, 0),
 "U1": ("Package_SO","SOIC-8_3.9x4.9mm_P1.27mm","TP4056", 26, 15, 0),
 "R1": ("Resistor_SMD","R_0805_2012Metric","2k", 26, 25, 0),
 "R2": ("Resistor_SMD","R_0805_2012Metric","1k", 20, 6, 0),
 "D1": ("LED_SMD","LED_0805_2012Metric","Red", 25, 6, 0),
 "R3": ("Resistor_SMD","R_0805_2012Metric","1k", 31, 6, 0),
 "D2": ("LED_SMD","LED_0805_2012Metric","Green", 36, 6, 0),
 "C2": ("Capacitor_SMD","C_0805_2012Metric","10uF", 34, 15, 0),
 "R4": ("Resistor_SMD","R_0805_2012Metric","100R", 33, 24, 0),
 "Q1": ("Package_TO_SOT_SMD","SOT-23-6","FS8205A", 40, 10, 0),
 "U2": ("Package_TO_SOT_SMD","SOT-23-6","DW01A", 40, 20, 0),
 "R5": ("Resistor_SMD","R_0805_2012Metric","2k", 40, 26, 0),
 "C3": ("Capacitor_SMD","C_0805_2012Metric","100nF", 44, 25, 0),
 "J2": ("Connector_JST","JST_PH_B2B-PH-SM4-TB_1x02-1MP_P2.00mm_Vertical","BATTERY", 51, 8, 0),
 "J3": ("Connector_JST","JST_PH_B2B-PH-SM4-TB_1x02-1MP_P2.00mm_Vertical","OUTPUT", 51, 22, 0),
}
PADNET = {
 "J1": {"A4":"+5V","A9":"+5V","B4":"+5V","B9":"+5V",
        "A1":"GND","A12":"GND","B1":"GND","B12":"GND","SH":"GND","A5":"CC1","B5":"CC2"},
 "C1": {"1":"+5V","2":"GND"},
 "R6": {"1":"CC1","2":"GND"}, "R7": {"1":"CC2","2":"GND"},
 "U1": {"1":"GND","2":"PROG","3":"GND","4":"+5V","5":"+BATT","6":"STDBY","7":"CHRG","8":"+5V"},
 "R1": {"1":"PROG","2":"GND"},
 "R2": {"1":"+5V","2":"D_RED"}, "D1": {"1":"CHRG","2":"D_RED"},
 "R3": {"1":"+5V","2":"D_GRN"}, "D2": {"1":"STDBY","2":"D_GRN"},
 "C2": {"1":"+BATT","2":"GND"},
 "R4": {"1":"+BATT","2":"DW_VCC"},
 "Q1": {"1":"BATT-","2":"OD","3":"GND","4":"OC","5":"FDRAIN","6":"FDRAIN"},
 "U2": {"1":"OD","2":"DW_CS","3":"OC","5":"DW_VCC","6":"BATT-"},
 "R5": {"1":"DW_CS","2":"GND"}, "C3": {"1":"DW_VCC","2":"BATT-"},
 "J2": {"1":"+BATT","2":"BATT-"}, "J3": {"1":"+BATT","2":"GND"},
}

FOOT = {}
def place(ref):
    lib, fpn, val, x, y, rot = PLACE[ref]
    fp = pcbnew.FootprintLoad(FPROOT + "\\" + lib + ".pretty", fpn)
    if not fp: raise SystemExit("FP load failed " + fpn)
    fp.SetReference(ref); fp.SetValue(val); board.Add(fp)
    fp.SetPosition(VECTOR2I(FromMM(x), FromMM(y))); fp.SetOrientationDegrees(rot)
    for pad in fp.Pads():
        nm = pad.GetNumber()
        if nm in PADNET.get(ref, {}): pad.SetNet(net(PADNET[ref][nm]))
    FOOT[ref] = fp
for ref in PLACE: place(ref)

# ---------- board outline ----------
def edge(x1,y1,x2,y2):
    s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(VECTOR2I(FromMM(x1),FromMM(y1))); s.SetEnd(VECTOR2I(FromMM(x2),FromMM(y2)))
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(FromMM(0.15)); board.Add(s)
edge(0,0,BW,0); edge(BW,0,BW,BH); edge(BW,BH,0,BH); edge(0,BH,0,0)

# ---------- grids ----------
NX = int(round(BW/RES)); NY = int(round(BH/RES))
def G(): return [[0]*(NY+1) for _ in range(NX+1)]
padF = G(); hard = G(); vno = G(); trk = {pcbnew.F_Cu: G(), pcbnew.B_Cu: G()}
def cell(v): return int(round(v/RES))
def mm(i): return i*RES
for i in range(NX+1):
    for j in range(NY+1):
        x,y = mm(i),mm(j)
        if x < 0.6 or x > BW-0.6 or y < 0.6 or y > BH-0.6: hard[i][j] = 1
def rect_dist(px,py, x1,y1,x2,y2):
    dx = max(x1-px, 0, px-x2); dy = max(y1-py, 0, py-y2); return math.hypot(dx,dy)

PADCENTERS = []
for ref, fp in FOOT.items():
    for pad in fp.Pads():
        p = pad.GetPosition(); bb = pad.GetBoundingBox()
        cx,cy = ToMM(p.x),ToMM(p.y)
        hx,hy = ToMM(bb.GetWidth())/2, ToMM(bb.GetHeight())/2
        nn = pad.GetNetname(); nid = NID.get(nn, BLOCK)
        PADCENTERS.append((cx,cy,hx,hy,nn))
        if ref == "J1": continue
        exp = WMAX_HALF + CLR + QUANT
        i0,i1 = cell(cx-hx-exp-0.2), cell(cx+hx+exp+0.2)
        j0,j1 = cell(cy-hy-exp-0.2), cell(cy+hy+exp+0.2)
        for i in range(max(0,i0), min(NX,i1)+1):
            for j in range(max(0,j0), min(NY,j1)+1):
                if rect_dist(mm(i),mm(j), cx-hx,cy-hy,cx+hx,cy+hy) <= exp:
                    v = padF[i][j]
                    padF[i][j] = nid if v == 0 else (v if v == nid else BLOCK)
for i in range(cell(8.6), cell(11.3)+1):       # USB fan keepout (manual escapes)
    for j in range(cell(10.3), cell(19.7)+1):
        if 0 <= i <= NX and 0 <= j <= NY: hard[i][j] = 1

# mounting-hole sites (courtyard- and edge-aware), marked hard so routing avoids
CYBOX = {}
for ref,fp in FOOT.items():
    try:
        bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
        CYBOX[ref] = (ToMM(bb.GetLeft()),ToMM(bb.GetTop()),ToMM(bb.GetRight()),ToMM(bb.GetBottom()))
    except Exception:
        CYBOX[ref] = None
def hole_ok(hx,hy,r=2.5):
    if hx<r+0.3 or hx>BW-r-0.3 or hy<r+0.3 or hy>BH-r-0.3: return False
    for bx in CYBOX.values():
        if bx and rect_dist(hx,hy,bx[0],bx[1],bx[2],bx[3]) < r+0.2: return False
    return True
HOLES = []
for hx,hy in [(3.0,3.0),(3.0,27.0),(10.0,27.0),(46.0,15.0)]:
    if hole_ok(hx,hy):
        HOLES.append((hx,hy))
        for i in range(cell(hx-1.7),cell(hx+1.7)+1):
            for j in range(cell(hy-1.7),cell(hy+1.7)+1):
                if 0<=i<=NX and 0<=j<=NY and math.hypot(mm(i)-hx,mm(j)-hy)<1.7: hard[i][j]=1

# ---------- tracks / vias ----------
VIAS = []
def add_track(x1,y1,x2,y2,w,netname,layer):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(VECTOR2I(FromMM(x1),FromMM(y1))); t.SetEnd(VECTOR2I(FromMM(x2),FromMM(y2)))
    t.SetWidth(FromMM(w)); t.SetLayer(layer); t.SetNet(net(netname)); board.Add(t)
def add_via(x,y,netname):
    v = pcbnew.PCB_VIA(board); v.SetPosition(VECTOR2I(FromMM(x),FromMM(y)))
    v.SetDrill(FromMM(0.3)); v.SetWidth(FromMM(0.6))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNet(net(netname)); board.Add(v); VIAS.append((x,y))
def brush(x1,y1,x2,y2,w,nid,layer):
    r = w/2 + CLR + WMAX_HALF + QUANT
    i0,i1 = cell(min(x1,x2)-r-0.2), cell(max(x1,x2)+r+0.2)
    j0,j1 = cell(min(y1,y2)-r-0.2), cell(max(y1,y2)+r+0.2)
    for i in range(max(0,i0),min(NX,i1)+1):
        for j in range(max(0,j0),min(NY,j1)+1):
            px,py = mm(i),mm(j); dx,dy = x2-x1, y2-y1
            if dx==0 and dy==0: d = math.hypot(px-x1,py-y1)
            else:
                t = max(0,min(1,((px-x1)*dx+(py-y1)*dy)/(dx*dx+dy*dy)))
                d = math.hypot(px-(x1+t*dx), py-(y1+t*dy))
            if d <= r:
                v = trk[layer][i][j]
                trk[layer][i][j] = nid if v==0 else (v if v==nid else BLOCK)
def brush_via(x,y,nid):
    r = 0.3 + CLR + WMAX_HALF + QUANT
    for i in range(cell(x-r-0.2),cell(x+r+0.2)+1):
        for j in range(cell(y-r-0.2),cell(y+r+0.2)+1):
            if not (0<=i<=NX and 0<=j<=NY): continue
            d = math.hypot(mm(i)-x,mm(j)-y)
            if d <= 0.6: vno[i][j] = 1          # forbid another via too close (hole-to-hole)
            if d <= r:
                for layer in (pcbnew.F_Cu,pcbnew.B_Cu):
                    v = trk[layer][i][j]
                    trk[layer][i][j] = nid if v==0 else (v if v==nid else BLOCK)

DIRS = [(1,0),(-1,0),(0,1),(0,-1)]
LAYERS = [pcbnew.F_Cu, pcbnew.B_Cu]
def passable(i,j,layer,nid):
    if i<0 or i>NX or j<0 or j>NY or hard[i][j]: return False
    if layer==pcbnew.F_Cu and padF[i][j] not in (0,nid): return False
    return trk[layer][i][j] in (0,nid)

def route(p, q, netname):
    nid = NID[netname]; w = wid(netname)
    si,sj = cell(p[0]),cell(p[1]); gi,gj = cell(q[0]),cell(q[1])
    start = (si,sj,0,-1); dist = {start:0}; pqh=[(0,start)]; prev={}; goal=None
    while pqh:
        d,(i,j,l,dr) = heapq.heappop(pqh)
        if d > dist.get((i,j,l,dr),1e18): continue
        if i==gi and j==gj and l==0: goal=(i,j,l,dr); break
        for k,(dx,dy) in enumerate(DIRS):
            ni,nj = i+dx, j+dy
            if not passable(ni,nj,LAYERS[l],nid): continue
            nc = d + 10 + (14 if dr!=-1 and dr!=k else 0)
            ns=(ni,nj,l,k)
            if nc < dist.get(ns,1e18): dist[ns]=nc; prev[ns]=(i,j,l,dr); heapq.heappush(pqh,(nc,ns))
        if vno[i][j]==0 and passable(i,j,LAYERS[0],nid) and passable(i,j,LAYERS[1],nid):
            ns=(i,j,1-l,dr); nc=d+100
            if nc < dist.get(ns,1e18): dist[ns]=nc; prev[ns]=(i,j,l,dr); heapq.heappush(pqh,(nc,ns))
    if goal is None: return False
    cells=[]; s=goal
    while s in prev: cells.append(s); s=prev[s]
    cells.append(start); cells.reverse()
    pts=[(mm(c[0]),mm(c[1]),c[2]) for c in cells]
    pts[0]=(p[0],p[1],pts[0][2]); pts[-1]=(q[0],q[1],pts[-1][2])
    k=0; n=len(pts)
    while k < n-1:
        x1,y1,l1 = pts[k]; x2,y2,l2 = pts[k+1]
        if l1!=l2:
            add_via(x1,y1,netname); brush_via(x1,y1,nid); k+=1; continue
        j2=k+1; ddx=(x2>x1)-(x2<x1); ddy=(y2>y1)-(y2<y1)
        while j2<n-1:
            ax,ay,al=pts[j2]; bx,by,bl=pts[j2+1]
            if bl!=al: break
            if ((bx>ax)-(bx<ax),(by>ay)-(by<ay))!=(ddx,ddy): break
            j2+=1
        ex,ey,_=pts[j2]
        add_track(x1,y1,ex,ey,w,netname,LAYERS[l1]); brush(x1,y1,ex,ey,w,nid,LAYERS[l1]); k=j2
    return True

def mst(points):
    pts=list(points); n=len(pts); E=[]
    if n<=1: return E
    used={0}; rem=set(range(1,n))
    while rem:
        best=None
        for i in used:
            for j in rem:
                d=abs(pts[i][0]-pts[j][0])+abs(pts[i][1]-pts[j][1])
                if best is None or d<best[0]: best=(d,i,j)
        _,i,j=best; E.append((pts[i],pts[j])); used.add(j); rem.discard(j)
    return E

NETPADS={}
for ref,mapping in PADNET.items():
    for num,nn in mapping.items():
        for p in FOOT[ref].Pads():
            if p.GetNumber()==num:
                pos=p.GetPosition(); NETPADS.setdefault(nn,set()).add(
                    (round(ToMM(pos.x),3),round(ToMM(pos.y),3)))

# --- USB escapes ---
# Upper VBUS -> F.Cu stub to the +5V terminal at (13, 12.55).
add_track(10.045,12.55,13.0,12.55,0.5,"+5V",pcbnew.F_Cu); brush(10.045,12.55,13.0,12.55,0.5,NID["+5V"],pcbnew.F_Cu)
# Lower VBUS -> short F stub, then a B.Cu jumper up under the CC lane so the
# top copper stays clear for the CC traces to escape downward.
add_track(10.045,17.45,11.5,17.45,0.4,"+5V",pcbnew.F_Cu); brush(10.045,17.45,11.5,17.45,0.4,NID["+5V"],pcbnew.F_Cu)
add_via(11.5,17.45,"+5V"); brush_via(11.5,17.45,NID["+5V"])
add_track(11.5,17.45,11.5,12.55,0.4,"+5V",pcbnew.B_Cu); brush(11.5,17.45,11.5,12.55,0.4,NID["+5V"],pcbnew.B_Cu)
add_via(11.5,12.55,"+5V"); brush_via(11.5,12.55,NID["+5V"])   # lands on upper stub
# CC1 / CC2 break out at x=12 and head down to R6 / R7.
add_track(10.045,13.75,12.0,13.75,0.3,"CC1",pcbnew.F_Cu);  brush(10.045,13.75,12.0,13.75,0.3,NID["CC1"],pcbnew.F_Cu)
add_track(10.045,16.75,12.0,16.75,0.3,"CC2",pcbnew.F_Cu);  brush(10.045,16.75,12.0,16.75,0.3,NID["CC2"],pcbnew.F_Cu)
NETPADS["+5V"] -= {(10.045,12.55),(10.045,17.45)}; NETPADS["+5V"] |= {(13.0,12.55)}
NETPADS["CC1"] -= {(10.045,13.75)}; NETPADS["CC1"] |= {(12.0,13.75)}
NETPADS["CC2"] -= {(10.045,16.75)}; NETPADS["CC2"] |= {(12.0,16.75)}

failed=[]
order=sorted([n for n in NETLIST if n!="GND"], key=lambda n: len(NETPADS.get(n,[])))
for nn in order:
    pts=sorted(NETPADS.get(nn,[]))
    for a,b in mst(pts):
        if a==b: continue
        if not route(a,b,nn): failed.append((nn,a,b))
print("FAILED edges:", len(failed))
for f in failed: print("   FAIL",f)

# ---------- GND stitching vias ----------
def via_spot(x,y):
    i,j=cell(x),cell(y)
    if i<3 or i>NX-3 or j<3 or j>NY-3: return False
    if any(math.hypot(vx-x,vy-y)<0.9 for vx,vy in VIAS): return False
    for di in range(-3,4):
        for dj in range(-3,4):
            if hard[i+di][j+dj]: return False
            if padF[i+di][j+dj] not in (0,NID["GND"]): return False
            for l in LAYERS:
                if trk[l][i+di][j+dj] not in (0,NID["GND"]): return False
    return True
stitch=0; gy=3.5
while gy<BH-2:
    gx=4.0
    while gx<BW-2:
        if via_spot(gx,gy): add_via(gx,gy,"GND"); brush_via(gx,gy,NID["GND"]); stitch+=1
        gx+=8.0
    gy+=6.0
print("stitch vias:", stitch, " holes:", len(HOLES))

# ---------- mounting holes ----------
for k,(hx,hy) in enumerate(HOLES):
    mh=pcbnew.FootprintLoad(FPROOT+"\\MountingHole.pretty","MountingHole_2.2mm_M2")
    mh.SetReference("H%d"%(k+1)); board.Add(mh); mh.SetPosition(VECTOR2I(FromMM(hx),FromMM(hy)))
    mh.Reference().SetVisible(False); mh.Value().SetVisible(False)

# ---------- zones (filled after reload) ----------
if DO_ZONES:
    for layer in LAYERS:
        z=pcbnew.ZONE(board); z.SetLayer(layer); z.SetNet(net("GND"))
        z.SetIsFilled(False); z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        z.SetLocalClearance(FromMM(0.25)); z.SetMinThickness(FromMM(0.25))
        o=z.Outline(); o.NewOutline()
        for x,y in [(0.4,0.4),(BW-0.4,0.4),(BW-0.4,BH-0.4),(0.4,BH-0.4)]: o.Append(FromMM(x),FromMM(y))
        board.Add(z)

# ---------- silkscreen ----------
if DO_SILK:
    def silk(text,x,y,size=0.8,ang=0):
        t=pcbnew.PCB_TEXT(board); t.SetText(text); t.SetLayer(pcbnew.F_SilkS)
        t.SetPosition(VECTOR2I(FromMM(x),FromMM(y)))
        t.SetTextSize(VECTOR2I(FromMM(size),FromMM(size))); t.SetTextThickness(FromMM(0.15))
        if ang: t.SetTextAngle(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T))
        board.Add(t)
    silk("USB-C", 8.6, 7.4, 0.8)
    silk("CHG", 22.6, 10.7, 0.8)
    silk("FULL", 33.2, 10.7, 0.8)
    silk("BAT", 47.0, 11.2, 0.8)
    silk("OUT", 44.0, 18.5, 0.8)
    silk("Smart Earbuds Charger", 16.5, 28.4, 0.9)

pcbnew.SaveBoard(OUT, board)
print("saved pre-fill", flush=True)
if DO_ZONES:
    b2 = pcbnew.LoadBoard(OUT); b2.BuildConnectivity()
    pcbnew.ZONE_FILLER(b2).Fill(b2.Zones()); pcbnew.SaveBoard(OUT, b2)
    print("zones filled & saved", flush=True)
