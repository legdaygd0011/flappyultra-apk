import pygame
import random
import sys
import math
import json
import os

pygame.init()
screen = pygame.display.set_mode((0, 0))
W, H = screen.get_size()
canvas = pygame.Surface((W, H))
clock = pygame.time.Clock()
u = H / 800  # масштаб под экран

font = pygame.font.SysFont(None, int(54 * u))
small = pygame.font.SysFont(None, int(40 * u))
tiny = pygame.font.SysFont(None, int(32 * u))
big = pygame.font.SysFont(None, int(110 * u))

# ================= сохранение =================
try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    BASE_DIR = os.getcwd()
SAVE_PATH = os.path.join(BASE_DIR, "flappy_save.json")
cfg = {"best": 0, "diff": 1, "theme": 3, "skin": 0, "fps": False}


def load_cfg():
    try:
        with open(SAVE_PATH) as f:
            d = json.load(f)
        for k in cfg:
            if k in d:
                cfg[k] = d[k]
    except Exception:
        pass


def save_cfg():
    try:
        with open(SAVE_PATH, "w") as f:
            json.dump(cfg, f)
    except Exception:
        pass


load_cfg()

DIFF_NAMES = ["Лёгкая", "Нормальная", "Сложная"]
DIFF_GAP = [1.16, 1.0, 0.86]
DIFF_SPEED = [0.87, 1.0, 1.13]
THEME_NAMES = ["День", "Закат", "Ночь", "Авто"]
SKIN_NAMES = ["Жёлтая", "Красная", "Синяя"]

# ================= физика =================
GROUND_H = int(110 * u)
FLOOR = H - GROUND_H
BIRD_X = W * 0.3
R = int(24 * u)
GRAVITY = 2300 * u
JUMP = -700 * u
MAX_FALL = 1100 * u
BASE_SPEED = 300 * u
PIPE_W = int(96 * u)
CAP_H = int(38 * u)
CAP_EXTRA = int(8 * u)
BASE_GAP = int(250 * u)
SPACING = int(400 * u)

cheats = {"god": False, "auto": False, "slow": False, "lowg": False, "wide": False}
CHEAT_LABELS = [
    ("god", "Бессмертие"),
    ("auto", "Автопилот"),
    ("slow", "Замедление"),
    ("lowg", "Низкая гравитация"),
    ("wide", "Широкий проход"),
]


def clamp(v, a, b):
    return max(a, min(b, v))


def lerp_c(a, b, k):
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


def shade(c, f):
    return tuple(int(clamp(v * f, 0, 255)) for v in c)


def cur_gap():
    k = DIFF_GAP[cfg["diff"]] * (1.4 if cheats["wide"] else 1.0)
    return int(BASE_GAP * k)


def cur_speed():
    return BASE_SPEED * DIFF_SPEED[cfg["diff"]]


# ================= темы =================
PAL = [
    {"top": (80, 165, 235), "bot": (205, 238, 250), "far": (150, 205, 175), "near": (105, 188, 120),
     "cloud": (255, 255, 255), "night": 0.0},
    {"top": (60, 55, 125), "bot": (255, 160, 95), "far": (150, 100, 130), "near": (95, 95, 90),
     "cloud": (255, 205, 185), "night": 0.2},
    {"top": (6, 8, 32), "bot": (36, 52, 105), "far": (30, 48, 85), "near": (22, 58, 60),
     "cloud": (75, 85, 125), "night": 1.0},
]


def make_sky(top, bot):
    s = pygame.Surface((W, H))
    for yy in range(H):
        pygame.draw.line(s, lerp_c(top, bot, clamp(yy / FLOOR, 0, 1)), (0, yy), (W, yy))
    return s


SKIES = [make_sky(p["top"], p["bot"]) for p in PAL]
STARS = [(random.randint(0, W), random.randint(0, int(FLOOR * 0.6)), random.uniform(0, 6.28),
          random.choice([1, 2])) for _ in range(70)]
