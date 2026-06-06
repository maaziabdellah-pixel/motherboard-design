# -*- coding: utf-8 -*-
"""
Generator for motherboard-design.kicad_sch  (Smart Earbuds Charging PCB)
KiCad 10 schematic. Self-contained: embeds all used symbols in lib_symbols.

Net connectivity is built with power symbols (+5V / GND / +BATT) and net
labels on short pin stubs, plus PWR_FLAGs so ERC sees the rails as driven.
"""
import os, re, math, uuid, sys

KSYM = r"C:\Program Files\KiCad\10.0\share\kicad\symbols"
OUT  = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "motherboard-design.kicad_sch")
PROJECT = "motherboard-design"
ROOT_UUID = "11111111-2222-3333-4444-555555555555"   # stable root sheet uuid

def U():            # fresh uuid
    return str(uuid.uuid4())

# ---------------------------------------------------------------- lib helpers
def lib_block(libfile, part):
    """Return the full (symbol "<part>" ...) block from a .kicad_sym file."""
    s = open(os.path.join(KSYM, libfile), encoding="utf-8").read()
    key = '(symbol "%s"' % part
    i = s.find(key)
    if i < 0:
        raise SystemExit("symbol not found: %s in %s" % (part, libfile))
    depth = 0
    for j in range(i, len(s)):
        if s[j] == '(':
            depth += 1
        elif s[j] == ')':
            depth -= 1
            if depth == 0:
                return s[i:j + 1]
    raise SystemExit("unterminated symbol %s" % part)

PIN_RE = re.compile(
    r'\(pin\s+(\S+)\s+(\S+)\s*\(at ([-\d.]+) ([-\d.]+) ([\d.]+)\)\s*'
    r'\(length ([-\d.]+)\)(.*?)\(name "([^"]*)".*?\(number "([^"]*)"',
    re.S)

def parse_pins(block):
    """lib_id pin geometry -> {num: (lx, ly, angle, etype, name)}"""
    g = {}
    for m in PIN_RE.finditer(block):
        etype, style, x, y, a, length, mid, name, num = m.groups()
        g[num] = (float(x), float(y), int(float(a)), etype, name)
    return g

# ---------------------------------------------------------------- custom syms
def ic_symbol(libid, ref_prefix, value, pins, body=None, desc=""):
    """Build a rectangular IC symbol. pins: list of (num,name,x,y,angle,etype)."""
    xs = [p[2] for p in pins]; ys = [p[3] for p in pins]
    if body is None:
        # body rectangle inset 2.54 from pin connection points
        bx = max(abs(min(xs)), abs(max(xs))) - 2.54
        by = max(abs(min(ys)), abs(max(ys))) + 1.27
        body = (-bx, -by, bx, by)
    x1, y1, x2, y2 = body
    name = libid.split(":")[1]
    out = []
    out.append('\t\t(symbol "%s"' % libid)
    out.append('\t\t\t(pin_names (offset 1.016))')
    out.append('\t\t\t(exclude_from_sim no)')
    out.append('\t\t\t(in_bom yes)')
    out.append('\t\t\t(on_board yes)')
    out.append('\t\t\t(property "Reference" "%s" (at %.3f %.3f 0)'
               ' (effects (font (size 1.27 1.27))))' % (ref_prefix, x1, y2 + 1.27))
    out.append('\t\t\t(property "Value" "%s" (at %.3f %.3f 0)'
               ' (effects (font (size 1.27 1.27))))' % (value, x1, y1 - 2.0))
    out.append('\t\t\t(property "Footprint" "" (at 0 0 0)'
               ' (effects (font (size 1.27 1.27)) (hide yes)))')
    out.append('\t\t\t(property "Datasheet" "" (at 0 0 0)'
               ' (effects (font (size 1.27 1.27)) (hide yes)))')
    out.append('\t\t\t(property "Description" "%s" (at 0 0 0)'
               ' (effects (font (size 1.27 1.27)) (hide yes)))' % desc)
    # graphic body
    out.append('\t\t\t(symbol "%s_0_1"' % name)
    out.append('\t\t\t\t(rectangle (start %.3f %.3f) (end %.3f %.3f)'
               ' (stroke (width 0.254) (type default)) (fill (type background)))'
               % (x1, y1, x2, y2))
    out.append('\t\t\t)')
    # pins
    out.append('\t\t\t(symbol "%s_1_1"' % name)
    for num, pname, px, py, pa, et in pins:
        out.append('\t\t\t\t(pin %s line (at %.3f %.3f %d) (length 2.54)'
                   ' (name "%s" (effects (font (size 1.016 1.016))))'
                   ' (number "%s" (effects (font (size 1.016 1.016)))))'
                   % (et, px, py, pa, pname, num))
    out.append('\t\t\t)')
    out.append('\t\t\t(embedded_fonts no)')
    out.append('\t\t)')
    return "\n".join(out)

