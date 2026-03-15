import pygame
import sys
import random
import math

# ── BUILT-IN SOUND FUNCTIONS ────────────────────────────────
def play_step(): pass
def play_celebration(): pass
def play_start(): pass
def play_menu(): pass

# ── colours ───────────────────────────────────────────────────────────────────
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
SKY_T = (240, 140, 70)
SKY_B = (255, 220, 140)
GD = (34, 85, 34)
GM = (60, 140, 60)
GL = (180, 230, 140)
BROWN = (110, 70, 30)
YELLOW = (255, 235, 60)
ORANGE = (255, 145, 10)
RED = (225, 55, 55)
BLUE = (55, 110, 230)
GOLD = (255, 200, 0)
PURPLE = (150, 65, 215)
CREAM = (255, 250, 230)
GREEN = (34, 139, 34)
GRAY = (150, 150, 150)

TRAIL_COLS = [
    (255, 90, 90, 145), (70, 115, 255, 145), 
    (255, 210, 40, 145), (80, 210, 100, 145)
]

CHAR_EMOJIS = ["🧑", "👩", "👦", "👧"]
CHAR_COLORS = [(210, 140, 55), (60, 130, 210), (255, 145, 10), (150, 65, 215)]

# ── layout ────────────────────────────────────────────────────────────────────
W, H = 1000, 650
FPS = 60
MAX_STATS = 50
MAX_STEPS = 5000

# ── game state ────────────────────────────────────────────────────────────────
class GameState:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.grid_w = 8
        self.grid_h = 6
        self.num_players = 2
        self.positions = [(0,0), (7,5), (0,0), (7,5)]
        self.trails = [[(0,0)], [(7,5)], [], []]
        self.heat_map = [[0]*10 for _ in range(12)]
        self.steps = [0, 0, 0, 0]
        self.running = False
        self.meeting = False
        self.elapsed_time = 0
        self.stats = []
        self.start_time = 0
        self.last_step_time = 0
        self.cell_size = 72
        self.speed_idx = 2
        self.speeds = [800, 500, 300, 150, 60]
        self.show_heat = False
        self.last_space = 0

state = GameState()

def cell_rect(c, r):
    return pygame.Rect(60 + c*state.cell_size, 100 + r*state.cell_size, 
                      state.cell_size, state.cell_size)

def random_step(c, r, gw, gh):
    dirs = [(dc,dr) for dc,dr in [(-1,0),(1,0),(0,-1),(0,1)] 
            if 0 <= c+dc < gw and 0 <= r+dr < gh]
    if not dirs:
        return c, r
    dc, dr = random.choice(dirs)
    return c + dc, r + dr

def draw_sky_gradient(screen):
    for y in range(H):
        ratio = y / H
        r = int(240 + ratio*15)
        g = int(140 + ratio*80)
        b = int(70 + ratio*70)
        pygame.draw.line(screen, (r,g,b), (0,y), (W,y))