clouds = [[random.randint(0, W), random.randint(int(40 * u), int(380 * u)), random.uniform(0.6, 1.4)]
          for _ in range(6)]
particles = []

# ================= предрендер труб =================


def make_pipe_surf(w, h):
    s = pygame.Surface((w, h))
    for x in range(w):
        k = x / max(1, w - 1)
        f = 0.7 + 0.65 * math.exp(-((k - 0.28) / 0.17) ** 2) - 0.25 * max(0, (k - 0.6) / 0.4)
        pygame.draw.line(s, shade((84, 180, 53), f), (x, 0), (x, h))
    return s


OUT = (28, 66, 18)
OL = max(2, int(3 * u))
PB = make_pipe_surf(PIPE_W, H)
pygame.draw.rect(PB, OUT, (0, 0, PIPE_W, H), OL)
PC = make_pipe_surf(PIPE_W + 2 * CAP_EXTRA, CAP_H)
pygame.draw.rect(PC, OUT, (0, 0, PIPE_W + 2 * CAP_EXTRA, CAP_H), OL)

# ================= предрендер земли =================
STEP = int(40 * u)
PERIOD = 2 * STEP
GRASS = int(26 * u)
tile = pygame.Surface((PERIOD, GROUND_H))
tile.fill((222, 184, 110))
for _ in range(int(40 * u)):
    pygame.draw.circle(tile, (196, 156, 88), (random.randint(0, PERIOD), random.randint(GRASS + 4, GROUND_H)),
                       random.randint(1, max(2, int(3 * u))))
pygame.draw.rect(tile, (110, 200, 60), (0, 0, PERIOD, GRASS))
pygame.draw.polygon(tile, (84, 170, 46), [(0, 0), (STEP, 0), (STEP - int(14 * u), GRASS), (-int(14 * u), GRASS)])
pygame.draw.polygon(tile, (84, 170, 46), [(PERIOD - int(14 * u), GRASS), (PERIOD, 0), (PERIOD + 1, 0),
                                          (PERIOD, GRASS)])
GROUND = pygame.Surface((W + 2 * PERIOD, GROUND_H))
for gx in range(0, W + 2 * PERIOD, PERIOD):
    GROUND.blit(tile, (gx, 0))
pygame.draw.line(GROUND, OUT, (0, 0), (W + 2 * PERIOD, 0), OL)
pygame.draw.line(GROUND, (170, 130, 70), (0, GRASS), (W + 2 * PERIOD, GRASS), OL)

# ================= птица =================
SKINS = [
    {"body": (252, 214, 40), "belly": (255, 240, 170), "wing": (236, 186, 30), "out": (190, 125, 10)},
    {"body": (230, 70, 60), "belly": (255, 205, 195), "wing": (190, 45, 45), "out": (120, 25, 25)},
    {"body": (70, 140, 235), "belly": (205, 228, 255), "wing": (45, 100, 200), "out": (25, 60, 130)},
]
WING_OFF = [-0.45, 0.0, 0.45, 0.0]
bird_cache = {}