# TP4056 (SOIC-8). Connection points at x=+-10.16, body to +-7.62.
TP4056_PINS = [
    ("1", "TEMP",  -10.16,  3.81, 0, "passive"),
    ("2", "PROG",  -10.16,  1.27, 0, "passive"),
    ("3", "GND",   -10.16, -1.27, 0, "power_in"),
    ("4", "VCC",   -10.16, -3.81, 0, "power_in"),
    ("5", "BAT",    10.16, -3.81, 180, "passive"),
    ("6", "STDBY",  10.16, -1.27, 180, "passive"),
    ("7", "CHRG",   10.16,  1.27, 180, "passive"),
    ("8", "CE",     10.16,  3.81, 180, "passive"),
]
DW01A_PINS = [
    ("1", "OD",  -7.62,  2.54, 0, "passive"),
    ("2", "CS",  -7.62,  0.00, 0, "passive"),
    ("3", "OC",  -7.62, -2.54, 0, "passive"),
    ("4", "TD",   7.62, -2.54, 180, "passive"),
    ("5", "VDD",  7.62,  0.00, 180, "passive"),
    ("6", "VSS",  7.62,  2.54, 180, "passive"),
]
FS8205_PINS = [
    ("1", "S1", -7.62,  2.54, 0, "passive"),
    ("2", "G1", -7.62,  0.00, 0, "passive"),
    ("3", "S2", -7.62, -2.54, 0, "passive"),
    ("4", "G2",  7.62, -2.54, 180, "passive"),
    ("5", "D2",  7.62,  0.00, 180, "passive"),
    ("6", "D1",  7.62,  2.54, 180, "passive"),
]

CUSTOM = {
    "EarbudsCharger:TP4056":  ic_symbol("EarbudsCharger:TP4056",  "U", "TP4056",  TP4056_PINS,  desc="1A standalone Li-ion charger"),
    "EarbudsCharger:DW01A":   ic_symbol("EarbudsCharger:DW01A",   "U", "DW01A",   DW01A_PINS,   desc="1-cell Li-ion protection IC"),
    "EarbudsCharger:FS8205A": ic_symbol("EarbudsCharger:FS8205A", "Q", "FS8205A", FS8205_PINS,  desc="Dual N-MOSFET protection switch"),
}
CUSTOM_GEOM = {
    "EarbudsCharger:TP4056":  {p[0]: (p[2], p[3], p[4], p[5], p[1]) for p in TP4056_PINS},
    "EarbudsCharger:DW01A":   {p[0]: (p[2], p[3], p[4], p[5], p[1]) for p in DW01A_PINS},
    "EarbudsCharger:FS8205A": {p[0]: (p[2], p[3], p[4], p[5], p[1]) for p in FS8205_PINS},
}

