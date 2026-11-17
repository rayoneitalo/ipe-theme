import random
import sys

R = random.Random(2087)
W, H = 1600, 1000
TOP_PAD = 280
VH = H + TOP_PAD
out = []


def a(s):
    out.append(s)


def n(x):
    s = f"{x:.1f}"
    return s[:-2] if s.endswith(".0") else s


def lerp(lo, hi, k):
    return lo + (hi - lo) * k


LAYERS = [
    dict(body="#16171b", top=(150, 500), w=(40, 100), cell=(6, 8), win=(3, 4), colors=("#5d626b", "#80858e"), gap=6),
    dict(body="#101114", top=(250, 580), w=(60, 140), cell=(8, 11), win=(4, 6), colors=("#8a9099", "#cdd2d8"), gap=14),
    dict(body="#0a0b0d", top=(370, 640), w=(80, 190), cell=(11, 15), win=(5, 8), colors=("#9aa0a8", "#e6eaee"), gap=22),
]
WORDS_V = ["HOTEL", "BAR", "LAN", "24H", "ラーメン", "居酒屋", "MOTEL"]
WORDS_H = ["FARMÁCIA 24H", "CÂMBIO", "PASTEL", "LIBERDADE", "DROGARIA"]
MONO = "Menlo,Consolas,'DejaVu Sans Mono',monospace"

signs = []
beacons = []


def window_patterns(prefix, cfg, lits):
    cw, ch = cfg["cell"]
    ww, wh = cfg["win"]
    cols, rows = 8, 12
    for vi, lit in enumerate(lits):
        a(f'<pattern id="{prefix}{vi}" width="{cols*cw}" height="{rows*ch}" patternUnits="userSpaceOnUse">')
        for r in range(rows):
            for c in range(cols):
                if R.random() < lit:
                    col = R.choice(cfg["colors"])
                    op = n(lerp(.3, 1, R.random()))
                    a(f'<rect x="{c*cw}" y="{r*ch}" width="{ww}" height="{wh}" fill="{col}" opacity="{op}"/>')
        a("</pattern>")


