"""
mode_k2.py  —  Wandering in the Woods  (Grades K-2)
CS251 Project — Lewis University
"""

import pygame, sys, random, math, threading

try:
    import numpy as np
    NUMPY_OK = True
except ImportError:
    NUMPY_OK = False

# ── colours ───────────────────────────────────────────────────────────────────
WHITE    = (255, 255, 255)
BLACK    = (20,  20,  20)
# warm sunset sky — much friendlier for kids than cold blue
SKY_T    = (250, 130,  60)   # deep warm orange at top
SKY_B    = (255, 210, 130)   # soft gold at horizon
SKY_T2   = (35,  15,  75)    # night purple top
SKY_B2   = (90,  45, 140)    # night purple bottom
GD       = (34,  85,  34)
GM       = (60,  140, 60)
GL       = (180, 230, 140)
BROWN    = (110,  70,  30)
YELLOW   = (255, 235,  60)
ORANGE   = (255, 145,  10)
RED      = (225,  55,  55)
BLUE     = (55,  110, 230)
GOLD     = (255, 200,   0)
PURPLE   = (150,  65, 215)
CREAM    = (255, 250, 230)   # warm cream for panel
TEAL     = (0,   185, 165)
LIME     = (130, 225,  55)
PINK     = (255, 110, 170)
GRAY     = (150, 150, 150)
DKGRAY   = (65,   65,  65)
PANEL_BORDER = (200, 130,  50)   # warm amber border on panel

TRAIL_A  = (255,  90,  90, 145)
TRAIL_B  = (70,  115, 255, 145)
BALLOONS = [(255,70,70),(70,160,255),(255,210,40),(80,210,100),(210,80,220)]
HEAT     = [GL,(230,240,80),(255,210,40),(255,140,30),(220,40,40)]

# ── layout ────────────────────────────────────────────────────────────────────
W, H      = 900, 600
GRID_N    = 6
CELL      = 76
ML        = 48
MT        = 88
GRID_W    = GRID_N * CELL
PX        = ML + GRID_W + 18
PW        = W - PX - 10
FPS       = 60
MAX_STATS = 20
MAX_STEPS = 2000

SPEEDS      = [900, 550, 320, 150, 55]
SPEED_NAMES = ["Very Slow", "Slow", "Normal", "Fast", "Very Fast"]

FUN_FACTS = [
    "Random walks were studied by\nAlbert Einstein in 1905! 🧠",
    "A 6x6 grid has 36 squares.\nHow many did they visit? 🔢",
    "Randomness means no pattern —\nthat is why it is unpredictable! 🎲",
    "Scientists use random walks to\nmodel how gases spread! ⚗️",
    "On a 6x6 grid, walkers meet\nin about 20-50 steps on average! 📊",
    "Random walks are used in biology\nto model how animals find food! 🐾",
    "The more squares they visit,\nthe better the exploration! 🗺️",
    "Can you guess the steps correctly?\nTry a few rounds to get better! 🎯",
]

MOOD_ICONS = {"love":"😍","happy":"😊","neutral":"😐","worried":"😟","crying":"😭"}

# ── 2 characters kids can choose from ────────────────────────────────────────
# (display_name, body_col, head_col, badge_label, trail_col)
CHAR_OPTIONS = [
    ("🐱 Cat",  (210, 140,  55), (240, 185, 110), "CAT",  (230,  70,  30, 170)),
    ("🐶 Dog",  ( 60, 130, 210), ( 90, 165, 240), "DOG",  ( 30,  90, 230, 170)),
]
# kids always pick from exactly these 2 — Cat = player 1, Dog = player 2

# ═══════════════════════════════════════════════════════════════════════════════
# SAFE SOUND UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def safe_speak(text):
    def _go():
        try:
            import pyttsx3
            e = pyttsx3.init()
            e.setProperty("rate", 160)
            e.say(text)
            e.runAndWait()
            e.stop()
        except Exception:
            pass
    try:
        threading.Thread(target=_go, daemon=True).start()
    except Exception:
        pass

_mixer_ready = False
def _ensure_mixer():
    global _mixer_ready
    if not _mixer_ready:
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            _mixer_ready = True
        except Exception:
            pass