# ---------------------------------------------------------------- std symbols
STD = [   # (libid, libfile, libpart)
    ("Device:R",                                "Device.kicad_sym",            "R"),
    ("Device:C",                                "Device.kicad_sym",            "C"),
    ("Device:LED",                              "Device.kicad_sym",            "LED"),
    ("Connector:USB_C_Receptacle_USB2.0_16P",   "Connector.kicad_sym",         "USB_C_Receptacle_USB2.0_16P"),
    ("Connector_Generic:Conn_01x02",            "Connector_Generic.kicad_sym", "Conn_01x02"),
    ("power:GND",                               "power.kicad_sym",             "GND"),
    ("power:+5V",                               "power.kicad_sym",             "+5V"),
    ("power:+BATT",                             "power.kicad_sym",             "+BATT"),
    ("power:PWR_FLAG",                          "power.kicad_sym",             "PWR_FLAG"),
]
LIBSYMS = {}     # libid -> text
GEOM    = {}     # libid -> pin geometry
for libid, libfile, libpart in STD:
    blk = lib_block(libfile, libpart)
    blk = blk.replace('(symbol "%s"' % libpart, '(symbol "%s"' % libid, 1)
    LIBSYMS[libid] = blk
    GEOM[libid] = parse_pins(blk)
for libid, blk in CUSTOM.items():
    LIBSYMS[libid] = blk
    GEOM[libid] = CUSTOM_GEOM[libid]

# ---------------------------------------------------------------- components
# ref: (libid, value, footprint, x, y)
COMPS = {
 "J1": ("Connector:USB_C_Receptacle_USB2.0_16P", "USB-C", "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12", 60, 105),
 "U1": ("EarbudsCharger:TP4056",  "TP4056",  "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",       140, 100),
 "U2": ("EarbudsCharger:DW01A",   "DW01A",   "Package_TO_SOT_SMD:SOT-23-6",               212, 122),
 "Q1": ("EarbudsCharger:FS8205A", "FS8205A", "Package_TO_SOT_SMD:SOT-23-6",               212, 86),
 "D1": ("Device:LED", "Red",   "LED_SMD:LED_0805_2012Metric", 128, 56),
 "D2": ("Device:LED", "Green", "LED_SMD:LED_0805_2012Metric", 166, 56),
 "R1": ("Device:R", "2k",   "Resistor_SMD:R_0805_2012Metric", 140, 142),
 "R2": ("Device:R", "1k",   "Resistor_SMD:R_0805_2012Metric", 118, 56),
 "R3": ("Device:R", "1k",   "Resistor_SMD:R_0805_2012Metric", 156, 56),
 "R4": ("Device:R", "100R", "Resistor_SMD:R_0805_2012Metric", 184, 104),
 "R5": ("Device:R", "2k",   "Resistor_SMD:R_0805_2012Metric", 238, 122),
 "R6": ("Device:R", "5.1k", "Resistor_SMD:R_0805_2012Metric", 86, 140),
 "R7": ("Device:R", "5.1k", "Resistor_SMD:R_0805_2012Metric", 98, 140),
 "C1": ("Device:C", "10uF", "Capacitor_SMD:C_0805_2012Metric", 104, 78),
 "C2": ("Device:C", "10uF", "Capacitor_SMD:C_0805_2012Metric", 176, 104),
 "C3": ("Device:C", "100nF","Capacitor_SMD:C_0805_2012Metric", 246, 108),
 "J2": ("Connector_Generic:Conn_01x02", "BATTERY", "Connector_JST:JST_PH_B2B-PH-SM4-TB_1x02-1MP_P2.00mm_Vertical", 268, 84),
 "J3": ("Connector_Generic:Conn_01x02", "OUTPUT",  "Connector_JST:JST_PH_B2B-PH-SM4-TB_1x02-1MP_P2.00mm_Vertical", 268, 120),
}

# snap placements to the 1.27 mm (50 mil) connection grid so every pin/wire
# endpoint lands on grid (all symbol pin offsets are multiples of 1.27).
def snap(v, g=1.27):
    return round(round(v / g) * g, 4)
COMPS = {r: (lib, val, fp, snap(x), snap(y)) for r, (lib, val, fp, x, y) in COMPS.items()}

