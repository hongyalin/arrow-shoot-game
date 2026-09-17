import pygame
import sys
import math

# ===================== 常量定义 =====================
WIDTH, HEIGHT = 600, 700
CELL_SIZE = 80
GRID_OFFSET_X = 60
GRID_OFFSET_Y = 100
GRID_COLS = 6
GRID_ROWS = 5

COLOR_BG = (240, 240, 240)
COLOR_GRID = (200, 200, 200)
COLOR_TEXT = (30, 30, 30)
COLOR_BLOCK = (220, 80, 80)
COLOR_OK = (60, 160, 60)
COLOR_BUTTON = (100, 140, 200)

# 方向常量：上、下、左、右
UP = 0
DOWN = 1
LEFT = 2
RIGHT = 3
DIR_OFFSET = [(0, -1), (0, 1), (-1, 0), (1, 0)]
DIR_CHAR = ["↑", "↓", "←", "→"]

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("一箭又一箭")
font = pygame.font.SysFont("simhei", 36)
small_font = pygame.font.SysFont("simhei", 24)
btn_font = pygame.font.SysFont("simhei",22)

# ===================== 关卡数据 =====================
LEVELS = [
    # 第1关
    [
        (0,0,RIGHT),
        (3,0,UP),
        (0,2,UP),
        (4,2,RIGHT)
    ],
    # 第2关
    [
        (1,1,RIGHT),
        (4,1,DOWN),
        (2,3,LEFT),
        (3,0,DOWN),
        (0,4,RIGHT)
    ],
    # 第3关
    [
        (0,0,DOWN),
        (2,1,RIGHT),
        (4,1,UP),
        (1,3,LEFT),
        (3,3,DOWN),
        (5,4,LEFT)
    ]
]

# 缓动函数 easeInOutSine：0→1平滑加速减速
def ease_in_out_sine(t):
    return -(math.cos(math.pi * t) - 1) / 2


class Arrow:
    def __init__(self, x, y, dire):
        self.x = x
        self.y = y
        self.dire = dire
        # 阻挡碰撞动画
        self.block_anim = False
        self.block_progress = 0  # 0 ~ 1
        self.block_target_dist = 0  # 碰到障碍物的像素距离
        # 飞出动画
        self.flying = False
        self.fly_time = 0
        # 动画锁定：动画播放时，不能再次点击触发动画
        self.locked = False
        # 本关是否已经扣过失误
        self.penalized = False

    def update(self):
        # 阻挡向前移动+回弹动画
        if self.block_anim:
            self.block_progress += 0.035
            if self.block_progress >= 1.0:
                self.block_anim = False
                self.block_progress = 0
                self.locked = False  # 动画结束解锁
        # 飞出动画
        if self.flying:
            self.fly_time += 1

    def draw(self, surf):
        # 网格中心点（原始位置）
        base_cx = GRID_OFFSET_X + self.x * CELL_SIZE + CELL_SIZE//2
        base_cy = GRID_OFFSET_Y + self.y * CELL_SIZE + CELL_SIZE//2
        cx, cy = base_cx, base_cy

        if self.block_anim:
            dx_dir, dy_dir = DIR_OFFSET[self.dire]
            # 前半段前进，后半段回弹，增加缓动
            if self.block_progress < 0.5:
                t = self.block_progress / 0.5
                factor = ease_in_out_sine(t)
            else:
                t = (1.0 - self.block_progress)/0.5
                factor = ease_in_out_sine(t)
            move_dist = factor * self.block_target_dist
            cx += dx_dir * move_dist
            cy += dy_dir * move_dist

        if self.flying:
            dx_dir, dy_dir = DIR_OFFSET[self.dire]
            cx += dx_dir * self.fly_time * 6
            cy += dy_dir * self.fly_time * 6

        # 颜色：阻挡动画时变红
        color = COLOR_BLOCK if self.block_anim else COLOR_TEXT
        if self.flying:
            color = COLOR_OK

        txt = font.render(DIR_CHAR[self.dire], True, color)
        rect = txt.get_rect(center=(cx, cy))
        surf.blit(txt, rect)


