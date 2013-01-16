from math import pi, degrees, atan2, cos, sin
from pickle import load
half_pi = pi / 2.0

W = 690
H = 640
size(W, H - 160)   # - 160
FLAG_CIRCLE = True
CIRCLESIZE = 8
LABELCOLOR = (0, 0, 0, 1)

MIN_DEG, MAX_DEG = 0, 180.0
RADIUS = 5
LENGTH_UNIT = 0.125 / 2
UNIT_PX = H / RADIUS / 2

def frange(min, max, unit):
    result = []
    tmp = min
    while tmp <= max:
        result.append(tmp)
        tmp += unit
    return result

def ring(v):
    blue = 1.77
    if v > blue:
        v = blue
    if v < 0:
        v += abs(int(v)) + 1
    elif v > 1:
        v -= int(v)
    return v

def get_color(val):
    if val >= -35:
        r, v = 0.6, 1
    elif val >= -40:
        r, v = 1, 1
    elif val >= -45:
        r, v = 1, 0.4
    elif val >= -50:
        r, v = 1, 0.03
    elif val >= -60 and False:
        r, v = 1, 0
    else:
        r, v = 1, 0
    #v, r = (60 + val) / 40.0, 1
    return (ring(-val / 45.0 + 0.51), 1, (90 + val) / 30.0)

def arc(self, originx, originy, radius, startangle, endangle, clockwise=True):
    """
    Draw an arc, the clockwise direction is relative to the orientation of the axis, 
    so it looks flipped compared to the normal Cartesial Plane
    # see http://nodebox.net/code/index.php/shared_2008-12-21-20-09-18 
    """
    self._segment_cache = None
    self.inheritFromContext() 
    if clockwise: 
        self._nsBezierPath.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_clockwise_( (originx, originy), radius, startangle, endangle, 1)
    else:
        self._nsBezierPath.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_( (originx, originy), radius, startangle, endangle)

def circle(x, y, r):
    oval(x - r / 2, y - r / 2, r, r)

def draw_baumkuchen(x, y, deg, l, val):
    deg = 360 - deg
    deg_cover = (180 / 16.0)
    deg_start = (deg - deg_cover)
    deg_end = (deg + deg_cover)
    colormode(HSB)
    nostroke()
    fill(*get_color(val))
    
    if not FLAG_CIRCLE:
        c = BezierPath()
        arc(c, x, y, l * UNIT_PX, deg_start, deg_end, 0)
        arc(c, x, y, (l - LENGTH_UNIT) * UNIT_PX, deg_end, deg_start, 1)
        c.closepath()
        c.draw()
    else:        
        circle(x + UNIT_PX * l * cos(deg2rad(deg)),
               y + UNIT_PX * l * sin(deg2rad(deg)),
               CIRCLESIZE)
    colormode(RGB)

def deg2rad(deg):
    return deg * pi / 180.0

def draw_map_contour(x, y):
    # degree division lines
    nofill()
    stroke(0.1)
    strokewidth(0.5)
    min_deg = MIN_DEG
    max_deg = MAX_DEG
    if not FLAG_CIRCLE:
        min_deg, max_deg = min_deg - (180 / 16.0), max_deg + (180 / 16.0)
    for deg in frange(min_deg, max_deg, 22.5):
        deg = 360 - deg
        line_end = (x + UNIT_PX * RADIUS * cos(deg2rad(deg)),
                    y + UNIT_PX * RADIUS * sin(deg2rad(deg)))
        line(x, y, *line_end)
    # length division arc
    for l in range(1, RADIUS + 1):
        stroke(*LABELCOLOR)
        c = BezierPath()
        arc(c, x, y, l * UNIT_PX, min_deg + 180, max_deg + 180, 0)
        c.draw()
        # length text
        nostroke()
        fill(*LABELCOLOR)
        for deg in (min_deg + 180, max_deg + 180):
            tx = x + UNIT_PX * l * cos(deg2rad(deg)) - 10
            ty = y + UNIT_PX * l * sin(deg2rad(deg)) + 18
            text("%d.0[m]" % l, tx, ty)
        nofill()
    # center meter label
    fill(*LABELCOLOR)
    text("0.0[m]", x - 10, y + 18)
    nofill()

def draw_map(x, y, result_dict):
    draw_map_contour(x, y)
    for l in reversed(frange(LENGTH_UNIT, RADIUS, LENGTH_UNIT)):
        for deg in frange(MIN_DEG, MAX_DEG, 22.5):
            if deg in result_dict and l in result_dict[deg]:
                draw_baumkuchen(x, y, deg, l, result_dict[deg][l])

def draw_level(x, y):
    k = 4
    h = 10
    low = -70
    max = -20
    for i in range(low, max + 1):
        if i != max:
            colormode(HSB)
            fill(*get_color(i))
            rect(x + i * k, y, k, h)
            colormode(RGB)
        if i % 10 == 0:
            stroke(0.5)
            strokewidth(1)
            line(x + i * k, y, x + i * k, y + h)
            nostroke()
            fill(*LABELCOLOR)
            if i == max:
                text("%d[dBm]" % i, x + i * k - 15, y + 24)
            else:
                text("%d" % i, x + i * k - 12, y + 24)
    # box
    stroke(*LABELCOLOR)
    strokewidth(0)
    line(x + k * max, y, x + k * low, y)
    line(x + k * max, y + h, x + k * low, y + h)
    nostroke()

def draw_description(desc):
    font("Helvetica", 16)
    nostroke()
    fill(*LABELCOLOR)
    text(desc, 20, 36)

# main
background(1)
font("Helvetica", 14)

datafiles = [
    {'desc':u"チップアンテナ型\n0-180°",
     'file':'rssi_0-180.p'},
    {'desc':u"チップアンテナ型\n180-360°",
     'file':'rssi_180-360.p'},
    {'desc':u"チップアンテナ型\n180-202.5°",
     'file':'rssi-180-2025.p'},
    {'desc':u"ホイップアンテナ型\n0-180°",
     'file':'rssi_whip_0-180.p'},
    {'desc':u"ホイップアンテナ型\n180-360°",
     'file':'rssi_whip_180-360.p'}
    ]
index = 4
draw_map(H / 2 + 20, H * 2 / 3, load(open(datafiles[index]['file'])))
draw_level(W + 20, 30)
# draw_description(datafiles[index]['desc'])