# per-component pin -> net   (USB lists only the representative pins to wire;
#                             stacked duplicates are connected automatically)
NETS = {
 "J1": {"A4":"+5V", "A1":"GND", "SH":"GND", "A5":"CC1", "B5":"CC2",
        "A6":"NC", "B6":"NC", "A7":"NC", "B7":"NC", "A8":"NC", "B8":"NC"},
 "U1": {"1":"GND", "2":"PROG", "3":"GND", "4":"+5V", "5":"+BATT",
        "6":"STDBY", "7":"CHRG", "8":"+5V"},
 "U2": {"1":"OD", "2":"DW_CS", "3":"OC", "4":"NC", "5":"DW_VCC", "6":"BATT-"},
 "Q1": {"1":"BATT-", "2":"OD", "3":"GND", "4":"OC", "5":"FDRAIN", "6":"FDRAIN"},
 "D1": {"1":"CHRG", "2":"D_RED"},
 "D2": {"1":"STDBY","2":"D_GRN"},
 "R1": {"1":"PROG", "2":"GND"},
 "R2": {"1":"+5V",  "2":"D_RED"},
 "R3": {"1":"+5V",  "2":"D_GRN"},
 "R4": {"1":"+BATT","2":"DW_VCC"},
 "R5": {"1":"DW_CS","2":"GND"},
 "R6": {"1":"CC1",  "2":"GND"},
 "R7": {"1":"CC2",  "2":"GND"},
 "C1": {"1":"+5V",  "2":"GND"},
 "C2": {"1":"+BATT","2":"GND"},
 "C3": {"1":"DW_VCC","2":"BATT-"},
 "J2": {"1":"+BATT","2":"BATT-"},
 "J3": {"1":"+BATT","2":"GND"},
}

POWER_SYMS = {"+5V": "power:+5V", "GND": "power:GND", "+BATT": "power:+BATT"}

# ---------------------------------------------------------------- geometry
def pin_abs(sx, sy, lx, ly):
    return (round(sx + lx, 4), round(sy - ly, 4))     # schematic Y is flipped

def outward(angle):
    a = math.radians(angle)
    return (-math.cos(a), math.sin(a))                 # unit vec away from body

# ---------------------------------------------------------------- emit
items = []        # schematic body s-expressions
pwr_n = [0]
flg_n = [0]

def emit_symbol(ref, libid, value, footprint, sx, sy):
    geom = GEOM[libid]
    s = []
    s.append('\t(symbol')
    s.append('\t\t(lib_id "%s")' % libid)
    s.append('\t\t(at %.4f %.4f 0)' % (sx, sy))
    s.append('\t\t(unit 1)')
    s.append('\t\t(exclude_from_sim no)')
    s.append('\t\t(in_bom yes)')
    s.append('\t\t(on_board yes)')
    s.append('\t\t(dnp no)')
    s.append('\t\t(uuid "%s")' % U())
    s.append('\t\t(property "Reference" "%s" (at %.4f %.4f 0)'
             ' (effects (font (size 1.27 1.27))))' % (ref, sx, sy - 12.0))
    s.append('\t\t(property "Value" "%s" (at %.4f %.4f 0)'
             ' (effects (font (size 1.27 1.27))))' % (value, sx, sy + 14.0))
    s.append('\t\t(property "Footprint" "%s" (at %.4f %.4f 0)'
             ' (effects (font (size 1.27 1.27)) (hide yes)))' % (footprint, sx, sy))
    s.append('\t\t(property "Datasheet" "" (at %.4f %.4f 0)'
             ' (effects (font (size 1.27 1.27)) (hide yes)))' % (sx, sy))
    s.append('\t\t(property "Description" "" (at %.4f %.4f 0)'
             ' (effects (font (size 1.27 1.27)) (hide yes)))' % (sx, sy))
    for num in geom:
        s.append('\t\t(pin "%s" (uuid "%s"))' % (num, U()))
    s.append('\t\t(instances (project "%s" (path "/%s"'
             ' (reference "%s") (unit 1))))' % (PROJECT, ROOT_UUID, ref))
    s.append('\t)')
    items.append("\n".join(s))