class Game:
    def __init__(self):
        # 新增状态：win_level 单关通关选择页
        self.state = "start"  # start / play / win_level / win / lose
        self.cur_level = 0
        self.max_mistake = 3
        self.mistake = 0
        self.arrows = []
        self.load_level(self.cur_level)

    def load_level(self, lid):
        self.arrows.clear()
        self.mistake = 0
        data = LEVELS[lid]
        for (x,y,d) in data:
            self.arrows.append(Arrow(x,y,d))

    def check_path(self, arrow:Arrow):
        """检测箭头前进方向是否有阻挡；返回 (是否可飞出, 阻挡距离像素)"""
        dx, dy = DIR_OFFSET[arrow.dire]
        cx, cy = arrow.x, arrow.y
        step_count = 0
        while True:
            cx += dx
            cy += dy
            step_count +=1
            # 到达边界，无阻挡，可以飞出
            if cx <0 or cx >= GRID_COLS or cy <0 or cy >= GRID_ROWS:
                return (True, 0)
            # 碰到其他箭头 -> 阻挡
            for a in self.arrows:
                if a == arrow: continue
                if a.x == cx and a.y == cy:
                    pixel_dist = step_count * CELL_SIZE
                    return (False, pixel_dist)

    def handle_click(self, mx, my):
        # ===== 失败界面：重新开始按钮 =====
        if self.state == "lose":
            lose_restart_btn = pygame.Rect(220, 420, 160, 50)
            if lose_restart_btn.collidepoint(mx, my):
                self.load_level(self.cur_level)
                self.state = "play"
            return

        # ===== 单关通关选择页面：下一关 / 返回主页 =====
        if self.state == "win_level":
            btn_next = pygame.Rect(80, 400, 180, 50)
            btn_home = pygame.Rect(340, 400, 180, 50)
            if btn_next.collidepoint(mx, my):
                self.cur_level += 1
                # 判断是否全部关卡通关
                if self.cur_level >= len(LEVELS):
                    self.state = "win"
                else:
                    self.load_level(self.cur_level)
                    self.state = "play"
            elif btn_home.collidepoint(mx, my):
                self.state = "start"
            return

        # 游戏界面：重新开始按钮
        restart_btn = pygame.Rect(420, 20, 130, 45)
        if restart_btn.collidepoint(mx, my):
            self.load_level(self.cur_level)
            return

        # 遍历箭头
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
                    # 被阻挡：只有本关还没罚过，才扣失误
                    arr.block_anim = True
                    arr.block_progress = 0
                    arr.block_target_dist = target_px
                    arr.locked = True
                    if not arr.penalized:
                        self.mistake +=1
                        arr.penalized = True  # 标记：本关已经罚过，永久不再扣分
                return

    def update(self):
        if self.state != "play":
            return
        # 更新所有箭头动画
        for a in self.arrows:
            a.update()
        # 移除飞出完成的箭头
        remain = []
        for a in self.arrows:
            if not (a.flying and a.fly_time > 20):
                remain.append(a)
        self.arrows = remain

        # 判断单关通关
        if len(self.arrows) == 0:
            self.state = "win_level"

        # 判断失败
        if self.mistake >= self.max_mistake:
            self.state = "lose"

    def draw(self):
        screen.fill(COLOR_BG)
        if self.state == "start":
            title = font.render("一箭又一箭", True, COLOR_TEXT)
            tip = small_font.render("点击开始游戏", True, COLOR_TEXT)
            info = small_font.render("点击箭头，前方无阻挡即可飞出", True, COLOR_TEXT)
            screen.blit(title, title.get_rect(center=(WIDTH//2, 220)))
            screen.blit(tip, tip.get_rect(center=(WIDTH//2,320)))
            screen.blit(info, info.get_rect(center=(WIDTH//2,380)))
            pygame.draw.rect(screen, COLOR_BUTTON, (220,460,160,50))
            start_txt = btn_font.render("开始游戏", True, (255,255,255))
            screen.blit(start_txt, start_txt.get_rect(center=(300,485)))

        elif self.state == "play":
            # 顶部信息
            lvl_txt = small_font.render(f"关卡：{self.cur_level+1}", True, COLOR_TEXT)
            mis_txt = small_font.render(f"失误次数：{self.mistake}/{self.max_mistake}", True, COLOR_TEXT)
            arr_txt = small_font.render(f"剩余箭头：{len(self.arrows)}", True, COLOR_TEXT)
            screen.blit(lvl_txt, (20, 20))
            screen.blit(mis_txt, (20, 50))
            screen.blit(arr_txt, (20, 80))
            # 重启按钮
            pygame.draw.rect(screen, COLOR_BUTTON, (420, 20, 130, 45))
            rst_txt = btn_font.render("重新开始", True, (255,255,255))
            screen.blit(rst_txt, rst_txt.get_rect(center=(485,42)))
            # 绘制网格
            for x in range(GRID_COLS+1):
                sx = GRID_OFFSET_X + x * CELL_SIZE
                pygame.draw.line(screen, COLOR_GRID, (sx, GRID_OFFSET_Y), (sx, GRID_OFFSET_Y + GRID_ROWS*CELL_SIZE))
            for y in range(GRID_ROWS+1):
                sy = GRID_OFFSET_Y + y * CELL_SIZE
                pygame.draw.line(screen, COLOR_GRID, (GRID_OFFSET_X, sy), (GRID_OFFSET_X + GRID_COLS*CELL_SIZE, sy))
            # 绘制箭头
            for a in self.arrows:
                a.draw(screen)

        elif self.state == "win_level":
            # 单关通关选择页面
            text = font.render(f"第{self.cur_level+1}关通关！", True, COLOR_OK)
            screen.blit(text, text.get_rect(center=(WIDTH//2,300)))
            # 两个按钮
            pygame.draw.rect(screen, COLOR_BUTTON, (80, 400, 180, 50))
            pygame.draw.rect(screen, COLOR_BUTTON, (340, 400, 180, 50))
            next_txt = btn_font.render("下一关", True, (255,255,255))
            home_txt = btn_font.render("返回主页", True, (255,255,255))
            screen.blit(next_txt, next_txt.get_rect(center=(170,425)))
            screen.blit(home_txt, home_txt.get_rect(center=(430,425)))

        elif self.state == "win":
            text = font.render("恭喜全部通关！", True, COLOR_OK)
            tip = small_font.render("全部关卡已完成", True, COLOR_TEXT)
            screen.blit(text, text.get_rect(center=(WIDTH//2,300)))
            screen.blit(tip, tip.get_rect(center=(WIDTH//2,360)))

        elif self.state == "lose":
            text = font.render("本关失败！", True, COLOR_BLOCK)
            tip = small_font.render("点击下方按钮重试本关", True, COLOR_TEXT)
            screen.blit(text, text.get_rect(center=(WIDTH//2,300)))
            screen.blit(tip, tip.get_rect(center=(WIDTH//2,360)))
            # 失败界面的重新开始按钮
            pygame.draw.rect(screen, COLOR_BUTTON, (220, 420, 160, 50))
            lose_rst_txt = btn_font.render("重新开始", True, (255,255,255))
            screen.blit(lose_rst_txt, lose_rst_txt.get_rect(center=(300,445)))
        pygame.display.flip()


game = Game()
clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = pygame.mouse.get_pos()
            if game.state == "start":
                btn_rect = pygame.Rect(220,460,160,50)
                if btn_rect.collidepoint(mx, my):
                    game.state = "play"
            else:
                game.handle_click(mx, my)
    game.update()
    game.draw()
    clock.tick(60)
