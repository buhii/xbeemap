from math import pi, degrees, atan2, cos, sin
from pickle import load
half_pi = pi / 2.0

W = 610
H = 560
size(W, H)
FLAG_CIRCLE = False

MIN_DEG, MAX_DEG = 0, 180
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

def get_color(val):
    if val >= -40:
        v = 1
    elif val >= -45:
        v = 0.4
    elif val >= -50:
        v = 0.1
    else:
        v = 0
    return (1.0, 0.0, 0.0, v)

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
               5)

def deg2rad(deg):
    return deg * pi / 180.0

def draw_map_contour(x, y):
    # degree division lines
    nofill()
    stroke(0.1)
    strokewidth(0.3)
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
        stroke(0.1)
        c = BezierPath()
        arc(c, x, y, l * UNIT_PX, min_deg + 180, max_deg + 180, 0)
        c.draw()
        # length text
        nostroke()
        fill(0, 0, 0, 0.5)
        for deg in (min_deg + 180, max_deg + 180):
            tx = x + UNIT_PX * l * cos(deg2rad(deg))
            ty = y + UNIT_PX * l * sin(deg2rad(deg)) + 10
            text("%d.0[m]" % l, tx, ty)
        nofill()

def draw_map(x, y, result_dict):
    draw_map_contour(x, y)
    for deg in frange(MIN_DEG, MAX_DEG, 22.5):
        for l in frange(LENGTH_UNIT, RADIUS, LENGTH_UNIT):
            draw_baumkuchen(x, y, deg, l, result_dict[deg][l])

def draw_level(x, y):
    k = 4
    h = 10
    for i in range(-100, 1):
        if i != 0:
            fill(*get_color(i))
            rect(x + i * k, y, k, h)
        if i % 10 == 0:
            stroke(0.1)
            strokewidth(0.3)
            line(x + i * k, y, x + i * k, y + h)
            nostroke()
            fill(0, 0, 0, 0.5)
            if i == 0:
                text("%d[dBm]" % i, x + i * k - 5, y + 20)
            else:
                text("%d" % i, x + i * k - 8, y + 20)
    # box
    stroke(0.1)
    strokewidth(0.3)
    line(x, y, x + k * -100, y)
    line(x, y + h, x + k * -100, y + h)
    nostroke()

def draw_description(desc):
    font("Helvetica", 16)
    nostroke()
    fill(0, 0, 0, 0.5)
    text(desc, 20, 36)

# main
font("Helvetica", 10)
draw_map(H / 2 + 20, H * 2 / 3, load(open('rssi_0-180.p')))
draw_level(W - 40, H - 50)
draw_description(u"チップアンテナ型\n0-180°")