def emit_wire(x1, y1, x2, y2):
    items.append('\t(wire (pts (xy %.4f %.4f) (xy %.4f %.4f))'
                 ' (stroke (width 0) (type default)) (uuid "%s"))'
                 % (x1, y1, x2, y2, U()))

def emit_label(text, x, y, ang):
    items.append('\t(label "%s" (at %.4f %.4f %d)'
                 ' (effects (font (size 1.27 1.27)) (justify left bottom))'
                 ' (uuid "%s"))' % (text, x, y, ang, U()))

def emit_noconnect(x, y):
    items.append('\t(no_connect (at %.4f %.4f) (uuid "%s"))' % (x, y, U()))

def emit_power(libid, value, x, y, rot):
    pwr_n[0] += 1
    ref = "#PWR%03d" % pwr_n[0]
    s = []
    s.append('\t(symbol')
    s.append('\t\t(lib_id "%s")' % libid)
    s.append('\t\t(at %.4f %.4f %d)' % (x, y, rot))
    s.append('\t\t(unit 1)')
    s.append('\t\t(exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)')
    s.append('\t\t(uuid "%s")' % U())
    s.append('\t\t(property "Reference" "%s" (at %.4f %.4f 0)'
             ' (effects (font (size 1.27 1.27)) (hide yes)))' % (ref, x, y))
    s.append('\t\t(property "Value" "%s" (at %.4f %.4f %d)'
             ' (effects (font (size 1.27 1.27))))' % (value, x, y, rot))
    s.append('\t\t(property "Footprint" "" (at %.4f %.4f 0)'
             ' (effects (font (size 1.27 1.27)) (hide yes)))' % (x, y))
    s.append('\t\t(property "Datasheet" "" (at %.4f %.4f 0)'
             ' (effects (font (size 1.27 1.27)) (hide yes)))' % (x, y))
    s.append('\t\t(pin "1" (uuid "%s"))' % U())
    s.append('\t\t(instances (project "%s" (path "/%s"'
             ' (reference "%s") (unit 1))))' % (PROJECT, ROOT_UUID, ref))
    s.append('\t)')
    items.append("\n".join(s))

def emit_flag(x, y):
    flg_n[0] += 1
    ref = "#FLG%03d" % flg_n[0]
    s = []
    s.append('\t(symbol')
    s.append('\t\t(lib_id "power:PWR_FLAG")')
    s.append('\t\t(at %.4f %.4f 0)' % (x, y))
    s.append('\t\t(unit 1)')
    s.append('\t\t(exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)')
    s.append('\t\t(uuid "%s")' % U())
    s.append('\t\t(property "Reference" "%s" (at %.4f %.4f 0)'
             ' (effects (font (size 1.27 1.27)) (hide yes)))' % (ref, x, y))
    s.append('\t\t(property "Value" "PWR_FLAG" (at %.4f %.4f 0)'
             ' (effects (font (size 1.27 1.27))))' % (x, y - 2.0))
    s.append('\t\t(property "Footprint" "" (at %.4f %.4f 0)'
             ' (effects (font (size 1.27 1.27)) (hide yes)))' % (x, y))
    s.append('\t\t(property "Datasheet" "" (at %.4f %.4f 0)'
             ' (effects (font (size 1.27 1.27)) (hide yes)))' % (x, y))
    s.append('\t\t(pin "1" (uuid "%s"))' % U())
    s.append('\t\t(instances (project "%s" (path "/%s"'
             ' (reference "%s") (unit 1))))' % (PROJECT, ROOT_UUID, ref))
    s.append('\t)')
    items.append("\n".join(s))

def pwr_rotation(libid, ox, oy):
    """cosmetic rotation so the symbol graphic points outward"""
    if libid == "power:GND":
        if oy > 0.5:  return 0
        if oy < -0.5: return 180
        if ox > 0.5:  return 270
        return 90
    else:  # +5V / +BATT graphic points up by default
        if oy < -0.5: return 0
        if oy > 0.5:  return 180
        if ox > 0.5:  return 90
        return 270