def pixo(x, y, w, size):
    gw = size * .36
    count = min(9, int(w // (gw * 1.5)))
    d = []
    for i in range(count):
        gx = x + i * gw * 1.5
        k = R.randrange(4)
        d.append(f"M{n(gx)} {n(y+size)}V{n(y+size*R.random()*.2)}")
        if k == 0:
            d.append(f"L{n(gx+gw)} {n(y)}V{n(y+size)}")
        elif k == 1:
            d.append(f"M{n(gx)} {n(y+size*.45)}L{n(gx+gw)} {n(y+size*.2)}M{n(gx+gw)} {n(y)}V{n(y+size)}")
        elif k == 2:
            d.append(f"M{n(gx)} {n(y)}L{n(gx+gw)} {n(y+size*.5)}L{n(gx)} {n(y+size)}")
        else:
            d.append(f"M{n(gx+gw*.5)} {n(y)}V{n(y+size)}M{n(gx)} {n(y+size*.3)}L{n(gx+gw)} {n(y+size*.12)}")
    if d:
        a(f'<path d="{"".join(d)}" stroke="#cdd2d8" stroke-opacity=".2" stroke-width="1.3" fill="none"/>')


def add_sign(layer, x, top, bw, cs):
    if R.random() < .55:
        text = R.choice(WORDS_V)
        w, h = cs * 1.7, len(text) * cs * 1.3 + cs * .5
        y = top + lerp(.08, .45, R.random()) * (690 - top)
        if y + h > 690:
            return
        sx = x + 3 if R.random() < .5 else x + bw - w - 3
        signs.append(dict(layer=layer, text=text, vertical=True, x=sx, y=y, w=w, h=h, cs=cs))
    else:
        text = R.choice(WORDS_H)
        w = len(text) * cs * .62 + cs * 1.2
        if w > bw * 1.1:
            return
        signs.append(dict(layer=layer, text=text, vertical=False, x=x + bw / 2 - w / 2, y=top - cs * 1.9 - 3, w=w, h=cs * 1.8, cs=cs))


def building(x, top, bw, cfg, li, prefix):
    body = cfg["body"]
    a(f'<rect x="{n(x)}" y="{n(top)}" width="{n(bw)}" height="{n(H-top)}" fill="{body}"/>')
    roof = top
    if R.random() < .35:
        sw, sh = bw * lerp(.4, .7, R.random()), lerp(8, 30, R.random())
        a(f'<rect x="{n(x+(bw-sw)/2)}" y="{n(top-sh)}" width="{n(sw)}" height="{n(sh)}" fill="{body}"/>')
        roof = top - sh
    if R.random() < .4:
        tw = min(bw * .3, 18)
        a(f'<rect x="{n(x+R.random()*(bw-tw))}" y="{n(top-tw*.6)}" width="{n(tw)}" height="{n(tw*.6)}" fill="{body}"/>')
    if R.random() < .3:
        ax, ah = x + bw * lerp(.2, .8, R.random()), lerp(12, 40, R.random())
        a(f'<path d="M{n(ax)} {n(roof)}V{n(roof-ah)}" stroke="{body}" stroke-width="2"/>')
        beacons.append((ax, roof - ah, 1.6))
    a(f'<rect x="{n(x)}" y="{n(top)}" width="1" height="{n(H-top)}" fill="#c8ced6" opacity=".08"/>')
    v = R.randrange(3)
    a(f'<rect width="{n(bw-8)}" height="{n(max(0, 745-top-8))}" fill="url(#{prefix}{v})" transform="translate({n(x+4)} {n(top+8)})"/>')
    if li in (1, 2) and R.random() < (.2 if li == 1 else .45):
        pixo(x + 6, top + 10, bw - 12, 12 if li == 1 else 18)
    if li == 3:
        pixo(x + 8, top + 14, bw - 16, 24)
    if li in (1, 2) and R.random() < (.14 if li == 1 else .36):
        add_sign(li, x, top, bw, 10 if li == 1 else 13)


def mast(x, top):
    base, half = 560, 8
    d = [f"M{n(x)} {n(top)}L{n(x-half)} {base}M{n(x)} {n(top)}L{n(x+half)} {base}"]
    y, s = top + 10, 1
    while y < base:
        k = (y - top) / (base - top)
        d.append(f"M{n(x-half*k)} {n(y)}L{n(x+half*k*s)} {n(y+10)}")
        y += 10
        s = -s
    a(f'<path d="{"".join(d)}" stroke="#202227" stroke-width="1.2" fill="none"/>')
    beacons.append((x, top - 2, 2.2))
    beacons.append((x, top + (base - top) * .4, 1.6))


def sign_svg(s, delay, broken):
    cls = "fb" if broken else "fl"
    x, y, w, h, cs = s["x"], s["y"], s["w"], s["h"], s["cs"]
    a(f'<g class="{cls}" style="animation-delay:-{n(delay)}s">')
    a(f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" fill="#060608" fill-opacity=".9" stroke="#e9ecef" stroke-opacity=".55"/>')
    a(f'<g filter="url(#glow)" fill="#eef1f4" font-family="{MONO}" font-weight="700" font-size="{n(cs)}" text-anchor="middle">')
    if s["vertical"]:
        for i, ch in enumerate(s["text"]):
            a(f'<text x="{n(x+w/2)}" y="{n(y+cs*1.25+i*cs*1.3)}">{ch}</text>')
    else:
        a(f'<text x="{n(x+w/2)}" y="{n(y+h/2+cs*.36)}">{s["text"]}</text>')
    a("</g></g>")



def eye_sign():
    """Neon eye above the billboard."""
    # The mod swaps everything between the markers for the playing track.
    a('<!--EYE--><g class="fl" style="animation-delay:-3s">')
    a('<rect x="1348" y="150" width="60" height="40" fill="#060608" fill-opacity=".9" stroke="#e9ecef" stroke-opacity=".5"/>')
    a('<g filter="url(#glow)" stroke="#eef1f4" stroke-width="2" fill="none">')
    a('<path d="M1360 170Q1378 156 1396 170Q1378 184 1360 170Z"/><path d="M1378 177V186" stroke-width="1.4"/>')
    a('</g><circle cx="1378" cy="170" r="4.5" fill="#eef1f4" filter="url(#glow)"/></g><!--/EYE-->')


def clock_tower():
    """Clock frozen at two minutes to midnight, with a cinema marquee below."""
    import math
    x, top, w = 232, 380, 100
    cx, cy, r = x + w / 2, 440, 32
    a(f'<rect x="{x}" y="{top}" width="{w}" height="{H-top}" fill="#0a0b0d"/>')
    a(f'<rect x="{x+w/2-12}" y="{top-26}" width="24" height="26" fill="#0a0b0d"/>')
    a(f'<rect x="{x}" y="{top}" width="1" height="{H-top}" fill="#c8ced6" opacity=".1"/>')
    a(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#08090b" stroke="#e9ecef" stroke-opacity=".8" stroke-width="2" filter="url(#glow)"/>')
    ticks = []
    for k in range(12):
        ang = math.radians(k * 30)
        r1 = r - (7 if k % 3 == 0 else 4)
        ticks.append(f"M{n(cx+math.sin(ang)*r1)} {n(cy-math.cos(ang)*r1)}L{n(cx+math.sin(ang)*(r-1.5))} {n(cy-math.cos(ang)*(r-1.5))}")
    a(f'<path d="{"".join(ticks)}" stroke="#e9ecef" stroke-width="1.6"/>')
    hour, minute = math.radians((11 + 58 / 60) * 30), math.radians(58 * 6)
    a(f'<g stroke="#ffffff" stroke-linecap="round" filter="url(#glow)">'
      f'<path d="M{n(cx)} {n(cy)}L{n(cx+math.sin(hour)*17)} {n(cy-math.cos(hour)*17)}" stroke-width="3"/>'
      f'<path d="M{n(cx)} {n(cy)}L{n(cx+math.sin(minute)*26)} {n(cy-math.cos(minute)*26)}" stroke-width="1.8"/></g>')
    a(f'<circle cx="{n(cx)}" cy="{cy}" r="2.4" fill="#fff"/>')
    mx, my, mw, mh = x - 22, 560, w + 44, 44
    a(f'<rect x="{mx}" y="{my}" width="{mw}" height="{mh}" fill="#060608" stroke="#e9ecef" stroke-opacity=".35"/>')
    for i, bx in enumerate(range(mx + 6, mx + mw - 3, 9)):
        cls = "q1" if i % 2 else "q2"
        a(f'<circle class="{cls}" cx="{bx}" cy="{my+4}" r="1.6" fill="#eef1f4"/><circle class="{cls}" cx="{bx}" cy="{my+mh-4}" r="1.6" fill="#eef1f4"/>')
    a(f'<g fill="#eef1f4" font-family="{MONO}" text-anchor="middle" filter="url(#glow)">'
      f'<text x="{n(mx+mw/2)}" y="{my+21}" font-size="12" font-weight="700">CINE IPÊ</text>'
      f'<text x="{n(mx+mw/2)}" y="{my+34}" font-size="8.5" fill="#aeb2b8">HOJE · SESSÃO 23:58</text></g>')


def street_lamp(x):
    a(f'<path d="M{x} 920V842h-14" stroke="#16171a" stroke-width="2.4" fill="none"/>')
    a(f'<rect x="{x-20}" y="840" width="10" height="3" fill="#eef1f4" filter="url(#glow)"/>')
    a(f'<path d="M{x-15} 843L{x-40} 920H{x+10}Z" fill="url(#cone)" opacity=".8"/>')
    a(f'<rect x="{x+2}" y="882" width="11" height="15" fill="#1b1c20" stroke="#3b3e44"/><rect x="{x+2}" y="882" width="11" height="2" fill="#3b3e44"/>')


def propeller_plane():
    """An old propeller plane crossing the smog, the other way from the helicopter."""
    a('<g><animateTransform attributeName="transform" type="translate" from="-160 95" to="1760 95" dur="130s" repeatCount="indefinite"/>')
    a('<g fill="#0e0f12" stroke="#3b3e44" stroke-width=".8">')
    a('<path d="M-20 0Q-8 -4 14 -2.5L20 0L14 2.5Q-8 4 -20 0Z"/>')
    a('<path d="M-17 -1L-23 -10L-19 -10L-12 -1.5Z"/><path d="M-4 1.5L9 1.5L5 6L-7 6Z"/><path d="M2 -2.5Q5 -6 9 -3Z"/></g>')
    a('<ellipse cx="21" cy="0" rx="1.2" ry="6.5" fill="#a0a6b0" opacity=".25"/>')
    a('<circle class="b" cx="-22" cy="-9" r="1.4" fill="#dc5a50" filter="url(#glow)"/>')
    a('<rect class="s" x="-1" y="5" width="2" height="2" fill="#fff" filter="url(#glow)"/></g>')


IPE = {
    "yellow": ("#cfa93f", "#e8c868"),
    "pink": ("#b25d8c", "#d98ab4"),
    "white": ("#cdd2d8", "#f2f4f6"),
}


def congress(cx):
    """National Congress: twin towers joined by their bridge, the Senate dome
    and the Chamber's bowl on the long platform, just above the rail deck."""
    base = 688
    a(f'<rect x="{cx-125}" y="{base}" width="250" height="12" fill="#0d0e10"/>')
    a(f'<rect x="{cx-125}" y="{base}" width="250" height="1" fill="#c8ced6" opacity=".18"/>')
    for tx in (cx - 19, cx + 3):
        a(f'<rect x="{tx}" y="350" width="16" height="{base-350}" fill="#111215"/>')
        a(f'<rect x="{tx}" y="350" width="1" height="{base-350}" fill="#c8ced6" opacity=".14"/>')
        stripes = "".join(f"M{tx+2} {y}h12" for y in range(356, base - 4, 6) if R.random() < .55)
        a(f'<path d="{stripes}" stroke="#aeb2b8" stroke-opacity=".3" stroke-width="1.2"/>')
    a(f'<rect x="{cx-3}" y="468" width="6" height="16" fill="#111215"/>')
    a(f'<rect x="{cx-3}" y="472" width="6" height="2" fill="#e9ecef" opacity=".6" filter="url(#glow)"/>')
    a(f'<path d="M{cx-112} {base}A32 19 0 0 1 {cx-48} {base}Z" fill="#121316" stroke="#c8ced6" stroke-opacity=".22"/>')
    a(f'<path d="M{cx+38} {base-17}Q{cx+78} {base+12} {cx+118} {base-17}Z" fill="#121316" stroke="#c8ced6" stroke-opacity=".22"/>')
    a(f'<rect x="{cx+76}" y="{base-6}" width="4" height="6" fill="#121316"/>')


def cathedral(cx):
    """Cathedral of Brasília: sixteen curved ribs pinched at the waist."""
    base, waist, top = 690, 640, 598
    ribs = []
    for k in range(-7, 8, 2):
        bx, wx, tx = cx + k * 4.6, cx + k * 1.6, cx + k * 3.4
        ribs.append(f"M{n(bx)} {base}Q{n(wx)} {waist} {n(tx)} {top}")
    d = "".join(ribs)
    a(f'<path d="{d}" stroke="#1a1b1f" stroke-width="5" fill="none" stroke-linecap="round"/>')
    a(f'<path d="{d}" stroke="#c8ced6" stroke-opacity=".28" stroke-width="1.1" fill="none"/>')
    a(f'<path d="M{cx} {top-4}V{top-22}M{cx-5} {top-15}H{cx+5}" stroke="#aeb2b8" stroke-opacity=".5" stroke-width="1.2"/>')


def ipe_tree(x, ground, scale, kind):
    """An ipê in bloom: bare twisted branches under a flat crown of flowers,
    a carpet of fallen petals, and a few petals drifting down with the rain."""
    base, light = IPE[kind]
    h = 96 * scale
    cy = ground - h
    trunk = (f"M{n(x-3*scale)} {ground}C{n(x-6*scale)} {n(ground-h*.4)} {n(x+5*scale)} {n(ground-h*.6)} {n(x)} {n(cy+14*scale)}"
             f"L{n(x+4*scale)} {n(cy+14*scale)}C{n(x+10*scale)} {n(ground-h*.6)} {n(x+1*scale)} {n(ground-h*.4)} {n(x+4*scale)} {ground}Z")
    a(f'<path d="{trunk}" fill="#121316"/>')
    limbs = []
    for k in (-1, -.45, .35, .9):
        ex, ey = x + k * 46 * scale, cy + R.uniform(-4, 10) * scale
        limbs.append(f"M{n(x+1)} {n(ground-h*.55)}Q{n(x+k*18*scale)} {n(ground-h*.75)} {n(ex)} {n(ey)}")
    a(f'<path d="{"".join(limbs)}" stroke="#121316" stroke-width="{n(2.4*scale)}" fill="none" stroke-linecap="round"/>')
    groups = {(base, ".6"): [], (base, ".92"): [], (light, ".85"): []}
    keys = list(groups)
    for _ in range(150):
        while True:
            u, v = R.uniform(-1, 1), R.uniform(-1, 1)
            if u * u + v * v <= 1:
                break
        bx, by = x + u * 62 * scale, cy + v * 30 * scale - (1 - u * u) * 8 * scale
        r = R.uniform(2, 4.4) * scale
        key = keys[2] if R.random() < .35 else keys[R.randrange(2)]
        groups[key].append(f'<circle cx="{n(bx)}" cy="{n(by)}" r="{n(r)}"/>')
    a('<g filter="url(#bloom)">' + "".join(
        f'<g fill="{col}" opacity="{op}">' + "".join(items) + '</g>' for (col, op), items in groups.items()) + '</g>')
    carpet = "".join(f"M{n(x+R.uniform(-70,70)*scale)} {n(ground+R.uniform(-3,6))}h{n(R.uniform(2,5))}" for _ in range(40))
    a(f'<path d="{carpet}" stroke="{base}" stroke-opacity=".45" stroke-width="2" stroke-linecap="round"/>')
    for i in range(6):
        px, py = x + R.uniform(-55, 55) * scale, cy + R.uniform(0, 20)
        fall, dur, sway = ground - py, R.uniform(6, 11), R.uniform(6, 16)
        a(f'<ellipse cx="{n(px)}" cy="{n(py)}" rx="2" ry="1.2" fill="{light}" opacity="0">'
          f'<animateTransform attributeName="transform" type="translate" values="0 0;{n(sway)} {n(fall*.33)};{n(-sway*.6)} {n(fall*.66)};{n(sway*.4)} {n(fall)}" dur="{n(dur)}s" begin="-{n(R.uniform(0, dur))}s" repeatCount="indefinite"/>'
          f'<animate attributeName="opacity" values="0;.9;.9;0" dur="{n(dur)}s" begin="-{n(R.uniform(0, dur))}s" repeatCount="indefinite"/></ellipse>')


def oryon_constellation():
    """Easter egg: Orion breaking through the smog over the left edge, signed ORYON."""
    stars = {
        "betelgeuse": (60, 42, 2.4, "#e8c868"), "bellatrix": (150, 56, 1.9, "#e9ecef"),
        "meissa": (104, 18, 1.4, "#e9ecef"), "alnitak": (88, 112, 1.9, "#e9ecef"),
        "alnilam": (105, 105, 2.0, "#e9ecef"), "mintaka": (122, 98, 1.8, "#e9ecef"),
        "saiph": (76, 182, 1.8, "#e9ecef"), "rigel": (160, 172, 2.4, "#cdd8e6"),
    }
    links = [("betelgeuse", "meissa"), ("meissa", "bellatrix"), ("betelgeuse", "alnitak"),
             ("bellatrix", "mintaka"), ("alnitak", "alnilam"), ("alnilam", "mintaka"),
             ("alnitak", "saiph"), ("mintaka", "rigel")]
    d = "".join(f"M{stars[a_][0]} {stars[a_][1]}L{stars[b][0]} {stars[b][1]}" for a_, b in links)
    # Shifted down so wide windows, which crop the top of the sky, still show Meissa.
    a('<g transform="translate(0 32)">')
    a(f'<path d="{d}" stroke="#aeb2b8" stroke-opacity=".2" stroke-width=".8" stroke-dasharray="2 3" fill="none"/>')
    for i, (x, y, r, col) in enumerate(stars.values()):
        a(f'<circle class="tw" cx="{x}" cy="{y}" r="{r}" fill="{col}" filter="url(#glow)" style="animation-delay:-{n(i * .45)}s"/>')
    a(f'<text x="176" y="112" font-family="{MONO}" font-size="9" letter-spacing="5" fill="#959aa1" opacity=".75">ORYON</text>')
    a('</g>')

a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {VH}" preserveAspectRatio="xMidYMax slice">')
a("<style>/*A*/"
  ".b{animation:bk 1.5s steps(1) infinite}@keyframes bk{50%{opacity:0}}"
  ".fl{animation:fl 9s steps(1) infinite}.fb{animation:fl 2.3s steps(1) infinite}"
  "@keyframes fl{0%,100%{opacity:1}2%{opacity:.15}4%{opacity:1}6%{opacity:.3}8%{opacity:1}}"
  ".s{animation:st 1.3s steps(1) infinite}@keyframes st{0%{opacity:1}12%{opacity:0}}"
  ".v{animation:vz 4s ease-in-out infinite}@keyframes vz{0%,100%{opacity:.7}50%{opacity:1}}"
  ".q1,.q2{animation:q 1.2s steps(1) infinite}.q2{animation-delay:-.6s}@keyframes q{50%{opacity:.15}}"
  ".tw{animation:tw 3.4s ease-in-out infinite}@keyframes tw{50%{opacity:.35}}"
  "</style>")
a("<defs>")
a('<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#030304"/><stop offset=".55" stop-color="#0d0e11"/><stop offset=".76" stop-color="#202226"/><stop offset="1" stop-color="#0c0d0f"/></linearGradient>')
a('<radialGradient id="fog"><stop offset="0" stop-color="#bec4cc" stop-opacity=".5"/><stop offset="1" stop-color="#bec4cc" stop-opacity="0"/></radialGradient>')
a('<radialGradient id="vig" cx=".5" cy=".62" r=".75"><stop offset=".45" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".72"/></radialGradient>')
a('<linearGradient id="beam" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#e9ecef" stop-opacity=".25"/><stop offset="1" stop-color="#e9ecef" stop-opacity="0"/></linearGradient>')
a('<linearGradient id="cone" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#c8ced6" stop-opacity=".16"/><stop offset="1" stop-color="#c8ced6" stop-opacity="0"/></linearGradient>')
a('<linearGradient id="refl" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e9ecef" stop-opacity=".08"/><stop offset="1" stop-color="#e9ecef" stop-opacity="0"/></linearGradient>')
a('<filter id="bloom" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation=".8" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
a('<filter id="glow" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="2.6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
a('<pattern id="scan" width="4" height="3" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#000" opacity=".28"/></pattern>')
for li, cfg in enumerate(LAYERS):
    window_patterns(f"w{li}", cfg, (.1, .18, .28))
for pid, count, lo, hi in (("rn", 34, 14, 30), ("rf", 46, 8, 16)):
    a(f'<pattern id="{pid}" width="240" height="240" patternUnits="userSpaceOnUse">')
    d = []
    for _ in range(count):
        x, y, ln = R.uniform(0, 240), R.uniform(0, 240), R.uniform(lo, hi)
        d.append(f"M{n(x)} {n(y)}l{n(ln*.12)} {n(-ln)}")
    width, op = ("1.1", ".2") if pid == "rn" else (".8", ".1")
    a(f'<path d="{"".join(d)}" stroke="#c8ced6" stroke-opacity="{op}" stroke-width="{width}" stroke-linecap="round"/>')
    a("</pattern>")
a('<clipPath id="bb"><rect x="1310" y="205" width="136" height="80"/></clipPath>')
a("</defs>")

a(f'<rect width="{W}" height="{VH}" fill="url(#sky)"/>')
for ex in (640, 960):
    a(f'<ellipse cx="{ex}" cy="{TOP_PAD+70}" rx="150" ry="24" fill="url(#fog)" opacity=".09"/>')
a(f'<g transform="translate(0 {TOP_PAD})">')
oryon_constellation()

for li, cfg in enumerate(LAYERS):
    a("<g>")
    if li == 0:
        for k in (.12, .44, .8):
            mast(W * k + R.random() * 40, lerp(60, 130, R.random()))
    x = -R.random() * 20
    while x < W:
        bw = lerp(*cfg["w"], R.random())
        building(x, lerp(*cfg["top"], R.random()), bw, cfg, li, f"w{li}")
        x += bw + R.random() * cfg["gap"]
    if li == 1:
        a(f'<rect x="1303" y="140" width="150" height="{H-140}" fill="{cfg["body"]}"/>')
        a('<rect x="1310" y="205" width="136" height="80" fill="#08090b" stroke="#e9ecef" stroke-opacity=".25"/>')
        a(f'<g clip-path="url(#bb)"><g filter="url(#glow)" fill="#e9ecef" font-family="{MONO}" font-size="26" font-weight="600">')
        a('<text x="1316" y="243">__BB__'
          '<animateTransform attributeName="transform" type="translate" from="0 0" to="-__BBW__ 0" dur="__BBD__s" repeatCount="indefinite"/></text>')
        a(f'</g><text x="1316" y="273" fill="#aeb2b8" font-family="{MONO}" font-size="11">L22 CINZA</text>')
        a('<rect x="1310" y="205" width="136" height="80" fill="url(#scan)"/></g>')
        eye_sign()
    if li == 2:
        congress(560)
        cathedral(930)
        clock_tower()
    for i, s in enumerate(signs):
        if s["layer"] == li and not (li == 2 and s["x"] < 370 and s["x"] + s["w"] > 200):
            sign_svg(s, R.uniform(0, 9), R.random() < .2)
    for bx, by, r in beacons:
        a(f'<circle class="b" cx="{n(bx)}" cy="{n(by)}" r="{r}" fill="#dc5a50" filter="url(#glow)" style="animation-delay:-{n(R.uniform(0,1.5))}s"/>')
    beacons.clear()
    a("</g>")

# Edge buildings in the nearest city layer's tone, so the sides blend with
# the skyline instead of framing it in a darker block.
a("<g>")
building(-10, 330, 205, LAYERS[2], 3, "w2")
building(1405, 360, 215, LAYERS[2], 3, "w2")
signs.append(dict(layer=3, text="HOTEL", vertical=True, x=150, y=410, w=27, h=5 * 15.6 * 1.3 + 8, cs=15.6))
signs.append(dict(layer=3, text="ラーメン", vertical=True, x=1548, y=440, w=27, h=4 * 15.6 * 1.3 + 8, cs=15.6))
for s in signs[-2:]:
    sign_svg(s, R.uniform(0, 9), s["text"] != "HOTEL")
for bx, by, r in beacons:
    a(f'<circle class="b" cx="{n(bx)}" cy="{n(by)}" r="{r}" fill="#dc5a50" filter="url(#glow)"/>')
beacons.clear()
a("</g>")

for fx, fy, fw, fh, dur in ((300, 560, 900, 160, 70), (1200, 640, 1000, 200, 90)):
    a(f'<ellipse cx="{fx}" cy="{fy}" rx="{fw/2}" ry="{fh/2}" fill="url(#fog)" opacity=".35">'
      f'<animateTransform attributeName="transform" type="translate" values="-160 0;160 0;-160 0" dur="{dur}s" repeatCount="indefinite"/></ellipse>')

a('<g><animateTransform attributeName="transform" type="translate" from="1700 175" to="-120 175" dur="80s" repeatCount="indefinite"/>')
a('<path d="M0 4L-70 900H70Z" fill="url(#cone)" style="mix-blend-mode:screen"><animateTransform attributeName="transform" type="rotate" values="-16;16;-16" dur="11s" repeatCount="indefinite"/></path>')
a('<ellipse rx="10" ry="4" fill="#0d0e10"/><rect x="6" y="-1" width="15" height="1.8" fill="#0d0e10"/><rect x="-14" y="-6" width="28" height="1" fill="#a0a6b0" opacity=".4"/>')
a('<rect class="s" x="-1" y="3" width="2.4" height="2.4" fill="#fff" filter="url(#glow)"/></g>')
propeller_plane()

a(f'<rect y="735" width="{W}" height="{H-735}" fill="#040405" opacity=".93"/>')
px = R.uniform(0, 150)
while px < W:
    a(f'<rect x="{n(px-8)}" y="735" width="34" height="7" fill="#0c0d0f"/><rect x="{n(px)}" y="735" width="18" height="185" fill="#0c0d0f"/><rect x="{n(px)}" y="742" width="1" height="178" fill="#c8ced6" opacity=".07"/>')
    px += 150
a(f'<rect y="700" width="{W}" height="35" fill="#101114"/><rect y="700" width="{W}" height="1" fill="#d2d7de" opacity=".2"/><rect y="694" width="{W}" height="1" fill="#a0a6b0" opacity=".14"/>')
lamps = []
lx = 30
while lx < W:
    a(f'<path d="M{lx} 694V674h9" stroke="#16171a" stroke-width="1.6" fill="none"/>')
    lamps.append(lx + 9)
    lx += 96
a('<g fill="#eef1f4" filter="url(#glow)">' + "".join(f'<rect x="{x-2}" y="673" width="5" height="2"/>' for x in lamps) + "</g>")

a('<g><animateTransform attributeName="transform" type="translate" from="-700 0" to="2400 0" dur="18s" repeatCount="indefinite"/>')
th, car = 20, 110
a(f'<path d="M{5*car} {674+11}L{5*car+170} {674+2}V{674+22}Z" fill="url(#beam)"/>')
for i in range(5):
    x = i * car
    if i == 4:
        a(f'<path d="M{x} 674H{x+car-24}L{x+car} 694H{x}Z" fill="#1b1c20"/>')
        ww = car - 32
    else:
        a(f'<rect x="{x}" y="674" width="{car-3}" height="{th}" fill="#1b1c20"/>')
        ww = car - 9
    a(f'<rect x="{x+4}" y="680" width="{ww}" height="6" fill="#e9ecef" opacity=".85" filter="url(#glow)"/>')
    if i == 4:
        a(f'<text x="{x+6}" y="692.5" font-family="{MONO}" font-size="5.5" letter-spacing="1.2" fill="#e8c868" filter="url(#glow)">L22 · ORYON</text>')
    a(f'<rect x="{x}" y="674" width="{car-3}" height="1" fill="#d2d7de" opacity=".25"/>')
a("</g>")

a(f'<rect y="920" width="{W}" height="{H-920}" fill="#070809"/><rect y="920" width="{W}" height="1" fill="#c8ced6" opacity=".08"/>')
street_lamp(1238)


for tx, kind, size in ((70, "yellow", 1.15), (330, "pink", 1.0), (1150, "white", 1.05), (1520, "yellow", 1.2)):
    ipe_tree(tx, 962, size, kind)

for s in signs:
    if s["layer"] >= 2:
        cx = s["x"] + s["w"] / 2
        a(f'<rect x="{n(cx-s["w"]*.3)}" y="924" width="{n(s["w"]*.6)}" height="76" fill="url(#refl)"/>')

a("</g>")
for pid, dur in (("rf", ".75"), ("rn", ".42")):
    a(f'<rect x="-240" y="-240" width="{W+480}" height="{VH+480}" fill="url(#{pid})">'
      f'<animateTransform attributeName="transform" type="translate" from="0 0" to="0 240" dur="{dur}s" repeatCount="indefinite"/></rect>')
a(f'<rect width="{W}" height="{VH}" fill="url(#scan)" opacity=".6"/>')
a(f'<rect width="{W}" height="{VH}" fill="url(#vig)"/>')
a("</svg>")

svg = "".join(out)
assert "`" not in svg and "${" not in svg and "\\" not in svg
sys.stdout.write("// Generated by scripts/gen_scene.py (seed 2087). Regenerate, don't edit.\nexport const SCENE = `" + svg + "`\n")