def build_bird(skin, frame):
    key = (skin, frame)
    if key in bird_cache:
        return bird_cache[key]
    sk = SKINS[skin]
    s = int(R * 3.6)
    surf = pygame.Surface((s, s), pygame.SRCALPHA)
    c = s // 2
    ol = max(2, int(3 * u))
    # хвост
    tail = [(int(c - R * 0.8), int(c - R * 0.1)), (int(c - R * 1.7), int(c - R * 0.55)),
            (int(c - R * 1.6), int(c + R * 0.15))]
    pygame.draw.polygon(surf, sk["wing"], tail)
    pygame.draw.polygon(surf, sk["out"], tail, max(1, int(2 * u)))
    # тело
    pygame.draw.circle(surf, sk["out"], (c, c), R + ol)
    pygame.draw.circle(surf, sk["body"], (c, c), R)
    pygame.draw.ellipse(surf, sk["belly"], (int(c - R * 0.6), int(c + R * 0.1), int(R * 1.3), int(R * 0.75)))
    pygame.draw.ellipse(surf, shade(sk["body"], 1.15), (int(c - R * 0.55), int(c - R * 0.85), int(R * 0.8), int(R * 0.4)))
    # крыло
    wo = int(WING_OFF[frame] * R)
    wing = (int(c - R * 0.95), int(c + wo - R * 0.2), int(R * 1.05), int(R * 0.62))
    pygame.draw.ellipse(surf, sk["wing"], wing)
    pygame.draw.ellipse(surf, sk["out"], wing, max(1, int(2 * u)))
    # глаз
    pygame.draw.circle(surf, (255, 255, 255), (int(c + R * 0.45), int(c - R * 0.3)), int(R * 0.4))
    pygame.draw.circle(surf, (20, 20, 20), (int(c + R * 0.58), int(c - R * 0.3)), int(R * 0.19))
    pygame.draw.circle(surf, (255, 255, 255), (int(c + R * 0.63), int(c - R * 0.37)), max(1, int(R * 0.06)))
    # клюв
    pygame.draw.polygon(surf, (240, 110, 30), [(int(c + R * 0.8), int(c - R * 0.05)),
                                               (int(c + R * 1.6), int(c + R * 0.15)),
                                               (int(c + R * 0.8), int(c + R * 0.42))])
    pygame.draw.line(surf, (170, 70, 10), (int(c + R * 0.85), int(c + R * 0.17)),
                     (int(c + R * 1.5), int(c + R * 0.17)), max(1, int(2 * u)))
    bird_cache[key] = surf
    return surf


# ================= текст и кнопки =================


def render_fit(f, msg, color, maxw):
    img = f.render(msg, True, color)
    if img.get_width() > maxw:
        k = maxw / img.get_width()
        img = pygame.transform.smoothscale(img, (int(maxw), max(1, int(img.get_height() * k))))
    return img


def text(surface, f, msg, cx, y, color=(255, 255, 255), shadow=True, maxw=None):
    maxw = maxw or W * 0.92
    img = render_fit(f, msg, color, maxw)
    if shadow:
        sh = render_fit(f, msg, (0, 0, 0), maxw)
        o = max(2, int(3 * u))
        surface.blit(sh, (cx - img.get_width() / 2 + o, y + o))
    surface.blit(img, (cx - img.get_width() / 2, y))


STYLES = {
    "primary": ((255, 150, 40), (190, 100, 10)),
    "normal": ((70, 130, 200), (40, 85, 150)),
    "danger": ((210, 70, 70), (150, 40, 40)),
    "on": ((70, 180, 80), (40, 120, 50)),
    "off": ((105, 105, 120), (65, 65, 80)),
}


def draw_button(label, style, rect):
    face, edge = STYLES[style]
    d = int(7 * u)
    rad = int(16 * u)
    pygame.draw.rect(screen, edge, (rect.x, rect.y + d, rect.w, rect.h), border_radius=rad)
    pygame.draw.rect(screen, face, rect, border_radius=rad)
    pygame.draw.rect(screen, (255, 255, 255), rect, max(2, int(2 * u)), border_radius=rad)
    img = render_fit(small, label, (255, 255, 255), rect.w * 0.9)
    screen.blit(img, (rect.centerx - img.get_width() / 2, rect.centery - img.get_height() / 2))


def make_buttons(items, top=None, row=84, gap=16):
    row = int(row * u)
    gap = int(gap * u)
    bw = int(min(W * 0.82, 560 * u))
    total = len(items) * row + (len(items) - 1) * gap
    if top is None:
        top = (H - total) // 2
    x = (W - bw) // 2
    return [(i, lb, st, pygame.Rect(x, top + n * (row + gap), bw, row)) for n, (i, lb, st) in enumerate(items)]


pause_btn = pygame.Rect(W - int(80 * u), int(16 * u), int(64 * u), int(64 * u))