STUB = 3.81

# place all components
for ref, (libid, value, fp, sx, sy) in COMPS.items():
    emit_symbol(ref, libid, value, fp, sx, sy)

# wire every assigned pin
for ref, (libid, value, fp, sx, sy) in COMPS.items():
    geom = GEOM[libid]
    netmap = NETS[ref]
    for num, net in netmap.items():
        lx, ly, ang, et, pname = geom[num]
        px, py = pin_abs(sx, sy, lx, ly)
        ox, oy = outward(ang)
        ex, ey = round(px + STUB * ox, 4), round(py + STUB * oy, 4)
        if net == "NC":
            emit_noconnect(px, py)
            continue
        emit_wire(px, py, ex, ey)
        if net in POWER_SYMS:
            emit_power(POWER_SYMS[net], net, ex, ey, pwr_rotation(POWER_SYMS[net], ox, oy))
        else:
            lang = 180 if ox < -0.3 else 0
            emit_label(net, ex, ey, lang)

# PWR_FLAG + rail symbol clusters so ERC sees rails as driven
for net, (fx, fy) in {"+5V": (snap(40), snap(70)), "GND": (snap(40), snap(150)),
                      "+BATT": (snap(292), snap(70))}.items():
    emit_wire(fx, fy, fx, fy + 5.08)
    emit_power(POWER_SYMS[net], net, fx, fy, pwr_rotation(POWER_SYMS[net], 0, -1))
    emit_flag(fx, fy + 5.08)

# ---------------------------------------------------------------- assemble
hdr = []
hdr.append('(kicad_sch')
hdr.append('\t(version 20260306)')
hdr.append('\t(generator "eeschema")')
hdr.append('\t(generator_version "10.0")')
hdr.append('\t(uuid "%s")' % ROOT_UUID)
hdr.append('\t(paper "A4")')
hdr.append('\t(title_block')
hdr.append('\t\t(title "Smart Earbuds Charging PCB")')
hdr.append('\t\t(date "2026-06-06")')
hdr.append('\t\t(rev "1.0")')
hdr.append('\t\t(company "OSCKA Solution")')
hdr.append('\t)')
hdr.append('\t(lib_symbols')
for libid in sorted(LIBSYMS):
    hdr.append(LIBSYMS[libid])
hdr.append('\t)')

ftr = []
ftr.append('\t(sheet_instances')
ftr.append('\t\t(path "/" (page "1"))')
ftr.append('\t)')
ftr.append('\t(embedded_fonts no)')
ftr.append(')')

doc = "\n".join(hdr) + "\n" + "\n".join(items) + "\n" + "\n".join(ftr) + "\n"
open(OUT, "w", encoding="utf-8").write(doc)
print("wrote", OUT, "(%d bytes, %d items)" % (len(doc), len(items)))

# ---------------------------------------------------------------- project lib
PRJDIR = os.path.dirname(OUT)
libdoc = ['(kicad_symbol_lib', '\t(version 20251024)',
          '\t(generator "earbuds_charger_gen")', '\t(generator_version "10.0")']
for libid in CUSTOM:
    name = libid.split(":")[1]
    libdoc.append(CUSTOM[libid].replace('(symbol "%s"' % libid,
                                         '(symbol "%s"' % name, 1))
libdoc.append(')')
libpath = os.path.join(PRJDIR, "EarbudsCharger.kicad_sym")
open(libpath, "w", encoding="utf-8").write("\n".join(libdoc) + "\n")
print("wrote", libpath)

tbl = ('(sym_lib_table\n\t(version 7)\n'
       '\t(lib (name "EarbudsCharger")(type "KiCad")'
       '(uri "${KIPRJMOD}/EarbudsCharger.kicad_sym")(options "")'
       '(descr "Smart Earbuds Charging PCB project symbols"))\n)\n')
tblpath = os.path.join(PRJDIR, "sym-lib-table")
open(tblpath, "w", encoding="utf-8").write(tbl)
print("wrote", tblpath)
