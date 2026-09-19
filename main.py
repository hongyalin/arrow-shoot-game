import pygame
import sys
import math
import time

# ===================== 全局常量定义 =====================
WIDTH, HEIGHT = 600, 700
CELL_SIZE = 80
GRID_OFFSET_X = 60
GRID_OFFSET_Y = 100
GRID_COLS = 6
GRID_ROWS = 5

COLOR_BG = (245, 247, 250)
COLOR_GRID = (180, 190, 210)
COLOR_GRID_CELL = (255, 255, 255)
COLOR_TEXT = (35, 45, 65)
COLOR_BLOCK = (230, 70, 70)
COLOR_OK = (50, 160, 90)
COLOR_BUTTON = (72, 130, 220)
COLOR_BUTTON_HOVER = (90, 150, 240)
COLOR_BUTTON_DISABLE = (160,160,160)
COLOR_PANEL = (255, 255, 255)
COLOR_SHADOW = (0, 0, 0, 40)
COLOR_HINT = (255,180,0) # 提示高亮颜色

UP = 0
DOWN = 1
LEFT = 2
RIGHT = 3
DIR_OFFSET = [(0, -1), (0, 1), (-1, 0), (1, 0)]
DIR_CHAR = ["↑", "↓", "←", "→"]

# ========== 关卡数据 ==========
LEVELS = [
    [
        (3,0,DOWN),
        (5,1,LEFT),
        (1,2,RIGHT),
        (0,3,RIGHT),
        (4,3,UP),
        (2,4,RIGHT)
    ],
    [
        (5,0,LEFT),
        (2,1,DOWN),
        (4,1,LEFT),
        (1,2,DOWN),
        (3,2,UP),
        (0,3,RIGHT),
        (5,3,UP)
    ],
    [
        (2,0,DOWN),
        (4,0,LEFT),
        (1,1,RIGHT),
        (5,1,UP),
        (0,2,RIGHT),
        (3,2,DOWN),
        (1,3,UP),
        (4,3,LEFT)
    ]
]

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("一箭又一箭")

home_bg_img = pygame.image.load("home_bg.png").convert_alpha()
home_bg_img = pygame.transform.scale(home_bg_img, (WIDTH, HEIGHT))

level_bg_img = pygame.image.load("level_bg.png").convert_alpha()
level_bg_img = pygame.transform.scale(level_bg_img, (WIDTH, HEIGHT))

success_bg_img = pygame.image.load("success_bg.png").convert_alpha()
success_bg_img = pygame.transform.scale(success_bg_img, (WIDTH, HEIGHT))

fail_bg_img = pygame.image.load("fail_bg.png").convert_alpha()
fail_bg_img = pygame.transform.scale(fail_bg_img, (WIDTH, HEIGHT))


font_big = pygame.font.SysFont("simhei", 42)
font_title = pygame.font.SysFont("simhei", 56)
font_normal = pygame.font.SysFont("simhei", 28)
font_small = pygame.font.SysFont("simhei", 24)
font_btn = pygame.font.SysFont("simhei", 24)

# ===================== 工具函数 =====================
def ease_in_out_sine(t):
    return -(math.cos(math.pi * t) - 1) / 2

def sec_to_mmss(total_sec):
    """将秒数转为 MM:SS 字符串，只保留整数秒"""
    s = int(total_sec)
    minute = s // 60
    sec = s % 60
    return f"{minute:02d}:{sec:02d}"

def draw_shadow_rect(surf, rect, color, radius=10):
    shadow = pygame.Surface(rect.size, pygame.SRCALPHA)
    shadow.fill(COLOR_SHADOW)
    surf.blit(shadow, (rect.x + 4, rect.y + 4))
    pygame.draw.rect(surf, color, rect, border_radius=radius)