def current_buttons():
    if ui == "menu":
        return make_buttons([("play", "Играть", "primary"), ("settings", "Настройки", "normal"),
                             ("cheats", "Читы", "normal"), ("exit", "Выйти", "danger")], top=int(H * 0.40))
    if ui == "settings":
        items = [("diff", "Сложность: " + DIFF_NAMES[cfg["diff"]], "normal"),
                 ("theme", "Время суток: " + THEME_NAMES[cfg["theme"]], "normal"),
                 ("skin", "Птица: " + SKIN_NAMES[cfg["skin"]], "normal"),
                 ("fps", "Показ FPS: " + ("ВКЛ" if cfg["fps"] else "ВЫКЛ"), "on" if cfg["fps"] else "off"),
                 ("reset", "Сбросить рекорд", "danger"),
                 ("back_menu", "Назад", "primary")]
        return make_buttons(items, top=int(H * 0.5 - 269 * u + 40 * u), row=78, gap=14)
    if ui == "cheats":
        items = [(k, lb + ": " + ("ВКЛ" if cheats[k] else "ВЫКЛ"), "on" if cheats[k] else "off")
                 for k, lb in CHEAT_LABELS]
        items += [("score", "+10 очков", "normal"), ("back_cheats", "Назад", "primary")]
        return make_buttons(items, top=int(H * 0.5 - 274 * u + 40 * u), row=68, gap=12)
    if ui == "pause":
        return make_buttons([("resume", "Продолжить", "primary"), ("cheats", "Читы", "normal"),
                             ("home", "В меню", "danger")])
    if ui == "exit":
        return make_buttons([("exit_yes", "Да, выйти", "danger"), ("exit_no", "Отмена", "primary")],
                            top=int(H * 0.5))
    if ui == "over":
        return make_buttons([("retry", "Заново", "primary"), ("home", "Меню", "normal")],
                            top=int(H * 0.64), row=80, gap=14)
    return []


# ================= игра =================


def new_game():
    return {"y": FLOOR * 0.5, "vy": 0.0, "pipes": [], "score": 0, "scroll": 0.0, "dead_t": 0.0,
            "last_cy": FLOOR * 0.5, "cheated": False, "new_best": False, "ang": 0.0}


def add_pipe(gm):
    lo = 270 * u
    hi = FLOOR - 270 * u
    cy = clamp(gm["last_cy"] + random.randint(int(-150 * u), int(150 * u)), lo, hi)
    gm["last_cy"] = cy
    gm["pipes"].append({"x": W + 10, "cy": cy, "passed": False})


def spawn(x, y, n, colors, speed, life, size):
    for _ in range(n):
        a = random.uniform(0, 6.283)
        s = random.uniform(0.3, 1.0) * speed
        particles.append([x, y, math.cos(a) * s, math.sin(a) * s, life, life, random.choice(colors), size])


def circle_rect_hit(cx, cy, r, rect):
    nx = clamp(cx, rect[0], rect[0] + rect[2])
    ny = clamp(cy, rect[1], rect[1] + rect[3])
    return (cx - nx) ** 2 + (cy - ny) ** 2 < r * r


def pipe_rects(p):
    gap = cur_gap()
    top = p["cy"] - gap / 2
    bot = p["cy"] + gap / 2
    x = p["x"]
    return [(x, 0, PIPE_W, top - CAP_H),
            (x - CAP_EXTRA, top - CAP_H, PIPE_W + 2 * CAP_EXTRA, CAP_H),
            (x - CAP_EXTRA, bot, PIPE_W + 2 * CAP_EXTRA, CAP_H),
            (x, bot + CAP_H, PIPE_W, FLOOR - bot - CAP_H)]


def flap(gm):
    gm["vy"] = JUMP
    spawn(BIRD_X - R, gm["y"] + R * 0.5, 4, [(255, 255, 255), (230, 240, 250)], 140 * u, 0.4, 6 * u)


def autopilot(gm):
    target = FLOOR * 0.45
    for p in gm["pipes"]:
        if p["x"] + PIPE_W + CAP_EXTRA > BIRD_X - R:
            target = p["cy"] + cur_gap() * 0.22
            break
    if gm["y"] > target and gm["vy"] > 0:
        flap(gm)