def draw_grid(screen):
    gw, gh = state.grid_w, state.grid_h
    for r in range(gh):
        for c in range(gw):
            col = GL if (r+c)%2==0 else GM
            if state.show_heat and state.meeting:
                visits = state.heat_map[r][c] if r < len(state.heat_map) and c < len(state.heat_map[0]) else 0
                heat_idx = min(4, visits//3)
                heat_cols = [GL, (230,240,80), (255,210,40), (255,140,30), (220,40,40)]
                col = heat_cols[heat_idx]
            pygame.draw.rect(screen, col, cell_rect(c,r))
            pygame.draw.rect(screen, GD, cell_rect(c,r), 2)

def draw_trail(screen, trail, col):
    if not trail:
        return
    ts = pygame.Surface((W, H), pygame.SRCALPHA)
    capped = trail[-100:]
    for i, (c, r) in enumerate(capped):
        alpha = min(255, int(80 + 120*(i/len(capped))))
        pygame.draw.ellipse(ts, col[:3]+(alpha,), 
                           cell_rect(c,r).inflate(-20,-20))
    screen.blit(ts, (0,0))

def draw_character(screen, c, r, player_idx, bounce=0):
    emoji = CHAR_EMOJIS[player_idx % len(CHAR_EMOJIS)]
    rc = cell_rect(c, r)
    cx, cy = rc.centerx, rc.centery + int(math.sin(bounce)*4)
    
    pygame.draw.ellipse(screen, (0,0,0,60), (cx-20, rc.centery+25, 40, 15))
    
    try:
        font = pygame.font.SysFont("segoeuisymbol", 52, bold=True)
    except:
        font = pygame.font.SysFont(None, 52, bold=True)
    txt = font.render(emoji, True, CHAR_COLORS[player_idx % len(CHAR_COLORS)])
    screen.blit(txt, txt.get_rect(center=(cx, cy)))

def draw_panel(screen, x, y, w, h):
    pygame.draw.rect(screen, CREAM, (x,y,w,h), border_radius=20)
    pygame.draw.rect(screen, (200, 160, 100), (x,y,w,h), 3, border_radius=20)

def draw_button(screen, rect, text, bg_col, fg_col=BLACK):
    shadow_rect = pygame.Rect(rect.x+3, rect.y+3, rect.w, rect.h)
    pygame.draw.rect(screen, (0,0,0,80), shadow_rect, border_radius=12)
    pygame.draw.rect(screen, bg_col, rect, border_radius=12)
    pygame.draw.rect(screen, WHITE, rect.inflate(-6,-6), 1, border_radius=10)
    
    font = pygame.font.SysFont("arial", 18, bold=True)
    txt = font.render(text, True, fg_col)
    screen.blit(txt, txt.get_rect(center=rect.center))


def setup_screen(screen, clock):
    placing_player = 0
    
    while True:
        mx, my = pygame.mouse.get_pos()
        
        # PROCESS EVENTS FIRST
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
            if event.type == pygame.MOUSEBUTTONDOWN:
                print(f"Click at ({mx}, {my})")  # DEBUG PRINT
                
                
                # Width buttons
                if 155 <= mx <= 255 and 200 <= my <= 240:  # + Width
                    print("Width + clicked")
                    state.grid_w = min(12, state.grid_w + 1)
                    state.cell_size = min(72, 800 // state.grid_w)
                    state.reset()
                
                if 285 <= mx <= 385 and 200 <= my <= 240:  # - Width
                    print("- Width clicked")
                    state.grid_w = max(4, state.grid_w - 1)
                    state.cell_size = min(72, 800 // state.grid_w)
                    state.reset()
                
                # Height buttons
                if 155 <= mx <= 255 and 250 <= my <= 290:  # + Height
                    print("Height + clicked")
                    state.grid_h = min(10, state.grid_h + 1)
                    state.cell_size = min(72, 600 // state.grid_h)
                    state.reset()
                
                if 285 <= mx <= 385 and 250 <= my <= 290:  # - Height
                    print("- Height clicked")
                    state.grid_h = max(4, state.grid_h - 1)
                    state.cell_size = min(72, 600 // state.grid_h)
                    state.reset()
                
                # Player buttons 
                if 150 <= mx <= 380 and 320 <= my <= 360:  # 2 Players
                    print("2 Players clicked")
                    state.num_players = 2
                    state.reset()
                if 150 <= mx <= 380 and 375 <= my <= 415:  # 3 Players
                    print("3 Players clicked")
                    state.num_players = 3
                    state.reset()
                if 150 <= mx <= 380 and 430 <= my <= 470:  # 4 Players
                    print("4 Players clicked")
                    state.num_players = 4
                    state.reset()
                if 150 <= mx <= 380 and 485 <= my <= 525:  # 5 Players
                    print("5 Players clicked")
                    state.num_players = 5
                    state.reset()
                
                # Grid placement
                grid_rect = pygame.Rect(60, 100, state.grid_w*state.cell_size, state.grid_h*state.cell_size)
                if grid_rect.collidepoint(mx, my):
                    gc = max(0, min(state.grid_w-1, (mx-60) // state.cell_size))
                    gr = max(0, min(state.grid_h-1, (my-100) // state.cell_size))
                    state.positions[placing_player] = (gc, gr)
                    placing_player = (placing_player + 1) % state.num_players
                    print(f"Player {placing_player} placed at ({gc}, {gr})")
                
                # START BUTTON 
                if 400 <= mx <= 600 and 500 <= my <= 550:
                    print("START GAME clicked!")
                    play_start()
                    return True
        
        # DRAWING
        screen.fill((200, 180, 120))
        draw_sky_gradient(screen)
        draw_grid(screen)
        
        # Title
        font = pygame.font.SysFont("arial", 36, bold=True)
        title = font.render("🌲 Wandering in the Woods — Grades 3-5 🌲", True, YELLOW)
        screen.blit(title, title.get_rect(center=(W//2, 40)))
        
        # Panel
        draw_panel(screen, 120, 170, 450, 380)
        
        # Labels and buttons
        font20 = pygame.font.SysFont("arial", 20, bold=True)
        screen.blit(font20.render("Grid Size:", True, BLACK), (140, 185))
        screen.blit(font20.render(f"W: {state.grid_w}", True, ORANGE), (140, 205))
        draw_button(screen, pygame.Rect(155, 200, 100, 40), "+", ORANGE)
        draw_button(screen, pygame.Rect(285, 200, 100, 40), "-", GRAY)
        
        screen.blit(font20.render(f"H: {state.grid_h}", True, ORANGE), (140, 255))
        draw_button(screen, pygame.Rect(155, 250, 100, 40), "+", ORANGE)
        draw_button(screen, pygame.Rect(285, 250, 100, 40), "-", GRAY)
        
        screen.blit(font20.render("Players:", True, BLACK), (140, 305))
        player_cols = [GRAY, GRAY, GOLD if state.num_players == 3 else GRAY, GRAY]
        draw_button(screen, pygame.Rect(150, 320, 230, 40), "2 Players", GRAY)
        draw_button(screen, pygame.Rect(150, 375, 230, 40), "3 Players", GOLD if state.num_players == 3 else GRAY)
        draw_button(screen, pygame.Rect(150, 430, 230, 40), "4 Players", GRAY)
        draw_button(screen, pygame.Rect(150, 485, 230, 40), "5 Players", GRAY)
        
        pos_font = pygame.font.SysFont("arial", 16)
        screen.blit(pos_font.render("Click grid cells to place players", True, BROWN), (140, 440))
        screen.blit(pos_font.render(f"Next: Player {placing_player+1} at {state.positions[placing_player]}", True, ORANGE), (140, 460))
        
        for i, (c,r) in enumerate(state.positions[:state.num_players]):
            pygame.draw.rect(screen, TRAIL_COLS[i], cell_rect(c,r), 5)
        
        draw_button(screen, pygame.Rect(400, 500, 200, 50), "▶ START GAME", ORANGE)
        
        pygame.display.flip()
        clock.tick(FPS)


def run_35(screen):
    clock = pygame.time.Clock()
    bounce_t = 0
    dragging_slider = False
    
    if not setup_screen(screen, clock):
        return
    
    fonts = {
        'big': pygame.font.SysFont("arial", 28, bold=True),
        'med': pygame.font.SysFont("arial", 22, bold=True),
        'sm': pygame.font.SysFont("arial", 18),
        'tiny': pygame.font.SysFont("arial", 14)
    }
    
    while True:
        now = pygame.time.get_ticks()
        mx, my = pygame.mouse.get_pos()
        
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return
                if ev.key == pygame.K_SPACE and now - state.last_space > 200:
                    state.last_space = now
                    if not state.running and not state.meeting:
                        state.running = True
                        state.start_time = now
                        state.last_step_time = now
                        play_start()
            
            if ev.type == pygame.MOUSEBUTTONDOWN:
                slider_rect = pygame.Rect(450, 580, 200, 20)
                if slider_rect.inflate(20, 20).collidepoint(mx, my):
                    dragging_slider = True
                
                reset_rect = pygame.Rect(850, 110, 100, 40)
                heatmap_rect = pygame.Rect(850, 160, 100, 40)
                replay_rect = pygame.Rect(850, 250, 100, 40)
                
                if reset_rect.collidepoint(mx, my):
                    state.reset()
                if state.meeting and heatmap_rect.collidepoint(mx, my):
                    state.show_heat = not state.show_heat
                if state.meeting and replay_rect.collidepoint(mx, my):
                    orig_positions = [trail[0] for trail in state.trails[:state.num_players]]
                    state.reset()
                    state.positions = orig_positions
                    for i in range(state.num_players):
                        state.trails[i] = [state.positions[i]]
            
            if ev.type == pygame.MOUSEBUTTONUP:
                dragging_slider = False
        
        if dragging_slider:
            slider_rect = pygame.Rect(450, 580, 200, 20)
            rel_pos = max(0, min(1, (mx - slider_rect.x) / slider_rect.width))
            state.speed_idx = int(rel_pos * (len(state.speeds) - 1))
        

        if state.running and not state.meeting and state.steps[0] < MAX_STEPS:
            if now - state.last_step_time >= state.speeds[state.speed_idx]:
                state.last_step_time = now
                gw, gh = state.grid_w, state.grid_h
                
                all_same_pos = True
                for i in range(state.num_players):
                    c, r = state.positions[i]
                    nc, nr = random_step(c, r, gw, gh)
                    state.positions[i] = (nc, nr)
                    state.trails[i].append((nc, nr))
                    if 0 <= nr < len(state.heat_map) and 0 <= nc < len(state.heat_map[0]):
                        state.heat_map[nr][nc] = min(20, state.heat_map[nr][nc] + 1)
                    state.steps[i] += 1
                    play_step()
                    
                    if i > 0 and state.positions[i] != state.positions[0]:
                        all_same_pos = False
                
                if all_same_pos:
                    state.running = False
                    state.meeting = True
                    state.elapsed_time = now
                    state.current_stat = min(state.steps[:state.num_players])
                    state.stats.append(state.current_stat)
                    if len(state.stats) > MAX_STATS:
                        state.stats.pop(0)
                    play_celebration()
        

        draw_sky_gradient(screen)
        draw_grid(screen)
        
        title = fonts['big'].render("🌲 Wandering in the Woods 🌲", True, YELLOW)
        screen.blit(title, title.get_rect(center=(W//2, 30)))
        
        for i in range(state.num_players):
            draw_trail(screen, state.trails[i], TRAIL_COLS[i])
        
        bounce_t += 0.15
        for i in range(state.num_players):
            draw_character(screen, *state.positions[i], i, bounce_t + i * 0.5)
        
        draw_panel(screen, 830, 80, 150, 500)
        
        y = 90
        screen.blit(fonts['med'].render("Game Info", True, ORANGE), (845, y)); y += 35
        total_steps = sum(state.steps[:state.num_players])
        screen.blit(fonts['sm'].render(f"Steps: {total_steps}", True, BROWN), (845, y)); y += 25
        
        if state.running or state.meeting:
            elapsed = (now - state.start_time) / 1000 if state.running else state.elapsed_time / 1000
            screen.blit(fonts['sm'].render(f"Time: {elapsed:.1f}s", True, BROWN), (845, y)); y += 25
        
        draw_button(screen, pygame.Rect(850, 110, 100, 40), "↺ Reset", GRAY)
        if state.meeting:
            btn_text = "🌡 Hide" if state.show_heat else "🌡 Heatmap"
            draw_button(screen, pygame.Rect(850, 160, 100, 40), btn_text, GREEN)
            draw_button(screen, pygame.Rect(850, 250, 100, 40), "🔄 Replay", ORANGE)
        
        speed_names = ["Very Slow", "Slow", "Normal", "Fast", "Very Fast"]
        screen.blit(fonts['tiny'].render(f"Speed: {speed_names[state.speed_idx]}", True, WHITE), (450, 565))
        slider_rect = pygame.Rect(450, 580, 200, 20)
        pygame.draw.rect(screen, GRAY, slider_rect, border_radius=10)
        knob_x = 450 + int(state.speed_idx / max(1, len(state.speeds)-1) * 200)
        pygame.draw.circle(screen, YELLOW, (knob_x, slider_rect.centery), 12)
        
        if state.stats:
            y = 400
            screen.blit(fonts['med'].render("📊 Statistics", True, GOLD), (845, y)); y += 30
            shortest = min(state.stats)
            longest = max(state.stats)
            avg = sum(state.stats) / len(state.stats)
            screen.blit(fonts['tiny'].render(f"Shortest: {shortest}", True, GREEN), (845, y)); y += 20
            screen.blit(fonts['tiny'].render(f"Longest: {longest}", True, RED), (845, y)); y += 20
            screen.blit(fonts['tiny'].render(f"Average: {avg:.1f}", True, BLUE), (845, y)); y += 20
            screen.blit(fonts['tiny'].render(f"Rounds: {len(state.stats)}", True, BROWN), (845, y))
        
        if not state.running and not state.meeting:
            instr = fonts['sm'].render("Press SPACE to begin! Drag speed slider. ESC=Menu", True, YELLOW)
            screen.blit(instr, instr.get_rect(center=(W//2, H-30)))
        
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Wandering in the Woods — Grades 3-5")
    play_menu()
    run_35(screen)
    pygame.quit()