def draw_heart(surf, x, y, size, filled):
    """绘制单颗红心，filled=True为满血，False为空心"""
    color = (230, 70, 70) if filled else (200, 200, 200)
    cx, cy = x + size // 2, y + size // 2
    r = size // 4

    pygame.draw.circle(surf, color, (cx - r // 2, cy - r // 4), r)
    pygame.draw.circle(surf, color, (cx + r // 2, cy - r // 4), r)

    tip = [
        (cx, cy + size // 3),
        (cx - size // 2, cy),
        (cx + size // 2, cy)
    ]
    pygame.draw.polygon(surf, color, tip)

def draw_hearts(surf, x, y, total, remain, size=24, gap=6):
    """连续绘制红心血条"""
    for i in range(total):
        draw_heart(surf, x + i * (size + gap), y, size, i < remain)

# ===================== Arrow =====================
class Arrow:
    def __init__(self, x, y, dire):
        self.x = x
        self.y = y
        self.dire = dire

        self.block_anim = False
        self.block_progress = 0.0
        self.block_target_dist = 0

        self.flying = False
        self.fly_progress = 0.0

        self.locked = False
        self.penalized = False
        self.hint_highlight = False # 是否提示高亮

    def update(self):
        if self.block_anim:
            self.block_progress += 0.04
            if self.block_progress >= 1.0:
                self.block_anim = False
                self.block_progress = 0.0
                self.locked = False

        if self.flying:
            self.fly_progress += 0.08

    def draw(self, surf):
        base_cx = GRID_OFFSET_X + self.x * CELL_SIZE + CELL_SIZE // 2
        base_cy = GRID_OFFSET_Y + self.y * CELL_SIZE + CELL_SIZE // 2
        cx, cy = base_cx, base_cy

        if self.block_anim:
            dx_dir, dy_dir = DIR_OFFSET[self.dire]
            if self.block_progress < 0.5:
                t = self.block_progress / 0.5
                factor = ease_in_out_sine(t)
            else:
                t = (1.0 - self.block_progress) / 0.5
                factor = ease_in_out_sine(t)
            move_dist = factor * self.block_target_dist
            cx += dx_dir * move_dist
            cy += dy_dir * move_dist

        if self.flying:
            dx_dir, dy_dir = DIR_OFFSET[self.dire]
            cx += dx_dir * self.fly_progress * CELL_SIZE * 1.4
            cy += dy_dir * self.fly_progress * CELL_SIZE * 1.4

        if self.block_anim:
            color = COLOR_BLOCK
        elif self.flying:
            color = COLOR_OK
        elif self.hint_highlight:
            # 闪烁效果
            if int(time.time()*8) % 2 == 0:
                color = COLOR_HINT
            else:
                color = COLOR_TEXT
        else:
            color = COLOR_TEXT

        txt = font_normal.render(DIR_CHAR[self.dire], True, color)
        rect = txt.get_rect(center=(cx, cy))
        surf.blit(txt, rect)

# ===================== Button =====================
class Button:
    def __init__(self, x, y, w, h, text, callback):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.hover = False
        self.disabled = False

    def handle_event(self, event):
        if self.disabled:
            return False
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()
                return True
        return False

    def draw(self, surf):
        if self.disabled:
            color = COLOR_BUTTON_DISABLE
        else:
            color = COLOR_BUTTON_HOVER if self.hover else COLOR_BUTTON
        draw_shadow_rect(surf, self.rect, color, radius=12)
        txt = font_btn.render(self.text, True, (255, 255, 255))
        txt_rect = txt.get_rect(center=self.rect.center)
        surf.blit(txt, txt_rect)

# ===================== Game =====================
class Game:
    def __init__(self):
        self.state = "start"
        self.cur_level = 0
        self.max_mistake = 3
        self.mistake = 0
        self.arrows = []

        self.start_time = 0.0
        self.elapsed_time = 0.0
        self.is_timing = False

        self.hint_count = 2
        self.hint_end_time = 0.0
        self.all_clear = False
        self.load_level(self.cur_level)

        self.btn_start = Button(220, 460, 160, 50, "开始游戏", self._start_game)
        self.btn_restart = Button(420, 20, 130, 45, "重新开始", lambda: self.load_level(self.cur_level))

        # 锦囊提示按钮：放在网格右下角
        self.btn_hint = Button(
            GRID_OFFSET_X + GRID_COLS * CELL_SIZE - 70,
            GRID_OFFSET_Y + GRID_ROWS * CELL_SIZE + 10,
            60, 60,
            "",
            self.do_hint
        )

        self.btn_next = Button(140, 340, 120, 50, "下一关", self._on_next_level)
        self.btn_home = Button(340, 340, 120, 50, "返回主页", lambda: self.goto_home())
        self.btn_restart_lose = Button(240, 380, 120, 50, "重新开始", self._retry_lose)
        self.btn_home_win = Button(240, 380, 120, 50, "返回主页", lambda: self.goto_home())

        self.btn_reset_all = Button(140, 340, 120, 50, "重置进度", self._reset_all_progress)
        self.btn_back_home = Button(340, 340, 120, 50, "返回主页", lambda: self.goto_home())

    def goto_home(self):
        self.state = "start"
        self.is_timing = False

    def _start_game(self):
        # 判断是否已经全部通关
        if self.all_clear:
            self.state = "all_clear_tip"  # 新状态：全部通关提示页
            return
        # 未通关，正常开局
        self.cur_level = 0
        self.load_level(self.cur_level)
        self.state = "play"
        self.start_time = time.time()
        self.is_timing = True

    def _retry_lose(self):
        self.load_level(self.cur_level)
        self.state = "play"
        self.start_time = time.time()
        self.is_timing = True

    def _on_next_level(self):
        self.cur_level += 1
        if self.cur_level >= len(LEVELS):
            self.state = "win"
            self.is_timing = False
            self.all_clear = True  # 全部通关，标记置True
        else:
            self.load_level(self.cur_level)
            self.state = "play"
            self.start_time = time.time()
            self.is_timing = True

    def load_level(self, lid):
        self.arrows.clear()
        self.mistake = 0
        self.elapsed_time = 0.0
        self.is_timing = False
        self.hint_count = 2
        self.hint_end_time = 0.0
        for (x, y, d) in LEVELS[lid]:
            self.arrows.append(Arrow(x, y, d))

    def check_path(self, arrow):
        dx, dy = DIR_OFFSET[arrow.dire]
        cx, cy = arrow.x, arrow.y

        while True:
            cx += dx
            cy += dy
            if cx < 0 or cx >= GRID_COLS or cy < 0 or cy >= GRID_ROWS:
                return True, 0
            for a in self.arrows:
                if a == arrow:
                    continue
                if a.x == cx and a.y == cy:
                    return False, math.hypot((cx - arrow.x) * CELL_SIZE, (cy - arrow.y) * CELL_SIZE)

    def do_hint(self):
        if self.hint_count <= 0:
            return
        if time.time() < self.hint_end_time:
            return

        for a in self.arrows:
            a.hint_highlight = False

        target_arrow = None
        for a in self.arrows:
            if a.locked:
                continue
            ok, _ = self.check_path(a)
            if ok:
                target_arrow = a
                break

        if target_arrow is not None:
            target_arrow.hint_highlight = True
            self.hint_count -= 1
            self.hint_end_time = time.time() + 1.5

    def handle_click_grid(self, mx, my):
        if self.state != "play":
            return

        if self.btn_restart.rect.collidepoint(mx, my):
            self.load_level(self.cur_level)
            self.state = "play"
            self.start_time = time.time()
            self.is_timing = True
            return

        if self.btn_hint.rect.collidepoint(mx, my):
            return

        for arr in self.arrows:
            if arr.locked:
                continue
            gx = GRID_OFFSET_X + arr.x * CELL_SIZE
            gy = GRID_OFFSET_Y + arr.y * CELL_SIZE
            rect = pygame.Rect(gx, gy, CELL_SIZE, CELL_SIZE)
            if rect.collidepoint(mx, my):
                can_fly, target_px = self.check_path(arr)
                if can_fly:
                    arr.flying = True
                else:
                    arr.block_anim = True
                    arr.block_progress = 0.0
                    arr.block_target_dist = target_px
                    arr.locked = True
                    if not arr.penalized:
                        self.mistake += 1
                        arr.penalized = True
                return

    def update(self):
        if self.state != "play":
            return
        if self.is_timing:
            self.elapsed_time = time.time() - self.start_time

        if time.time() > self.hint_end_time:
            for a in self.arrows:
                a.hint_highlight = False

        for a in self.arrows:
            a.update()
        self.arrows = [a for a in self.arrows if not (a.flying and a.fly_progress >= 1.0)]

        if len(self.arrows) == 0:
            self.state = "win_level"
            self.is_timing = False
        if self.mistake >= self.max_mistake:
            self.state = "lose"
            self.is_timing = False

    def _reset_all_progress(self):
        self.all_clear = False
        self.cur_level = 0
        self.load_level(self.cur_level)
        self.state = "play"
        self.start_time = time.time()
        self.is_timing = True

    def draw(self):
        screen.fill(COLOR_BG)
        if self.state == "start":
            screen.blit(home_bg_img, (0, 0))

            title = font_title.render("一箭又一箭", True, COLOR_TEXT)
            tip = font_small.render("点击开始游戏", True, COLOR_TEXT)
            info = font_small.render("点击箭头，前方无阻挡即可飞出", True, COLOR_TEXT)
            screen.blit(title, title.get_rect(center=(WIDTH // 2, 220)))
            screen.blit(tip, tip.get_rect(center=(WIDTH // 2, 320)))
            screen.blit(info, info.get_rect(center=(WIDTH // 2, 380)))
            self.btn_start.draw(screen)

        elif self.state == "all_clear_tip":
            panel = pygame.Rect(120, 180, 360, 340)
            pygame.draw.rect(screen, COLOR_PANEL, panel, border_radius=16)
            pygame.draw.rect(screen, COLOR_GRID, panel, 3, border_radius=16)
            text = font_big.render("您已完成全部关卡！", True, COLOR_OK)
            tip = font_small.render("是否重置进度，重新挑战？", True, COLOR_TEXT)
            screen.blit(text, text.get_rect(center=(WIDTH // 2, 240)))
            screen.blit(tip, tip.get_rect(center=(WIDTH // 2, 290)))
            # 两个按钮：重置 / 返回主页
            self.btn_reset_all = Button(140, 340, 120, 50, "重置进度", self._reset_all_progress)
            self.btn_back_home = Button(340, 340, 120, 50, "返回主页", lambda: self.goto_home())
            self.btn_reset_all.draw(screen)
            self.btn_back_home.draw(screen)


        elif self.state == "play":
            screen.blit(level_bg_img, (0, 0))
            lvl_txt = font_small.render(f"关卡：{self.cur_level + 1}/{len(LEVELS)}", True, COLOR_TEXT)
            arr_txt = font_small.render(f"剩余箭头：{len(self.arrows)}", True, COLOR_TEXT)
            screen.blit(lvl_txt, (20, 20))
            screen.blit(arr_txt, (20, 50))

            grid_center_x = GRID_OFFSET_X + (GRID_COLS * CELL_SIZE) // 2

            # 计时放在红心上方
            time_str = sec_to_mmss(self.elapsed_time)
            time_txt = font_small.render(f"用时：{time_str}", True, COLOR_TEXT)
            time_rect = time_txt.get_rect(center=(grid_center_x, GRID_OFFSET_Y - 70))
            screen.blit(time_txt, time_rect)

            # 红心放在计时下方
            heart_total_width = 3 * 24 + 2 * 6
            heart_start_x = grid_center_x - heart_total_width // 2
            heart_y = GRID_OFFSET_Y - 42
            draw_hearts(screen, heart_start_x, heart_y, self.max_mistake, self.max_mistake - self.mistake, size=24, gap=6)

            self.btn_restart.draw(screen)

            # 绘制网格
            for x in range(GRID_COLS + 1):
                sx = GRID_OFFSET_X + x * CELL_SIZE
                pygame.draw.line(screen, COLOR_GRID, (sx, GRID_OFFSET_Y),
                                 (sx, GRID_OFFSET_Y + GRID_ROWS * CELL_SIZE), 2)
            for y in range(GRID_ROWS + 1):
                sy = GRID_OFFSET_Y + y * CELL_SIZE
                pygame.draw.line(screen, COLOR_GRID, (GRID_OFFSET_X, sy),
                                 (GRID_OFFSET_X + GRID_COLS * CELL_SIZE, sy), 2)
            for x in range(GRID_COLS):
                for y in range(GRID_ROWS):
                    rect = pygame.Rect(
                        GRID_OFFSET_X + x * CELL_SIZE + 2,
                        GRID_OFFSET_Y + y * CELL_SIZE + 2,
                        CELL_SIZE - 4,
                        CELL_SIZE - 4
                    )
                    pygame.draw.rect(screen, COLOR_GRID_CELL, rect, border_radius=6)

            for a in self.arrows:
                a.draw(screen)

            # 锦囊提示按钮
            self.btn_hint.disabled = (self.hint_count <= 0)
            self._draw_hint_button()

        elif self.state == "win_level":
            screen.blit(success_bg_img, (0, 0))
            panel = pygame.Rect(120, 180, 360, 340)
            pygame.draw.rect(screen, COLOR_PANEL, panel, border_radius=16)
            pygame.draw.rect(screen, COLOR_GRID, panel, 3, border_radius=16)
            text = font_big.render(f"第{self.cur_level + 1}关通关！", True, COLOR_OK)
            time_str = sec_to_mmss(self.elapsed_time)
            time_info = font_small.render(f"本关用时：{time_str}", True, COLOR_TEXT)
            screen.blit(text, text.get_rect(center=(WIDTH // 2, 240)))
            screen.blit(time_info, time_info.get_rect(center=(WIDTH // 2, 290)))
            self.btn_next.draw(screen)
            self.btn_home.draw(screen)

        elif self.state == "win":
            screen.blit(success_bg_img, (0, 0))
            panel = pygame.Rect(120, 180, 360, 340)
            pygame.draw.rect(screen, COLOR_PANEL, panel, border_radius=16)
            pygame.draw.rect(screen, COLOR_GRID, panel, 3, border_radius=16)
            text = font_big.render("恭喜全部通关！", True, COLOR_OK)
            tip = font_small.render("你完成全部3个关卡", True, COLOR_TEXT)
            screen.blit(text, text.get_rect(center=(WIDTH // 2, 260)))
            screen.blit(tip, tip.get_rect(center=(WIDTH // 2, 320)))
            self.btn_home_win.draw(screen)

        elif self.state == "lose":
            screen.blit(fail_bg_img, (0, 0))
            panel = pygame.Rect(120, 180, 360, 340)
            pygame.draw.rect(screen, COLOR_PANEL, panel, border_radius=16)
            pygame.draw.rect(screen, COLOR_GRID, panel, 3, border_radius=16)
            text = font_big.render("本关失败！", True, COLOR_BLOCK)
            tip = font_small.render("点击下方按钮重试", True, COLOR_TEXT)
            screen.blit(text, text.get_rect(center=(WIDTH // 2, 260)))
            screen.blit(tip, tip.get_rect(center=(WIDTH // 2, 320)))
            self.btn_restart_lose.draw(screen)

        pygame.display.flip()

    def _draw_hint_button(self):
        """绘制灯泡图标按钮，并在右上角显示剩余提示次数"""
        btn = self.btn_hint
        color = COLOR_BUTTON_HOVER if btn.hover else COLOR_BUTTON
        if btn.disabled:
            color = COLOR_BUTTON_DISABLE

        draw_shadow_rect(screen, btn.rect, color, radius=14)

        cx = btn.rect.centerx
        cy = btn.rect.centery

        if btn.disabled:
            # 禁用态：灰色灯泡
            bulb_color = (230, 230, 230)
            base_color = (170, 170, 170)
        else:
            # 可用态：黄色发光灯泡
            bulb_color = (255, 230, 120)
            base_color = (255, 200, 60)

            # 外圈柔光
            pygame.draw.circle(screen, (255, 245, 180), (cx, cy - 4), 24)

        # 灯泡主体
        pygame.draw.circle(screen, bulb_color, (cx, cy - 4), 18)
        pygame.draw.circle(screen, base_color, (cx, cy - 4), 18, 2)

        # 灯泡高光
        pygame.draw.circle(screen, (255, 255, 255), (cx - 6, cy - 10), 4)

        # 灯座
        pygame.draw.rect(screen, base_color, (cx - 6, cy + 10, 12, 6), border_radius=2)
        pygame.draw.rect(screen, base_color, (cx - 5, cy + 16, 10, 4), border_radius=2)

        # 次数角标
        badge_radius = 12
        badge_x = btn.rect.right - 8
        badge_y = btn.rect.top + 8
        pygame.draw.circle(screen, (230, 70, 70), (badge_x, badge_y), badge_radius)
        pygame.draw.circle(screen, (255, 255, 255), (badge_x, badge_y), badge_radius, 2)
        num_txt = font_btn.render(str(self.hint_count), True, (255, 255, 255))
        num_rect = num_txt.get_rect(center=(badge_x, badge_y))
        screen.blit(num_txt, num_rect)


# ===================== main loop =====================
if __name__ == "__main__":
    game = Game()
    clock = pygame.time.Clock()

    while True:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if game.state == "start":
                game.btn_start.handle_event(event)
            elif game.state == "play":
                game.btn_restart.handle_event(event)
                game.btn_hint.handle_event(event)
            elif game.state == "win_level":
                game.btn_next.handle_event(event)
                game.btn_home.handle_event(event)
            elif game.state == "win":
                game.btn_home_win.handle_event(event)
            elif game.state == "lose":
                game.btn_restart_lose.handle_event(event)
            elif game.state == "all_clear_tip":
                game.btn_reset_all.handle_event(event)
                game.btn_back_home.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                game.handle_click_grid(mx, my)

        game.update()
        game.draw()
        clock.tick(60)
