"""
main.py  —  Wandering in the Woods
===================================
Combined entry point for K-2 mode (this dev) and Grades 3-5 mode (Spandana).

Run with:   python main.py
Requires:   pip install pygame numpy
Optional:   pip install pyttsx3
"""

import pygame
import sys
import random
import math

from mode_k2 import run_k2
from mode_35 import run_35

# ── window — use 1000x650 so mode_35 fits without resizing ───────────────────
W, H = 1000, 650

# ── colours ───────────────────────────────────────────────────────────────────
SKY_T   = (250, 130,  60)
SKY_B   = (255, 210, 130)
GD      = ( 34,  85,  34)
GM      = ( 60, 140,  60)
BROWN   = (101,  67,  33)
YELLOW  = (255, 220,  50)
ORANGE  = (255, 140,   0)
WHITE   = (255, 255, 255)
CREAM   = (255, 252, 235)
DKBLUE  = ( 30,  60, 130)

# ── fonts ─────────────────────────────────────────────────────────────────────
def _fonts():
    return {
        "title": pygame.font.SysFont("comicsansms", 48, bold=True),
        "sub"  : pygame.font.SysFont("comicsansms", 20),
        "btn"  : pygame.font.SysFont("comicsansms", 26, bold=True),
        "small": pygame.font.SysFont("comicsansms", 16),
    }

# ── helpers ───────────────────────────────────────────────────────────────────
def draw_tree(surf, x, y, s=40):
    pygame.draw.rect(surf, BROWN, (x-s//8, y, s//4, s//3))
    pygame.draw.polygon(surf, GM,  [(x,y-s),(x-s//2,y),(x+s//2,y)])
    pygame.draw.polygon(surf, GD,  [(x,y-int(s*1.4)),(x-s//3,y-s//2),(x+s//3,y-s//2)])

def draw_bg(surf, stars):
    # gradient sky
    for y in range(H - 80):
        ratio = y / max(H-80, 1)
        c = tuple(int(SKY_T[i]+(SKY_B[i]-SKY_T[i])*ratio) for i in range(3))
        pygame.draw.line(surf, c, (0,y), (W,y))
    # stars
    for sx, sy, sr in stars:
        pygame.draw.circle(surf, (255,255,220), (sx,sy), sr)
    # ground
    pygame.draw.rect(surf, GD, (0, H-80, W, 80))
    pygame.draw.rect(surf, GM, (0, H-80, W, 22))

def draw_btn(surf, fonts, rect, label, bg, fg=WHITE):
    # shadow
    shadow = pygame.Rect(rect.x+3, rect.y+5, rect.w, rect.h)
    pygame.draw.rect(surf, tuple(max(0,c-70) for c in bg), shadow, border_radius=18)
    # main
    pygame.draw.rect(surf, bg, rect, border_radius=18)
    # shine
    shine = pygame.Rect(rect.x+8, rect.y+5, rect.w-16, rect.h//3)
    pygame.draw.rect(surf, tuple(min(255,c+50) for c in bg), shine, border_radius=14)
    # border
    pygame.draw.rect(surf, BROWN, rect, 2, border_radius=18)
    # text
    s = fonts["btn"].render(label, True, fg)
    surf.blit(s, s.get_rect(center=rect.center))

# ── safe menu sound ───────────────────────────────────────────────────────────
def play_menu_chime():
    try:
        import numpy as np
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        for freq in [523, 659]:
            n   = int(44100 * 0.15)
            t   = __import__("numpy").linspace(0, 0.15, n, False)
            w   = __import__("numpy").sin(2 * 3.14159 * freq * t)
            fade = min(int(n*0.2), 300)
            w[-fade:] *= __import__("numpy").linspace(1,0,fade)
            s   = (w * 0.2 * 32767).astype(__import__("numpy").int16)
            st  = __import__("numpy").column_stack([s,s])
            pygame.sndarray.make_sound(st).play()
            pygame.time.delay(160)
    except Exception:
        pass

# ── background music ──────────────────────────────────────────────────────────
def start_music():
    try:
        pygame.mixer.music.load("Game_music.mp3")
        pygame.mixer.music.set_volume(0.35)
        pygame.mixer.music.play(-1)
    except Exception:
        pass   # no crash if music file missing

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN MENU
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    pygame.init()
    try:
        pygame.mixer.init()
    except Exception:
        pass

    # Use 1000x650 so mode_35 renders correctly
    # mode_k2 also works fine at this size — it draws relative to its own W,H constants
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Wandering in the Woods")
    clock  = pygame.time.Clock()
    fonts  = _fonts()

    # fixed decorative elements
    stars    = [(random.randint(0,W), random.randint(0,H//3),
                 random.choice([1,1,2])) for _ in range(40)]
    tree_pos = [(60,H-85),(150,H-95),(270,H-85),(380,H-90),
                (620,H-88),(730,H-85),(840,H-95),(960,H-85)]

    # button rects — centred, nice spacing
    BTN_K2   = pygame.Rect(W//2-200, 300, 400, 68)
    BTN_35   = pygame.Rect(W//2-200, 390, 400, 68)
    BTN_QUIT = pygame.Rect(W//2-120, 490, 240, 44)

    start_music()
    play_menu_chime()

    while True:

        # ── events ────────────────────────────────────────────────────────────
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

            if ev.type == pygame.MOUSEBUTTONDOWN:
                mx, my = ev.pos

                if BTN_K2.collidepoint(mx, my):
                    # K-2 mode draws at 900x600 internally but screen is 1000x650
                    # so we pass the full screen — it draws from top-left, rest stays as bg
                    run_k2(screen)
                    play_menu_chime()

                elif BTN_35.collidepoint(mx, my):
                    run_35(screen)
                    play_menu_chime()

                elif BTN_QUIT.collidepoint(mx, my):
                    pygame.quit(); sys.exit()

        # ── draw ──────────────────────────────────────────────────────────────
        draw_bg(screen, stars)
        for tx, ty in tree_pos:
            draw_tree(screen, tx, ty, 42)

        # title with outline
        title_txt = "🌲  Wandering in the Woods  🌲"
        for dx, dy in [(-2,0),(2,0),(0,-2),(0,2)]:
            sh = fonts["title"].render(title_txt, True, BROWN)
            screen.blit(sh, sh.get_rect(center=(W//2+dx, 170+dy)))
        t = fonts["title"].render(title_txt, True, YELLOW)
        screen.blit(t, t.get_rect(center=(W//2, 170)))

        # subtitle
        sub = fonts["sub"].render(
            "Two friends lost in a forest — can they find each other?", True, WHITE)
        screen.blit(sub, sub.get_rect(center=(W//2, 232)))

        # grade buttons
        draw_btn(screen, fonts, BTN_K2,   "🌱  Grades K – 2   (Beginners)",  (60,140,60))
        draw_btn(screen, fonts, BTN_35,   "🌿  Grades 3 – 5   (Explorer)",   (50,100,200))
        draw_btn(screen, fonts, BTN_QUIT, "Exit",                             (160,60,60))

        # small credit line
        credit = fonts["small"].render(
            "CS251  ·  Lewis University  ·  Spring 2026", True, (220,210,180))
        screen.blit(credit, credit.get_rect(center=(W//2, 575)))

        esc_hint = fonts["small"].render("Press ESC to quit", True, (200,200,200))
        screen.blit(esc_hint, esc_hint.get_rect(center=(W//2, 600)))

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