# ================= рисование мира =================


def pal(key, a, b, k):
    return lerp_c(PAL[a][key], PAL[b][key], k)


def draw_celestial(which):
    if which == 0:
        cx, cy = int(W * 0.8), int(150 * u)
        pygame.draw.circle(canvas, (250, 240, 175), (cx, cy), int(95 * u))
        pygame.draw.circle(canvas, (255, 247, 200), (cx, cy), int(70 * u))
        pygame.draw.circle(canvas, (255, 252, 225), (cx, cy), int(48 * u))
    elif which == 1:
        cx, cy = int(W * 0.7), int(FLOOR - 170 * u)
        pygame.draw.circle(canvas, (255, 190, 120), (cx, cy), int(115 * u))
        pygame.draw.circle(canvas, (255, 150, 70), (cx, cy), int(80 * u))
    else:
        cx, cy = int(W * 0.78), int(150 * u)
        pygame.draw.circle(canvas, (235, 238, 250), (cx, cy), int(44 * u))
        for dx, dy, r in ((-14, -8, 9), (10, 12, 12), (12, -16, 6)):
            pygame.draw.circle(canvas, (208, 212, 232), (int(cx + dx * u), int(cy + dy * u)), int(r * u))


def draw_hills(scroll, base, a1, a2, factor, color):
    pts = [(0, FLOOR)]
    for x in range(0, W + 30, 30):
        y = FLOOR - base - a1 * math.sin((x + scroll * factor) / (130 * u)) \
            - a2 * math.sin((x + scroll * factor) / (47 * u))
        pts.append((x, y))
    pts.append((W + 30, FLOOR))
    pygame.draw.polygon(canvas, color, pts)


def draw_cloud(x, y, s, color):
    r = int(34 * u * s)
    sh = shade(color, 0.86)
    parts = ((0, 0, 1.0), (r * 0.9, -r * 0.3, 1.3), (r * 1.9, 0, 1.0), (r * 1.0, r * 0.2, 1.1))
    for dx, dy, k in parts:
        pygame.draw.circle(canvas, sh, (int(x + dx), int(y + dy + r * 0.18)), int(r * k))
    for dx, dy, k in parts:
        pygame.draw.circle(canvas, color, (int(x + dx), int(y + dy)), int(r * k))


def draw_pipe(p):
    gap = cur_gap()
    top = int(p["cy"] - gap / 2)
    bot = int(p["cy"] + gap / 2)
    x = int(p["x"])
    h = top - CAP_H
    if h > 0:
        canvas.blit(PB, (x, 0), (0, 0, PIPE_W, h))
    canvas.blit(PC, (x - CAP_EXTRA, top - CAP_H))
    canvas.blit(PC, (x - CAP_EXTRA, bot))
    bh = FLOOR - bot - CAP_H
    if bh > 0:
        canvas.blit(PB, (x, bot + CAP_H), (0, 0, PIPE_W, bh))


def draw_medal(cx, cy, score):
    r = int(40 * u)
    if score >= 30:
        col = (255, 200, 40)
    elif score >= 20:
        col = (200, 200, 210)
    elif score >= 10:
        col = (205, 127, 50)
    else:
        pygame.draw.circle(screen, (190, 175, 150), (cx, cy), r, max(2, int(3 * u)))
        return
    pygame.draw.circle(screen, shade(col, 0.6), (cx, cy), r)
    pygame.draw.circle(screen, col, (cx, cy), int(r * 0.85))
    pygame.draw.circle(screen, shade(col, 1.2), (cx, cy), int(r * 0.5), max(2, int(3 * u)))


def draw_pause_icon():
    pygame.draw.rect(screen, (40, 40, 55), pause_btn, border_radius=int(14 * u))
    pygame.draw.rect(screen, (255, 255, 255), pause_btn, max(2, int(2 * u)), border_radius=int(14 * u))
    bw = int(10 * u)
    pygame.draw.rect(screen, (255, 255, 255), (pause_btn.centerx - int(15 * u), pause_btn.y + int(16 * u), bw, int(32 * u)))
    pygame.draw.rect(screen, (255, 255, 255), (pause_btn.centerx + int(5 * u), pause_btn.y + int(16 * u), bw, int(32 * u)))


