# main.py
import pygame
import sys
import numpy as np
import math
import os
from ai_model import train_initial_model

# ================= 游戏配置 =================
WIDTH, HEIGHT = 800, 600
FPS = 60
WIN_SCORE = 5

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
GRAY = (100, 100, 100)
GREEN = (50, 220, 50)
RED = (220, 50, 50)

# ================= 声音合成 =================
class DummySound:
    def play(self): pass

def create_beep_sound(frequency, duration=0.1):
    """使用 Numpy 动态合成基础波形，免去了附带 wav 文件的烦恼"""
    try:
        sample_rate = 44100
        n_samples = int(round(duration * sample_rate))
        buf = np.zeros((n_samples, 2), dtype=np.int16)
        max_amplitude = 2**14 - 1
        for s in range(n_samples):
            t = float(s) / sample_rate
            val = int(round(max_amplitude * math.sin(2 * math.pi * frequency * t)))
            buf[s][0] = val # 左声道
            buf[s][1] = val # 右声道
        return pygame.sndarray.make_sound(buf)
    except Exception:
        return DummySound() # 如果没装 numpy 等环境，静音运行

# ================= 实体类 =================
class Paddle:
    def __init__(self, x, y):
        self.width = 15
        self.height = 100
        self.x = x
        self.y = y
        self.speed = 7
        self.score = 0

    def move(self, up):
        if up:
            self.y -= self.speed
        else:
            self.y += self.speed
        # 边界控制
        self.y = max(0, min(self.y, HEIGHT - self.height))

    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, (self.x, self.y, self.width, self.height), border_radius=5)

    def center_y(self):
        return self.y + self.height / 2

class Ball:
    def __init__(self):
        self.size = 15
        self.reset()
        self.max_speed = 12

    def reset(self):
        self.x = WIDTH // 2 - self.size // 2
        self.y = HEIGHT // 2 - self.size // 2
        # 随机初始方向
        self.vx = 5 if np.random.rand() > 0.5 else -5
        self.vy = np.random.uniform(-4, 4)

    def move(self):
        self.x += self.vx
        self.y += self.vy

    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, (self.x, self.y, self.size, self.size), border_radius=self.size//2)

# ================= 辅助函数 =================
def get_chinese_font(size):
    """直接读取系统底层的中文字体文件，彻底解决方块乱码"""
    # Windows 默认的微软雅黑和黑体路径
    win_font_1 = "C:/Windows/Fonts/msyh.ttc"
    win_font_2 = "C:/Windows/Fonts/simhei.ttf"
    
    if os.path.exists(win_font_1):
        return pygame.font.Font(win_font_1, size)
    elif os.path.exists(win_font_2):
        return pygame.font.Font(win_font_2, size)
    else:
        # 如果实在找不到，再使用系统默认回退
        return pygame.font.SysFont("SimHei", size)