def _sine(freq, ms, vol=0.18):
    try:
        _ensure_mixer()
        if not NUMPY_OK or not pygame.mixer.get_init():
            return None
        n    = int(44100 * ms / 1000)
        t    = np.linspace(0, ms/1000, n, False)
        w    = np.sin(2 * np.pi * freq * t)
        fade = min(int(n * 0.15), 500)
        w[:fade]  *= np.linspace(0, 1, fade)
        w[-fade:] *= np.linspace(1, 0, fade)
        s = (w * vol * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(np.column_stack([s, s]))
    except Exception:
        return None

def _play(snd):
    try:
        if snd: snd.play()
    except Exception:
        pass

def sfx_step():
    _play(_sine(300, 55, 0.07))

def sfx_start():
    _play(_sine(440, 110, 0.20))
    try:
        pygame.time.delay(120)
        _play(_sine(550, 110, 0.20))
    except Exception:
        pass

def sfx_celebrate():
    for f, d in [(523,0),(659,120),(784,240),(1047,360)]:
        try:
            if d: pygame.time.delay(d)
            _play(_sine(f, 190, 0.28))
        except Exception:
            pass

# ═══════════════════════════════════════════════════════════════════════════════
# CONFETTI
# ═══════════════════════════════════════════════════════════════════════════════

def make_confetti(cx, cy, n=70):
    return [{
        "x":  cx + random.randint(-40, 40),
        "y":  cy + random.randint(-20, 20),
        "vx": random.uniform(-3.5, 3.5),
        "vy": random.uniform(-5.5, -1.0),
        "col": random.choice([RED,BLUE,GOLD,LIME,PINK,ORANGE,PURPLE,WHITE]),
        "size": random.randint(4, 10),
        "shape": random.choice(["rect","circle","diamond"]),
        "life": 1.0,
    } for _ in range(n)]

def tick_confetti(ps):
    out = []
    for p in ps:
        p["x"]  += p["vx"]
        p["y"]  += p["vy"]
        p["vy"] += 0.14
        p["vx"] *= 0.985
        p["life"] -= 0.008
        if p["life"] > 0 and p["y"] < H + 30:
            out.append(p)
    return out

def draw_confetti(surf, ps):
    for p in ps:
        try:
            x, y = int(p["x"]), int(p["y"])
            s    = max(2, int(p["size"] * p["life"]))
            col  = p["col"]
            if p["shape"] == "circle":
                pygame.draw.circle(surf, col, (x,y), s//2)
            elif p["shape"] == "diamond":
                pygame.draw.polygon(surf, col, [(x,y-s),(x+s,y),(x,y+s),(x-s,y)])
            else:
                pygame.draw.rect(surf, col, (x-s//2,y-s//2,s,s), border_radius=1)
        except Exception:
            pass

# ═══════════════════════════════════════════════════════════════════════════════
# FONTS  — bold + friendly
# ═══════════════════════════════════════════════════════════════════════════════

def _fonts():
    def _f(size, bold=False):
        for name in ["Arial Rounded MT Bold", "Verdana", "comicsansms"]:
            try:
                return pygame.font.SysFont(name, size, bold=bold)
            except Exception:
                pass
        return pygame.font.SysFont("comicsansms", size, bold=bold)
    return {
        "title": _f(25, True),
        "big"  : _f(27, True),
        "med"  : _f(20, True),
        "sm"   : _f(17),
        "tiny" : _f(15),
        "micro": _f(13),
    }

# ═══════════════════════════════════════════════════════════════════════════════
# DRAWING HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def cell_rect(c, r):
    return pygame.Rect(ML + c*CELL, MT + r*CELL, CELL, CELL)

def manhattan(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])

def heat_col(v):
    if v == 0: return HEAT[0]
    if v <= 2: return HEAT[1]
    if v <= 4: return HEAT[2]
    if v <= 7: return HEAT[3]
    return HEAT[4]

def get_mood(steps, met):
    if met:        return "love",    GOLD
    if steps < 20: return "happy",   LIME
    if steps < 40: return "neutral", YELLOW
    if steps < 60: return "worried", ORANGE
    return             "crying",     RED

def rstep(c, r):
    dirs = [(dc,dr) for dc,dr in [(-1,0),(1,0),(0,-1),(0,1)]
            if 0 <= c+dc < GRID_N and 0 <= r+dr < GRID_N]
    d = random.choice(dirs) if dirs else (0,0)
    return c+d[0], r+d[1]

def draw_bg(surf, stars, night):
    try:
        t1, t2 = (SKY_T2, SKY_B2) if night else (SKY_T, SKY_B)
        for y in range(H - 70):
            ratio = y / max(H-70, 1)
            c = tuple(int(t1[i]+(t2[i]-t1[i])*ratio) for i in range(3))
            pygame.draw.line(surf, c, (0,y), (W,y))
        for sx,sy,sr in stars:
            pygame.draw.circle(surf, (255,255,210), (sx,sy), sr)
        if night:
            pygame.draw.circle(surf, (245,245,180), (820,55), 28)
            pygame.draw.circle(surf, SKY_T2,        (832,48), 22)
        pygame.draw.rect(surf, GD, (0,H-70,W,70))
        pygame.draw.rect(surf, GM, (0,H-70,W,18))
    except Exception:
        surf.fill((220,160,80))

def draw_tree(surf, x, y, s=34):
    try:
        pygame.draw.rect(surf, BROWN,  (x-s//8, y, s//4, s//3))
        pygame.draw.polygon(surf, GM,  [(x,y-s),(x-s//2,y),(x+s//2,y)])
        pygame.draw.polygon(surf, GD,  [(x,y-int(s*1.45)),(x-s//3,y-s//2),(x+s//3,y-s//2)])
    except Exception:
        pass

def draw_grid(surf, hmap, show_heat, closest=None):
    try:
        for r in range(GRID_N):
            for c in range(GRID_N):
                col = heat_col(hmap[r][c]) if show_heat else (GL if (r+c)%2==0 else GM)
                pygame.draw.rect(surf, col, cell_rect(c,r))
                pygame.draw.rect(surf, GD,  cell_rect(c,r), 2)
        if closest:
            rc = cell_rect(*closest)
            pygame.draw.rect(surf, GOLD,   rc, 5)
            pygame.draw.rect(surf, ORANGE, rc.inflate(-4,-4), 2)
    except Exception:
        pass

def draw_footprint(surf, c, r, col, flip=False):
    """Draw two footprints in a cell. flip=True mirrors left/right for player 2."""
    try:
        rc = cell_rect(c, r)
        cx, cy = rc.centerx, rc.centery
        ox = 3 if not flip else -3   # slight offset so P1 and P2 prints differ
        # left foot
        pygame.draw.ellipse(surf, col, (cx-11+ox, cy-4, 9, 14))
        # right foot  
        pygame.draw.ellipse(surf, col, (cx+2+ox,  cy-4, 9, 14))
        # toes on left foot
        for tx in range(3):
            pygame.draw.circle(surf, col, (cx-10+ox+tx*3, cy-6), 2)
        # toes on right foot
        for tx in range(3):
            pygame.draw.circle(surf, col, (cx+3+ox+tx*3,  cy-6), 2)
    except Exception:
        pass

def draw_trail(surf, trail, col, fp_mode, flip=False):
    try:
        ts     = pygame.Surface((W, H), pygame.SRCALPHA)
        capped = trail[-180:]
        for idx, (c, r) in enumerate(capped):
            alpha = min(255, int(60 + 100*(idx/max(len(capped),1))))
            if fp_mode:
                # draw footprints on every other cell so they don't overlap
                if idx % 2 == 0:
                    draw_footprint(ts, c, r, col[:3]+(alpha,), flip)
            else:
                pygame.draw.ellipse(ts, col[:3]+(alpha,),
                                    cell_rect(c,r).inflate(-18,-18))
        surf.blit(ts, (0,0))
    except Exception:
        pass

def draw_char(surf, c, r, char_idx, mood, fonts, bounce=0):
    """Draw character using CHAR_OPTIONS style with mood face."""
    try:
        _, body_col, head_col, label, _ = CHAR_OPTIONS[char_idx]
        rc = cell_rect(c,r)
        cx = rc.centerx
        cy = rc.centery + int(math.sin(bounce)*3)

        # shadow
        shad = pygame.Surface((38,10), pygame.SRCALPHA)
        pygame.draw.ellipse(shad, (0,0,0,55), (0,0,38,10))
        surf.blit(shad, (cx-19, rc.centery+26))

        # body + head
        pygame.draw.circle(surf, body_col, (cx,cy+10), 19)
        pygame.draw.circle(surf, head_col, (cx,cy-11), 16)
        pygame.draw.circle(surf, tuple(max(0,v-40) for v in head_col),(cx,cy-11),16,2)

        # eyes
        if mood == "love":
            for ex in [cx-5, cx+5]:
                pygame.draw.circle(surf, RED, (ex-1,cy-14), 3)
                pygame.draw.circle(surf, RED, (ex+1,cy-14), 3)
                pygame.draw.polygon(surf, RED, [(ex-3,cy-13),(ex+3,cy-13),(ex,cy-10)])
        elif mood == "crying":
            for ex in [cx-5, cx+5]:
                pygame.draw.circle(surf, WHITE, (ex,cy-13), 4)
                pygame.draw.line(surf, BLACK, (ex-2,cy-15),(ex+2,cy-11), 2)
                pygame.draw.line(surf, BLACK, (ex+2,cy-15),(ex-2,cy-11), 2)
            pygame.draw.ellipse(surf, (100,160,255),(cx-9,cy-6,4,7))
            pygame.draw.ellipse(surf, (100,160,255),(cx+5,cy-6,4,7))
        elif mood == "worried":
            for ex in [cx-5, cx+5]:
                pygame.draw.circle(surf, WHITE, (ex,cy-13), 4)
                pygame.draw.circle(surf, BLACK, (ex,cy-13), 2)
            pygame.draw.line(surf, BLACK, (cx-8,cy-19),(cx-3,cy-17), 2)
            pygame.draw.line(surf, BLACK, (cx+8,cy-19),(cx+3,cy-17), 2)
        else:
            for ex in [cx-5, cx+5]:
                pygame.draw.circle(surf, WHITE, (ex,cy-13), 4)
                pygame.draw.circle(surf, BLACK, (ex,cy-13), 2)
                pygame.draw.circle(surf, WHITE, (ex+1,cy-14), 1)

        # mouth
        if mood == "love":
            pygame.draw.arc(surf, RED,   pygame.Rect(cx-7,cy-8,14,10), math.pi,2*math.pi,3)
        elif mood == "happy":
            pygame.draw.arc(surf, BLACK, pygame.Rect(cx-6,cy-7,12,8),  math.pi,2*math.pi,2)
        elif mood == "neutral":
            pygame.draw.line(surf, BLACK, (cx-5,cy-4),(cx+5,cy-4), 2)
        else:
            pygame.draw.arc(surf, BLACK, pygame.Rect(cx-6,cy-3,12,8),  0,math.pi,2)

        # badge
        pygame.draw.circle(surf, body_col, (cx,cy+10), 11)
        lbl = fonts["tiny"].render(label[:4], True, WHITE)
        surf.blit(lbl, lbl.get_rect(center=(cx,cy+10)))
    except Exception:
        pass

def draw_balloons(surf, frame):
    try:
        for i,col in enumerate(BALLOONS):
            x = 65 + i*160
            y = 430 - (frame%160)*2 + i*14
            if y > -60:
                pygame.draw.ellipse(surf, col,   (x-20,y-30,40,50))
                pygame.draw.ellipse(surf, WHITE, (x-9, y-22, 9,12))
                for j in range(3):
                    pygame.draw.line(surf, BROWN,
                        (x+random.randint(-2,2),y+20+j*6),
                        (x+random.randint(-2,2),y+26+j*6), 1)
    except Exception:
        pass

def panel(surf, x, y, w, h):
    try:
        # main fill
        pygame.draw.rect(surf, (255, 252, 235), (x,y,w,h), border_radius=22)
        # top inner highlight strip — gives a candy-like sheen
        pygame.draw.rect(surf, (255, 255, 250),
                         pygame.Rect(x+6, y+6, w-12, h//3), border_radius=18)
        # border
        pygame.draw.rect(surf, PANEL_BORDER, (x,y,w,h), 4, border_radius=22)
    except Exception:
        pass

def btn(surf, fonts, rect, label, bg, fg=WHITE):
    try:
        # chunky drop shadow
        shadow = pygame.Rect(rect.x+3, rect.y+5, rect.w, rect.h)
        pygame.draw.rect(surf, tuple(max(0,c-70) for c in bg),
                         shadow, border_radius=16)
        # main pill shape
        pygame.draw.rect(surf, bg, rect, border_radius=16)
        # top shine strip
        shine_h = rect.h // 3
        shine = pygame.Rect(rect.x+6, rect.y+4, rect.w-12, shine_h)
        pygame.draw.rect(surf, tuple(min(255,c+55) for c in bg),
                         shine, border_radius=12)
        # label
        s = fonts["sm"].render(str(label), True, fg)
        surf.blit(s, s.get_rect(center=rect.center))
    except Exception:
        pass

def section_header(surf, fonts, text, col, y):
    """Draws a coloured pill-shaped section label."""
    try:
        s    = fonts["med"].render(text, True, WHITE)
        r    = s.get_rect()
        pill = pygame.Rect(PX+8, y, r.w+22, r.h+8)
        pygame.draw.rect(surf, col,                     pill, border_radius=12)
        pygame.draw.rect(surf, tuple(min(255,c+50) for c in col),
                         pill.inflate(-6,-4), 1, border_radius=10)
        surf.blit(s, (pill.x+11, pill.y+4))
        return pill.bottom + 6
    except Exception:
        return y + 28

def divline(surf, y):
    # dotted-style divider — more playful
    for dx in range(PX+10, PX+PW-20, 8):
        pygame.draw.circle(surf, PANEL_BORDER, (dx, y), 1)

def draw_bar_chart(surf, fonts, stats, x, y, w, h):
    try:
        if not stats: return
        recent = stats[-8:]
        mx     = max(recent) if max(recent) > 0 else 1
        bw     = (w-4) // len(recent)
        pygame.draw.rect(surf, (240,248,235), (x,y,w,h), border_radius=4)
        pygame.draw.rect(surf, GM,            (x,y,w,h), 1, border_radius=4)
        for i,val in enumerate(recent):
            bh  = max(2, int((h-14)*val/mx))
            bx  = x+2+i*bw
            by  = y+h-bh-4
            pygame.draw.rect(surf, (100,200,100),(bx+1,by,bw-2,bh), border_radius=2)
        s = fonts["micro"].render(f"Last {len(recent)} rounds", True, BROWN)
        surf.blit(s, (x+2, y+1))
    except Exception:
        pass

# ═══════════════════════════════════════════════════════════════════════════════
# CHARACTER PICK SCREEN  — kids tap one of 2 cartoon characters each
# ═══════════════════════════════════════════════════════════════════════════════

def char_pick_screen(screen, fonts, stars, trees, night):
    """
    Simple two-step pick:
      Step 1 — Player 1 clicks Cat or Dog
      Step 2 — Player 2 clicks the remaining one automatically
    Returns (idx_p1, idx_p2) where idx is 0=Cat or 1=Dog
    """
    clock  = pygame.time.Clock()
    picks  = [-1, -1]   # -1 = not yet chosen
    step   = 0          # 0=p1 picking, 1=p2 picking, 2=done

    # two big character cards centred on screen
    CARD_W, CARD_H = 210, 260
    card_rects = [
        pygame.Rect(W//2 - 240, 200, CARD_W, CARD_H),   # Cat card
        pygame.Rect(W//2 +  30, 200, CARD_W, CARD_H),   # Dog card
    ]
    GO = pygame.Rect(W//2 - 115, 490, 230, 46)

    while True:
        now = pygame.time.get_ticks()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return 0, 1
            if ev.type == pygame.MOUSEBUTTONDOWN:
                mx, my = ev.pos
                if step < 2:
                    for i, cr in enumerate(card_rects):
                        if cr.collidepoint(mx, my):
                            if step == 0:
                                picks[0] = i
                                picks[1] = 1 - i   # auto assign other to p2
                                step     = 2        # both picked instantly
                if step == 2 and GO.collidepoint(mx, my):
                    return picks[0], picks[1]
                # also allow clicking GO after auto-pick
                if step == 2 and GO.collidepoint(mx, my):
                    return picks[0], picks[1]

        # draw background
        draw_bg(screen, stars, night)
        for tx,ty in trees:
            draw_tree(screen, tx, ty, 34)

        # title card
        card_bg = pygame.Rect(W//2-270, 120, 540, 400)
        pygame.draw.rect(screen, CREAM,        card_bg, border_radius=22)
        pygame.draw.rect(screen, PANEL_BORDER, card_bg, 4, border_radius=22)

        # heading
        if step == 0:
            hdg = fonts["big"].render("🌲  Player 1 — pick your character!  🌲", True, BROWN)
        else:
            hdg = fonts["big"].render("🎉  Both players are ready!  🎉", True, GD)
        screen.blit(hdg, hdg.get_rect(center=(W//2, 153)))

        sub_text = "Tap a character to choose!" if step == 0 else "Click  Let's Go!  to start!"
        sub = fonts["sm"].render(sub_text, True, GRAY)
        screen.blit(sub, sub.get_rect(center=(W//2, 183)))

        # draw the two character cards
        for i, (cname, bcol, hcol, lbl, _) in enumerate(CHAR_OPTIONS):
            cr       = card_rects[i]
            is_p1    = (picks[0] == i)
            is_p2    = (picks[1] == i)
            chosen   = is_p1 or is_p2

            # card background + border
            bg_col  = (255,245,235) if is_p1 else ((235,245,255) if is_p2 else WHITE)
            bd_col  = ORANGE if is_p1 else (BLUE if is_p2 else GRAY)
            bd_w    = 4 if chosen else 2
            pygame.draw.rect(screen, bg_col, cr, border_radius=14)
            pygame.draw.rect(screen, bd_col, cr, bd_w, border_radius=14)

            # mini character drawing inside card
            cx2, cy2 = cr.centerx, cr.y + 110
            bounce2  = int(math.sin(now * 0.005 + i * 2) * 5) if chosen else 0
            # body
            pygame.draw.circle(screen, bcol, (cx2, cy2+bounce2+8),  26)
            # head
            pygame.draw.circle(screen, hcol, (cx2, cy2+bounce2-16), 22)
            pygame.draw.circle(screen, tuple(max(0,v-35) for v in hcol),
                               (cx2, cy2+bounce2-16), 22, 2)
            # happy eyes
            for ex in [cx2-7, cx2+7]:
                pygame.draw.circle(screen, WHITE, (ex, cy2+bounce2-19), 5)
                pygame.draw.circle(screen, BLACK, (ex, cy2+bounce2-19), 3)
                pygame.draw.circle(screen, WHITE, (ex+1, cy2+bounce2-20), 1)
            # smile
            pygame.draw.arc(screen, BLACK,
                pygame.Rect(cx2-8, cy2+bounce2-10, 16, 10), math.pi, 2*math.pi, 2)

            # character name
            nl = fonts["med"].render(cname, True, BROWN)
            screen.blit(nl, nl.get_rect(center=(cr.centerx, cr.y + 200)))

            # P1 / P2 badge
            if is_p1:
                b = fonts["sm"].render("P1", True, WHITE)
                br = b.get_rect(center=(cr.x+22, cr.y+22))
                pygame.draw.circle(screen, ORANGE, br.center, 16)
                screen.blit(b, br)
            if is_p2:
                b = fonts["sm"].render("P2", True, WHITE)
                br = b.get_rect(center=(cr.right-22, cr.y+22))
                pygame.draw.circle(screen, BLUE, br.center, 16)
                screen.blit(b, br)

            # hover glow when not yet picked
            if step == 0 and cr.collidepoint(pygame.mouse.get_pos()):
                ov = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
                pygame.draw.rect(ov, (255,200,100,40), (0,0,CARD_W,CARD_H), border_radius=14)
                screen.blit(ov, cr.topleft)

        # Let's Go button (only when both picked)
        if step == 2:
            btn(screen, fonts, GO, "🌲   Let's Go!   🌲", GD)

        pygame.display.flip()
        clock.tick(FPS)

# ═══════════════════════════════════════════════════════════════════════════════
# FUN FACT POPUP
# ═══════════════════════════════════════════════════════════════════════════════

def fun_fact_popup(screen, fonts, fact, clock):
    try:
        lines = [l.strip() for l in fact.split("\n")]
        popup = pygame.Rect(ML+GRID_W//2-185, MT+GRID_W//2-70, 370, 130)
        start = pygame.time.get_ticks()
        while pygame.time.get_ticks()-start < 3500:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
                if ev.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN): return
            overlay = pygame.Surface((W,H), pygame.SRCALPHA)
            pygame.draw.rect(overlay, (0,0,0,110), (0,0,W,H))
            screen.blit(overlay, (0,0))
            pygame.draw.rect(screen, CREAM,  popup, border_radius=18)
            pygame.draw.rect(screen, ORANGE, popup, 4,  border_radius=18)
            hdr = fonts["med"].render("💡 Did you know?", True, ORANGE)
            screen.blit(hdr, hdr.get_rect(center=(popup.centerx, popup.y+26)))
            for i,ln in enumerate(lines):
                s = fonts["sm"].render(ln, True, GD)
                screen.blit(s, s.get_rect(center=(popup.centerx,popup.y+60+i*22)))
            dim = fonts["tiny"].render("tap anywhere to skip", True, GRAY)
            screen.blit(dim, dim.get_rect(center=(popup.centerx, popup.bottom-14)))
            pygame.display.flip()
            clock.tick(FPS)
    except Exception:
        pass

# ═══════════════════════════════════════════════════════════════════════════════
# PODIUM SCREEN
# ═══════════════════════════════════════════════════════════════════════════════

def podium_screen(screen, fonts, stats, clock):
    try:
        best  = min(stats)
        worst = max(stats)
        avg   = sum(stats)/len(stats)
        start = pygame.time.get_ticks()
        confetti = make_confetti(W//2, H//2, 80)
        while pygame.time.get_ticks()-start < 6000:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
                if ev.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN): return
            screen.fill((255,195,80))
            confetti = tick_confetti(confetti)
            draw_confetti(screen, confetti)
            t = fonts["big"].render("🏆   Results Podium   🏆", True, BROWN)
            screen.blit(t, t.get_rect(center=(W//2, 80)))
            for px2,py2,pw2,ph2,col,lbl in [
                (W//2-195, 250, 130, 170, GOLD,  f"🥇 BEST\n{best} steps"),
                (W//2- 55, 300, 110, 120, GRAY,  f"AVG\n{avg:.1f}"),
                (W//2+ 70, 320, 120, 100, BROWN, f"🐢 MOST\n{worst} steps"),
            ]:
                pygame.draw.rect(screen, col,  (px2,py2,pw2,ph2), border_radius=8)
                pygame.draw.rect(screen, WHITE,(px2,py2,pw2,ph2), 2, border_radius=8)
                for li,ln in enumerate(lbl.split("\n")):
                    s = fonts["med"].render(ln, True, WHITE)
                    screen.blit(s, s.get_rect(center=(px2+pw2//2, py2+30+li*28)))
            sub = fonts["sm"].render(
                f"{len(stats)} rounds played  —  press any key to continue", True, WHITE)
            screen.blit(sub, sub.get_rect(center=(W//2, H-40)))
            pygame.display.flip()
            clock.tick(FPS)
    except Exception:
        pass

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN K-2 GAME
# ═══════════════════════════════════════════════════════════════════════════════

def run_k2(screen):
    pygame.display.set_caption("Wandering in the Woods — K-2")
    fonts  = _fonts()
    clock  = pygame.time.Clock()
    stars  = [(random.randint(0,W), random.randint(0,H//3),
               random.choice([1,1,2])) for _ in range(50)]
    trees  = [(44,H-75),(110,H-82),(195,H-75),(670,H-80),
              (750,H-75),(835,H-82),(885,H-75)]

    night  = False

    # ── character pick (simple 2-choice screen) ───────────────────────────────
    p1_char, p2_char = char_pick_screen(screen, fonts, stars, trees, night)
    # names come from character choice
    name_a = CHAR_OPTIONS[p1_char][0]   # e.g. "🐱 Cat"
    name_b = CHAR_OPTIONS[p2_char][0]
    trail_a = CHAR_OPTIONS[p1_char][4]
    trail_b = CHAR_OPTIONS[p2_char][4]

    # ── persistent settings ───────────────────────────────────────────────────
    spd         = 2
    show_heat   = False
    step_mode   = False
    fp_mode     = False
    guess_val   = ""      # renamed from pred_val → guess
    guess_locked= False
    guess_result= ""
    show_stats  = False   # stats hidden by default, shown on button click
    best_streak = 0
    cur_streak  = 0
    fact_idx    = 0
    bounce_t    = 0.0
    all_stats   = []
    paused      = False

    SLIDER = pygame.Rect(PX+8, H-52, PW-16, 8)

    # ── buttons ───────────────────────────────────────────────────────────────
    B_BACK   = pygame.Rect(12,   12,  108, 32)
    B_START  = pygame.Rect(PX+8, 40,  PW-16, 34)
    B_RESET  = pygame.Rect(PX+8, 80,  PW-16, 32)
    B_STEP   = pygame.Rect(PX+8, 116, (PW-20)//2, 26)
    B_FP     = pygame.Rect(PX+8+((PW-20)//2)+4, 116, (PW-20)//2, 26)
    B_NIGHT  = pygame.Rect(PX+8, 146, (PW-20)//2, 26)
    B_CHARS  = pygame.Rect(PX+8+((PW-20)//2)+4, 146, (PW-20)//2, 26)
    B_STATS  = pygame.Rect(PX+8, 176, PW-16, 26)   # toggle stats visibility
    B_PAUSE  = pygame.Rect(PX+8, 206, PW-16, 26)

    last_space = 0
    dragging   = False

    def new_round():
        return dict(
            pa=(0,0), pb=(GRID_N-1,GRID_N-1),
            ta=[(0,0)], tb=[(GRID_N-1,GRID_N-1)],
            hmap=[[0]*GRID_N for _ in range(GRID_N)],
            ca=0, cb=0,
            met=False, running=False,
            frame=0, last_t=0,
            start_ms=0, elapsed=0.0,
            stats=[],
            won=False,
            step_pending=False,
            closest_dist=(GRID_N-1)*2,
            closest_cell=None,
            confetti=[],
            unique_a=set(),
            unique_b=set(),
        )

    st = new_round()

    while True:
        now = pygame.time.get_ticks()
        if st["running"] and not paused:
            bounce_t += 0.18

        # ── events ────────────────────────────────────────────────────────────
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return

                # guess input — only before start
                if not guess_locked:
                    if ev.key == pygame.K_BACKSPACE:
                        guess_val = guess_val[:-1]
                    elif ev.unicode.isdigit() and len(guess_val) < 4:
                        guess_val += ev.unicode

                # SPACE — throttled
                if ev.key == pygame.K_SPACE and now-last_space > 180:
                    last_space = now
                    if not st["running"] and not st["met"]:
                        st["running"]  = True
                        st["start_ms"] = now
                        st["last_t"]   = now
                        guess_locked   = True
                        sfx_start()
                        safe_speak(f"Go! Find each other!")
                    elif step_mode and st["running"]:
                        st["step_pending"] = True

                if ev.key == pygame.K_n:  night = not night
                if ev.key == pygame.K_f:  fp_mode = not fp_mode
                if ev.key == pygame.K_p and st["running"]:
                    paused = not paused
                if ev.key == pygame.K_r and st["met"]:
                    st=new_round(); guess_locked=False; guess_result=""
                    show_heat=False; paused=False

            if ev.type == pygame.MOUSEBUTTONDOWN:
                mx, my = ev.pos

                if B_BACK.collidepoint(mx,my):
                    return

                if B_START.collidepoint(mx,my) and not st["running"] and not st["met"]:
                    st["running"]  = True
                    st["start_ms"] = now
                    st["last_t"]   = now   # reset so first step fires after delay
                    guess_locked   = True
                    sfx_start()
                    safe_speak("Go! Find each other!")

                if B_RESET.collidepoint(mx,my):
                    st=new_round(); guess_locked=False; guess_result=""
                    show_heat=False; paused=False

                if B_STEP.collidepoint(mx,my):  step_mode = not step_mode
                if B_FP.collidepoint(mx,my):    fp_mode   = not fp_mode
                if B_NIGHT.collidepoint(mx,my): night     = not night
                if B_STATS.collidepoint(mx,my): show_stats = not show_stats

                if B_CHARS.collidepoint(mx,my):
                    # go back to character pick screen
                    p1_char, p2_char = char_pick_screen(
                        screen, fonts, stars, trees, night)
                    name_a  = CHAR_OPTIONS[p1_char][0]
                    name_b  = CHAR_OPTIONS[p2_char][0]
                    trail_a = CHAR_OPTIONS[p1_char][4]
                    trail_b = CHAR_OPTIONS[p2_char][4]
                    st=new_round(); guess_locked=False; guess_result=""
                    paused=False

                if B_PAUSE.collidepoint(mx,my) and st["running"] and not st["met"]:
                    paused = not paused

                if st["met"]:
                    HB = pygame.Rect(PX+8, H-168, PW-16, 26)
                    if HB.collidepoint(mx,my):
                        show_heat = not show_heat

                if SLIDER.inflate(0,28).collidepoint(mx,my):
                    dragging = True

            if ev.type == pygame.MOUSEBUTTONUP:
                dragging = False
            if ev.type == pygame.MOUSEMOTION and dragging:
                rel = (ev.pos[0]-SLIDER.x) / max(SLIDER.width,1)
                spd = max(0, min(len(SPEEDS)-1, int(rel*len(SPEEDS))))

        # ── step logic ────────────────────────────────────────────────────────
        do_step = False
        if st["running"] and not st["met"] and not paused:
            if st["ca"] >= MAX_STEPS:
                st["running"] = False
            elif step_mode:
                do_step = bool(st["step_pending"])
                st["step_pending"] = False
            else:
                do_step = (now - st["last_t"] >= SPEEDS[spd])

        if do_step:
            st["last_t"] = now
            ca, ra = rstep(*st["pa"])
            cb, rb = rstep(*st["pb"])
            st["pa"] = (ca,ra); st["pb"] = (cb,rb)
            st["ta"].append((ca,ra)); st["tb"].append((cb,rb))
            st["hmap"][ra][ca] = min(st["hmap"][ra][ca]+1, 20)
            st["hmap"][rb][cb] = min(st["hmap"][rb][cb]+1, 20)
            st["ca"] += 1; st["cb"] += 1
            st["unique_a"].add((ca,ra))
            st["unique_b"].add((cb,rb))
            sfx_step()

            dist = manhattan(st["pa"], st["pb"])
            if dist < st["closest_dist"]:
                st["closest_dist"] = dist
                st["closest_cell"] = (ca,ra)

            if (ca,ra) == (cb,rb):
                st["running"] = False
                st["met"]     = True
                st["elapsed"] = (now - st["start_ms"]) / 1000
                mx2, my2 = cell_rect(ca,ra).center
                st["confetti"] = make_confetti(mx2, my2, 80)
                st["stats"].append(st["ca"])
                all_stats.append(st["ca"])
                if len(all_stats) > MAX_STATS: all_stats.pop(0)
                sfx_celebrate()

                if guess_val.isdigit():
                    g    = int(guess_val)
                    diff = abs(g - st["ca"])
                    if diff == 0:    guess_result = "PERFECT!! 🎯"
                    elif diff <= 3:  guess_result = f"So close! Off by {diff}! 🌟"
                    elif diff <= 8:  guess_result = f"Great! Off by {diff} 👏"
                    elif diff <= 20: guess_result = f"Good try! Off by {diff}"
                    else:            guess_result = f"Off by {diff} — try again!"
                else:
                    guess_result = ""

                safe_speak(f"{name_a} and {name_b} found each other in {st['ca']} steps!")

                fun_fact_popup(screen, fonts,
                               FUN_FACTS[fact_idx % len(FUN_FACTS)], clock)
                fact_idx += 1

                if len(all_stats) >= 5 and len(all_stats) % 5 == 0:
                    podium_screen(screen, fonts, all_stats, clock)

        if st["confetti"]:
            st["confetti"] = tick_confetti(st["confetti"])

        # ══════════════════════════════════════════════════════
        # DRAW
        # ══════════════════════════════════════════════════════
        draw_bg(screen, stars, night)
        for tx,ty in trees:
            draw_tree(screen, tx, ty, 34)

        # title vs celebration
        if not st["met"]:
            title_col = (255,245,200) if night else YELLOW
            title_txt = "🌲  Wandering in the Woods  🌲"
            # chunky outlined title for bubbly look
            for dx,dy in [(-2,0),(2,0),(0,-2),(0,2),(-2,-2),(2,2)]:
                sh = fonts["title"].render(title_txt, True, BROWN)
                screen.blit(sh, sh.get_rect(center=(ML+GRID_W//2+dx, 52+dy)))
            t = fonts["title"].render(title_txt, True, title_col)
            screen.blit(t, t.get_rect(center=(ML+GRID_W//2, 52)))
        else:
            st["frame"] += 1
            draw_balloons(screen, st["frame"])
            draw_confetti(screen, st["confetti"])
            cel = fonts["big"].render("🎉  They Found Each Other!  🎉", True, ORANGE)
            sh  = fonts["big"].render("🎉  They Found Each Other!  🎉", True, BROWN)
            pos = cel.get_rect(center=(ML+GRID_W//2, 48))
            screen.blit(sh, pos.move(2,2))
            screen.blit(cel, pos)

        closest = st["closest_cell"] if st["ca"] > 0 else None
        draw_grid(screen, st["hmap"], show_heat and st["met"], closest)
        draw_trail(screen, st["ta"], trail_a, fp_mode, flip=False)
        draw_trail(screen, st["tb"], trail_b, fp_mode, flip=True)

        mood_a, _ = get_mood(st["ca"], st["met"])
        mood_b, _ = get_mood(st["cb"], st["met"])
        draw_char(screen, *st["pa"], p1_char, mood_a, fonts, bounce_t)
        draw_char(screen, *st["pb"], p2_char, mood_b, fonts, bounce_t+math.pi)

        # distance bar under grid
        if st["running"] and not paused:
            dist  = manhattan(st["pa"], st["pb"])
            maxd  = (GRID_N-1)*2
            prox  = 1 - dist/max(maxd,1)
            bary  = MT + GRID_N*CELL + 4
            bar_r = pygame.Rect(ML, bary, GRID_W, 10)
            pygame.draw.rect(screen, DKGRAY, bar_r, border_radius=5)
            fw = max(0, int(GRID_W*prox))
            if fw:
                pygame.draw.rect(screen,
                    (int(220*prox), int(200*(1-prox)), 50),
                    pygame.Rect(ML,bary,fw,10), border_radius=5)
            pygame.draw.rect(screen, BROWN, bar_r, 1, border_radius=5)
            dl = fonts["tiny"].render(
                f"Distance: {dist} cell{'s' if dist!=1 else ''}", True, WHITE)
            screen.blit(dl, dl.get_rect(center=(ML+GRID_W//2, bary+20)))

        # paused overlay
        if paused and st["running"] and not st["met"]:
            ov = pygame.Surface((GRID_W, GRID_N*CELL), pygame.SRCALPHA)
            pygame.draw.rect(ov, (0,0,0,100), (0,0,GRID_W,GRID_N*CELL))
            screen.blit(ov, (ML, MT))
            pm = fonts["big"].render("⏸   PAUSED", True, WHITE)
            ps = fonts["sm"].render("Press P or click Resume to continue", True, YELLOW)
            screen.blit(pm, pm.get_rect(center=(ML+GRID_W//2, MT+GRID_N*CELL//2-16)))
            screen.blit(ps, ps.get_rect(center=(ML+GRID_W//2, MT+GRID_N*CELL//2+20)))

        # ── RIGHT PANEL ───────────────────────────────────────
        panel(screen, PX, 30, PW, H-98)

        # buttons
        btn(screen, fonts, B_BACK,  "← Menu",    GD)
        if not st["running"] and not st["met"]:
            btn(screen, fonts, B_START, "▶  Start  (SPACE)", ORANGE)
        btn(screen, fonts, B_RESET, "↺  Reset",  GM)
        btn(screen, fonts, B_STEP,
            "Step: ON ⏸" if step_mode else "Step: OFF", RED if step_mode else DKGRAY)
        btn(screen, fonts, B_FP,
            "Feet: ON 👣" if fp_mode else "Feet: OFF", PURPLE if fp_mode else DKGRAY)
        btn(screen, fonts, B_NIGHT,
            "🌙 Night" if not night else "☀ Day",
            (40,40,110) if night else (210,145,0))
        btn(screen, fonts, B_CHARS,  "Change Chars", (100,80,180))
        btn(screen, fonts, B_STATS,
            "📊 Hide Stats" if show_stats else "📊 Show Stats",
            (60,130,180) if show_stats else DKGRAY)
        if st["running"] and not st["met"]:
            pause_label = "▶ Resume" if paused else "⏸ Pause"
            pause_col   = ORANGE    if paused else (60,100,180)
            btn(screen, fonts, B_PAUSE, pause_label, pause_col)

        # ── panel info ────────────────────────────────────────
        y = 238

        mi_a     = MOOD_ICONS.get(mood_a, "😊")
        mi_b     = MOOD_ICONS.get(mood_b, "😊")
        na_short = name_a.split()[1] if " " in name_a else name_a
        nb_short = name_b.split()[1] if " " in name_b else name_b

        # coloured pill header — Steps
        y = section_header(screen, fonts, "👣  Steps", (180, 100, 30), y)
        screen.blit(fonts["sm"].render(f"P1 {na_short}:  {st['ca']} steps  {mi_a}",
                    True, ORANGE), (PX+14, y)); y += 22
        screen.blit(fonts["sm"].render(f"P2 {nb_short}:  {st['cb']} steps  {mi_b}",
                    True, BLUE),   (PX+14, y)); y += 22

        # cells explored
        explored = len(st["unique_a"] | st["unique_b"])
        total    = GRID_N * GRID_N
        screen.blit(fonts["tiny"].render(
            f"Explored  {explored}/{total} cells  ({int(explored/total*100)}%)",
            True, BROWN), (PX+14, y)); y += 18

        # timer
        el = (now - st["start_ms"]) / 1000 if st["running"] else st["elapsed"]
        if st["running"] or st["met"]:
            screen.blit(fonts["sm"].render(f"⏱  {el:.1f}s", True, BROWN), (PX+14, y))
        y += 22

        divline(screen, y); y += 10

        # ── STATS — hidden unless toggled ─────────────────────
        if show_stats and len(all_stats) > 0:
            y = section_header(screen, fonts, "📊  Best Score", (60, 140, 60), y)
            best_ever  = min(all_stats)
            best_round = all_stats.index(best_ever) + 1
            pygame.draw.rect(screen, (255, 248, 215),
                             pygame.Rect(PX+10, y, PW-20, 54), border_radius=14)
            pygame.draw.rect(screen, GOLD,
                             pygame.Rect(PX+10, y, PW-20, 54), 3, border_radius=14)
            star_s   = fonts["big"].render("⭐", True, GOLD)
            best_txt = fonts["big"].render(f"{best_ever} steps!", True, GD)
            screen.blit(star_s,   (PX+16,  y+12))
            screen.blit(best_txt, best_txt.get_rect(center=(PX+PW//2+12, y+27)))
            y += 60
            screen.blit(fonts["tiny"].render(
                f"Round {best_round}   •   {len(all_stats)} rounds played",
                True, BROWN), (PX+14, y)); y += 20
            divline(screen, y); y += 10

        # ── GUESS section ──────────────────────────────────────
        y = section_header(screen, fonts, "🎯  Make a Guess!", (200, 80, 20), y)
        if not guess_locked:
            screen.blit(fonts["tiny"].render("How many steps to find each other?",
                        True, GRAY), (PX+10,y)); y+=16
            box = pygame.Rect(PX+10, y, PW-20, 28)
            pygame.draw.rect(screen, WHITE,  box, border_radius=8)
            pygame.draw.rect(screen, ORANGE, box, 2, border_radius=8)
            screen.blit(fonts["med"].render(guess_val+"|", True, BLACK),
                        (box.x+8, box.y+4))
            y += 32
            screen.blit(fonts["tiny"].render("Type a number, then press Start!",
                        True, GRAY), (PX+10,y)); y+=16
        else:
            if guess_val:
                screen.blit(fonts["tiny"].render(f"Your guess: {guess_val} steps",
                            True, BROWN), (PX+10,y)); y+=17
            if guess_result:
                rc2 = GOLD if "PERFECT" in guess_result else \
                      LIME if "So" in guess_result else \
                      BLUE if "Great" in guess_result else BROWN
                screen.blit(fonts["sm"].render(guess_result, True, rc2),(PX+10,y)); y+=18

        # heatmap button (only after meeting)
        if st["met"]:
            HB = pygame.Rect(PX+8, H-168, PW-16, 26)
            btn(screen, fonts, HB,
                "🌡 Hide Heatmap" if show_heat else "🌡 Show Heatmap",
                RED if show_heat else GM)

        # speed slider
        screen.blit(fonts["tiny"].render(f"⚡  {SPEED_NAMES[spd]}", True, WHITE),
                    (SLIDER.x, SLIDER.y-16))
        pygame.draw.rect(screen, (50,50,50),  SLIDER, border_radius=4)
        pygame.draw.rect(screen, ORANGE,      SLIDER, 1, border_radius=4)
        kx = SLIDER.x + int(spd/max(len(SPEEDS)-1,1)*SLIDER.width)
        pygame.draw.circle(screen, YELLOW, (kx, SLIDER.centery), 10)
        pygame.draw.circle(screen, BROWN,  (kx, SLIDER.centery), 10, 2)

        # bottom hint
        if not st["running"] and not st["met"]:
            h2 = fonts["sm"].render("Type a guess above → then press Start! 🌲",
                                    True, (255,245,200) if night else YELLOW)
            screen.blit(h2, h2.get_rect(center=(ML+GRID_W//2, H-42)))
            h3 = fonts["tiny"].render("N = night   F = footprints   P = pause   R = reset",
                                      True, (200,200,200))
            screen.blit(h3, h3.get_rect(center=(ML+GRID_W//2, H-24)))

        pygame.display.flip()
        clock.tick(FPS)