# ================= действия кнопок =================
g = new_game()
state = "ready"  # ready / play / dead
ui = "menu"      # menu / settings / cheats / pause / exit / over / None
cheat_back = "menu"


def handle(bid):
    global g, state, ui, cheat_back
    if bid in ("play", "retry"):
        g = new_game()
        state = "ready"
        ui = None
    elif bid == "settings":
        ui = "settings"
    elif bid == "cheats":
        cheat_back = ui
        ui = "cheats"
    elif bid == "exit":
        ui = "exit"
    elif bid == "exit_yes":
        save_cfg()
        pygame.quit()
        sys.exit()
    elif bid in ("exit_no", "back_menu"):
        ui = "menu"
    elif bid == "back_cheats":
        ui = cheat_back
    elif bid == "diff":
        cfg["diff"] = (cfg["diff"] + 1) % 3
        save_cfg()
    elif bid == "theme":
        cfg["theme"] = (cfg["theme"] + 1) % 4
        save_cfg()
    elif bid == "skin":
        cfg["skin"] = (cfg["skin"] + 1) % 3
        save_cfg()
    elif bid == "fps":
        cfg["fps"] = not cfg["fps"]
        save_cfg()
    elif bid == "reset":
        cfg["best"] = 0
        save_cfg()
    elif bid in cheats:
        cheats[bid] = not cheats[bid]
    elif bid == "score":
        g["score"] += 10
        g["cheated"] = True
    elif bid == "resume":
        ui = None
    elif bid == "home":
        g = new_game()
        state = "ready"
        ui = "menu"


# ================= главный цикл =================
t = 0.0
shake = 0.0