# ================= 核心主循环 =================
def main():
    # 预加载与预训练 AI
    ai_model = train_initial_model()

    # 初始化 Pygame
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    pygame.key.stop_text_input()  # 新增本行：强行禁止系统输入法在这个窗口弹出来
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Created by Mio - PyTorch版")
    clock = pygame.time.Clock()

    # 字体加载
    font_large = get_chinese_font(64)
    font_small = get_chinese_font(24)

    # 音效生成
    sound_hit = create_beep_sound(600, 0.05)
    sound_score = create_beep_sound(300, 0.3)

    # 实例化对象
    player = Paddle(30, HEIGHT // 2 - 50)
    ai_paddle = Paddle(WIDTH - 45, HEIGHT // 2 - 50)
    ball = Ball()

    # 游戏状态控制
    state = "PLAYING" # PLAYING, PAUSED, GAMEOVER
    winner_text = ""

    running = True
    while running:
        # 1. 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_p and state != "GAMEOVER":
                    state = "PAUSED" if state == "PLAYING" else "PLAYING"
                elif event.key == pygame.K_r:
                    # 重置游戏
                    player.score = 0
                    ai_paddle.score = 0
                    ball.reset()
                    state = "PLAYING"

        if state == "PLAYING":
            # 2. 玩家控制 (W / S 或 上 / 下)
            keys = pygame.key.get_pressed()
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                player.move(up=True)
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                player.move(up=False)

            # 3. PyTorch AI 实时推理
            # 提取并归一化特征
            state_vector =[
                ball.x / WIDTH,
                ball.y / HEIGHT,
                ball.vx / ball.max_speed,
                ball.vy / ball.max_speed,
                player.center_y() / HEIGHT,
                ai_paddle.center_y() / HEIGHT
            ]
            action = ai_model.predict(state_vector)
            
            # AI 动作执行: 0 为上，1 为下
            if action == 0:
                ai_paddle.move(up=True)
            elif action == 1:
                ai_paddle.move(up=False)

            # 4. 更新球与物理碰撞
            ball.move()

            # 上下墙壁碰撞
            if ball.y <= 0 or ball.y >= HEIGHT - ball.size:
                ball.vy = -ball.vy
                sound_hit.play()

            # 挡板碰撞检测
            ball_rect = pygame.Rect(ball.x, ball.y, ball.size, ball.size)
            player_rect = pygame.Rect(player.x, player.y, player.width, player.height)
            ai_rect = pygame.Rect(ai_paddle.x, ai_paddle.y, ai_paddle.width, ai_paddle.height)

            if ball_rect.colliderect(player_rect) and ball.vx < 0:
                ball.vx = -ball.vx * 1.1 # 稍微加速
                ball.vy += (ball.y - player.center_y()) * 0.05 # 击球位置影响角度
                sound_hit.play()
            
            if ball_rect.colliderect(ai_rect) and ball.vx > 0:
                ball.vx = -ball.vx * 1.1
                ball.vy += (ball.y - ai_paddle.center_y()) * 0.05
                sound_hit.play()

            # 速度上限限制
            ball.vx = max(min(ball.vx, ball.max_speed), -ball.max_speed)
            ball.vy = max(min(ball.vy, ball.max_speed), -ball.max_speed)

            # 5. 得分判定
            if ball.x < 0:
                ai_paddle.score += 1
                sound_score.play()
                ball.reset()
            elif ball.x > WIDTH:
                player.score += 1
                sound_score.play()
                ball.reset()

            # 胜负判定
            if player.score >= WIN_SCORE:
                state = "GAMEOVER"
                winner_text = "玩家 获胜！"
            elif ai_paddle.score >= WIN_SCORE:
                state = "GAMEOVER"
                winner_text = "人机 获胜！"

        # 6. 渲染画面
        screen.fill(BLACK)
        
        # 绘制中线
        pygame.draw.aaline(screen, GRAY, (WIDTH//2, 0), (WIDTH//2, HEIGHT))

        # 绘制实体
        player.draw(screen)
        ai_paddle.draw(screen)
        ball.draw(screen)

        # 绘制分数
        score_p1 = font_large.render(str(player.score), True, WHITE)
        score_p2 = font_large.render(str(ai_paddle.score), True, WHITE)
        screen.blit(score_p1, (WIDTH // 4 - score_p1.get_width()//2, 50))
        screen.blit(score_p2, (WIDTH * 3 // 4 - score_p2.get_width()//2, 50))

        # 底部说明
        ai_tag = font_small.render("Created by Mio ", True, GREEN)
        screen.blit(ai_tag, (WIDTH - ai_tag.get_width() - 20, HEIGHT - 40))
        controls_text = font_small.render("操作: W/S移动 | P暂停 | R重玩 | ESC退出", True, GRAY)
        screen.blit(controls_text, (20, HEIGHT - 40))

        # 状态文本渲染
        if state == "PAUSED":
            pause_text = font_large.render("已暂停 (按P继续)", True, WHITE)
            screen.blit(pause_text, (WIDTH//2 - pause_text.get_width()//2, HEIGHT//2 - 50))
        
        elif state == "GAMEOVER":
            over_text = font_large.render(winner_text, True, RED if "AI" in winner_text else GREEN)
            hint_text = font_small.render("按 R 键重新开始，ESC 退出", True, WHITE)
            screen.blit(over_text, (WIDTH//2 - over_text.get_width()//2, HEIGHT//2 - 60))
            screen.blit(hint_text, (WIDTH//2 - hint_text.get_width()//2, HEIGHT//2 + 20))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()