def effective_theme():
    return (g["score"] // 10) % 3 if cfg["theme"] == 3 else cfg["theme"]


theme_cur = theme_prev = effective_theme()
fade = 1.0

while True:
    raw = min(clock.tick(60) / 1000, 0.05)
    ts = 0.5 if cheats["slow"] else 1.0
    frozen = state == "play" and ui is not None
    dt = 0 if frozen else raw * ts
    t += dt

    # ---------- ввод ----------
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            save_cfg()
            pygame.quit()
            sys.exit()
        tap = False
        if e.type == pygame.MOUSEBUTTONDOWN:
            if ui is not None:
                if ui == "over" and g["dead_t"] < 0.6:
                    continue
                for bid, lb, st, rect in current_buttons():
                    if rect.collidepoint(e.pos):
                        handle(bid)
                        break
            elif state in ("ready", "play") and pause_btn.collidepoint(e.pos):
                ui = "pause"
            else:
                tap = True
        elif e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE and ui is None:
            tap = True
        if tap:
            if state == "ready":
                state = "play"
                flap(g)
            elif state == "play" and not cheats["auto"]:
                flap(g)

    # ---------- смена темы ----------
    target = effective_theme()
    if target != theme_cur:
        theme_prev, theme_cur, fade = theme_cur, target, 0.0
    fade = min(1.0, fade + raw / 1.6)

    # ---------- обновление ----------
    if dt > 0:
        for c in clouds:
            c[0] -= 30 * u * c[2] * dt
            if c[0] < -200 * u:
                c[0] = W + 100 * u
                c[1] = random.randint(int(40 * u), int(380 * u))

        if state == "ready":
            base = H * 0.28 if ui == "menu" else FLOOR * 0.5
            g["y"] = base + math.sin(t * 4) * 10 * u
            g["scroll"] += cur_speed() * 0.5 * dt

        elif state == "play":
            if any(cheats.values()):
                g["cheated"] = True
            grav = GRAVITY * (0.4 if cheats["lowg"] else 1.0)
            if cheats["auto"]:
                autopilot(g)
            g["vy"] = min(g["vy"] + grav * dt, MAX_FALL)
            g["y"] += g["vy"] * dt
            spd = cur_speed()
            g["scroll"] += spd * dt

            if not g["pipes"] or g["pipes"][-1]["x"] < W - SPACING:
                add_pipe(g)
            for p in g["pipes"]:
                p["x"] -= spd * dt
                if not p["passed"] and p["x"] + PIPE_W < BIRD_X - R:
                    p["passed"] = True
                    g["score"] += 1
            if not g["cheated"] and g["score"] > cfg["best"]:
                cfg["best"] = g["score"]
                g["new_best"] = True
            g["pipes"] = [p for p in g["pipes"] if p["x"] > -PIPE_W - 40 * u]

            if g["y"] - R < 0:
                g["y"] = R
                g["vy"] = max(g["vy"], 0)

            hit = False
            if g["y"] + R >= FLOOR:
                g["y"] = FLOOR - R
                if cheats["god"]:
                    g["vy"] = 0
                else:
                    hit = True
            if not cheats["god"]:
                for p in g["pipes"]:
                    for r in pipe_rects(p):
                        if circle_rect_hit(BIRD_X, g["y"], R * 0.85, r):
                            hit = True
            if hit:
                state = "dead"
                ui = "over"
                g["dead_t"] = 0.0
                g["vy"] = -300 * u
                shake = 0.4
                spawn(BIRD_X, g["y"], 24, [(252, 214, 40), (255, 240, 170), (240, 110, 30)], 360 * u, 0.9, 8 * u)
                save_cfg()

        elif state == "dead":
            g["dead_t"] += raw
            g["vy"] = min(g["vy"] + GRAVITY * dt, MAX_FALL)
            g["y"] += g["vy"] * dt
            if g["y"] + R > FLOOR:
                g["y"] = FLOOR - R
                g["vy"] = 0

        tgt_ang = -90 if state == "dead" else clamp(-g["vy"] / u * 0.08, -80, 28)
        g["ang"] += (tgt_ang - g["ang"]) * min(1.0, 12 * dt)

        for p in particles:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += GRAVITY * 0.3 * dt
            p[4] -= dt
        particles[:] = [p for p in particles if p[4] > 0]

    shake = max(0.0, shake - raw)

    # ---------- отрисовка мира ----------
    canvas.blit(SKIES[theme_prev] if fade < 1 else SKIES[theme_cur], (0, 0))
    if fade < 1:
        SKIES[theme_cur].set_alpha(int(255 * fade))
        canvas.blit(SKIES[theme_cur], (0, 0))
        SKIES[theme_cur].set_alpha(255)

    night = PAL[theme_prev]["night"] + (PAL[theme_cur]["night"] - PAL[theme_prev]["night"]) * fade
    if night > 0.05:
        for sx, sy, ph, sz in STARS:
            b = int(255 * min(1.0, night) * (0.6 + 0.4 * math.sin(t * 2 + ph)))
            pygame.draw.circle(canvas, (b, b, b), (sx, sy), max(1, int(sz * u)))

    draw_celestial(theme_cur if fade >= 0.5 else theme_prev)
    ccol = pal("cloud", theme_prev, theme_cur, fade)
    for c in clouds:
        draw_cloud(c[0], c[1], c[2], ccol)
    draw_hills(g["scroll"], 120 * u, 40 * u, 15 * u, 0.08, pal("far", theme_prev, theme_cur, fade))
    draw_hills(g["scroll"], 60 * u, 35 * u, 18 * u, 0.2, pal("near", theme_prev, theme_cur, fade))

    for p in g["pipes"]:
        draw_pipe(p)
    canvas.blit(GROUND, (0, FLOOR), (int(g["scroll"] % PERIOD), 0, W, GROUND_H))

    for p in particles:
        rad = max(1, int(p[7] * p[4] / p[5]))
        pygame.draw.circle(canvas, p[6], (int(p[0]), int(p[1])), rad)

    menu_bird = state == "ready" and ui == "menu"
    hide_bird = state == "ready" and ui in ("settings", "cheats", "exit")
    if not hide_bird:
        bx = W / 2 if menu_bird else BIRD_X
        frame = 1 if state == "dead" else int(t * 16) % 4
        rot = pygame.transform.rotate(build_bird(cfg["skin"], frame), g["ang"])
        canvas.blit(rot, rot.get_rect(center=(int(bx), int(g["y"]))))

    s = int(14 * u * shake / 0.4)
    ox = random.randint(-s, s) if s > 0 else 0
    oy = random.randint(-s, s) if s > 0 else 0
    screen.fill((0, 0, 0))
    screen.blit(canvas, (ox, oy))

    # ---------- интерфейс ----------
    if ui in ("settings", "cheats", "pause", "exit"):
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 160))
        screen.blit(ov, (0, 0))

    if ui not in ("menu", "settings", "cheats", "exit") or state != "ready":
        if state in ("play", "dead") or ui is None or ui == "pause":
            text(screen, big, str(g["score"]), W / 2, int(40 * u))

    if ui is None and state in ("ready", "play"):
        draw_pause_icon()
    if cfg["fps"]:
        text(screen, tiny, "FPS %d" % int(clock.get_fps()), int(70 * u), int(16 * u))
    if ui is None and any(cheats.values()):
        text(screen, tiny, "ЧИТЫ ВКЛ", int(80 * u), int(52 * u), (255, 170, 50), maxw=int(150 * u))

    if state == "ready" and ui is None:
        text(screen, font, "Тапни, чтобы лететь", W / 2, int(H * 0.62))

    btns = current_buttons()

    if ui == "menu":
        text(screen, big, "Flappy Bird", W / 2, int(H * 0.06))
        text(screen, small, "Рекорд: %d" % cfg["best"], W / 2, int(H * 0.17))
    elif btns:
        titles = {"settings": "Настройки", "cheats": "Читы", "pause": "Пауза", "exit": "Выйти из игры?"}
        if ui in titles:
            text(screen, font, titles[ui], W / 2, btns[0][3].y - int(80 * u))

    if ui == "over":
        text(screen, big, "Game Over", W / 2, int(H * 0.06))
        if g["dead_t"] > 0.4:
            cw = int(min(W * 0.88, 560 * u))
            card = pygame.Rect((W - cw) // 2, int(H * 0.2), cw, int(H * 0.38))
            pygame.draw.rect(screen, (255, 248, 225), card, border_radius=int(20 * u))
            pygame.draw.rect(screen, (90, 60, 30), card, max(3, int(4 * u)), border_radius=int(20 * u))
            draw_medal(card.x + int(cw * 0.22), card.centery - int(10 * u), g["score"])
            tx = card.x + int(cw * 0.65)
            dark = (90, 60, 30)
            text(screen, tiny, "СЧЁТ", tx, card.y + int(40 * u), dark, shadow=False, maxw=cw * 0.4)
            text(screen, font, str(g["score"]), tx, card.y + int(75 * u), (60, 40, 20), shadow=False, maxw=cw * 0.4)
            text(screen, tiny, "РЕКОРД", tx, card.y + int(150 * u), dark, shadow=False, maxw=cw * 0.4)
            text(screen, font, str(cfg["best"]), tx, card.y + int(185 * u), (60, 40, 20), shadow=False, maxw=cw * 0.4)
            if g["new_best"]:
                text(screen, tiny, "НОВЫЙ РЕКОРД!", card.centerx, card.bottom - int(48 * u), (210, 50, 50),
                     shadow=False, maxw=cw * 0.8)
            elif g["cheated"]:
                text(screen, tiny, "С читами рекорд не считается", card.centerx, card.bottom - int(48 * u),
                     (140, 100, 60), shadow=False, maxw=cw * 0.9)
            if g["dead_t"] > 0.6:
                for bid, lb, st, rect in btns:
                    draw_button(lb, st, rect)
    else:
        for bid, lb, st, rect in btns:
            draw_button(lb, st, rect)

    pygame.display.flip()
