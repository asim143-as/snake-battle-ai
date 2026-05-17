import pygame
import sys
import random
import heapq
from collections import deque


WINDOW_W, WINDOW_H = 600, 600
GRID = 20
COLS= WINDOW_W // GRID
ROWS = WINDOW_H // GRID
FPS = 7
AI_MOVE_DELAY = 2
WIN_SCORE          = 5
winner        = None

BG          = (12,  12,  20)
GRID_CLR    = (28,  28,  42)
P_HEAD      = (80,  230,  90)
P_BODY      = (45,  170,  55)
AI_HEAD     = (70,  140, 240)
AI_BODY     = (35,   85, 185)
FOOD_CLR    = (230,  55,  60)
PATH_CLR    = (255, 200,  50)
TEXT_CLR    = (220, 220, 220)
DIM_CLR     = (110, 110, 130)
PANEL_CLR   = (20,  20,  35)
WIN_CLR_P   = (80,  230,  90)
WIN_CLR_AI  = (70,  140, 240)
PANEL_H     = 50

UP    = ( 0, -1)
DOWN  = ( 0,  1)
LEFT  = (-1,  0)
RIGHT = ( 1,  0)
DIRS  = [UP, DOWN, LEFT, RIGHT]

OPPOSITE = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}


def manhattan(a: tuple, b: tuple) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(start: tuple, goal: tuple, obstacles: set) -> list:
    open_heap = []
    counter   = 0
    heapq.heappush(open_heap, (manhattan(start, goal), counter, start))

    came_from = {}
    g_score   = {start: 0}

    while open_heap:
        _, _, cur = heapq.heappop(open_heap)

        if cur == goal:
            path = []
            while cur in came_from:
                path.append(cur)
                cur = came_from[cur]
            path.reverse()
            return path

        for dx, dy in DIRS:
            nb = (cur[0] + dx, cur[1] + dy)

            if not (0 <= nb[0] < COLS and 0 <= nb[1] < ROWS):
                continue
            if nb in obstacles:
                continue

            tg = g_score[cur] + 1
            if tg < g_score.get(nb, float('inf')):
                came_from[nb] = cur
                g_score[nb]   = tg
                f              = tg + manhattan(nb, goal)
                counter       += 1
                heapq.heappush(open_heap, (f, counter, nb))

    return []


def flood_fill(start: tuple, obstacles: set) -> int:
    visited = {start}
    queue   = deque([start])
    while queue:
        cx, cy = queue.popleft()
        for dx, dy in DIRS:
            nb = (cx + dx, cy + dy)
            if (0 <= nb[0] < COLS and 0 <= nb[1] < ROWS
                    and nb not in obstacles and nb not in visited):
                visited.add(nb)
                queue.append(nb)
    return len(visited)

def ai_next_cell(ai_snake: deque, human_snake: deque, food: tuple):
    head      = ai_snake[0]

    ai_obs    = set(ai_snake)    - {ai_snake[-1]}
    human_obs = set(human_snake) - {human_snake[-1]}
    obstacles = ai_obs | human_obs

    path = astar(head, food, obstacles)
    if path:
        return path[0], path

    best, best_space = None, -1
    full_obs = set(ai_snake) | set(human_snake)
    for dx, dy in DIRS:
        nb = (head[0] + dx, head[1] + dy)
        if (0 <= nb[0] < COLS and 0 <= nb[1] < ROWS
                and nb not in full_obs):
            space = flood_fill(nb, full_obs)
            if space > best_space:
                best_space, best = space, nb
    return best, []

def spawn_food(snake1: deque, snake2: deque) -> tuple:
    occupied = set(snake1) | set(snake2)
    while True:
        pos = (random.randint(0, COLS - 1), random.randint(0, ROWS - 1))
        if pos not in occupied:
            return pos


def init_game():
    p_start  = (COLS // 4,     ROWS // 2)
    p_snake  = deque([p_start,
                      (p_start[0] - 1, p_start[1]),
                      (p_start[0] - 2, p_start[1])])
    p_dir    = RIGHT

    ai_start = (3 * COLS // 4, ROWS // 2)
    ai_snake = deque([ai_start,
                      (ai_start[0] + 1, ai_start[1]),
                      (ai_start[0] + 2, ai_start[1])])

    food     = spawn_food(p_snake, ai_snake)
    p_score  = ai_score = 0
    return p_snake, p_dir, ai_snake, food, p_score, ai_score


def grid_rect(x: int, y: int) -> pygame.Rect:
    return pygame.Rect(x * GRID, PANEL_H + y * GRID, GRID, GRID)


def draw_bg(surf: pygame.Surface) -> None:
    surf.fill(BG)
    for x in range(0, WINDOW_W, GRID):
        pygame.draw.line(surf, GRID_CLR, (x, PANEL_H), (x, WINDOW_H))
    for y in range(PANEL_H, WINDOW_H, GRID):
        pygame.draw.line(surf, GRID_CLR, (0, y), (WINDOW_W, y))


def draw_snake(surf: pygame.Surface, snake: deque,
               head_clr: tuple, body_clr: tuple) -> None:

    for i, (x, y) in enumerate(snake):
        clr  = head_clr if i == 0 else body_clr
        rect = grid_rect(x, y).inflate(-2, -2)
        pygame.draw.rect(surf, clr, rect, border_radius=5)


def draw_food(surf: pygame.Surface, food: tuple) -> None:
    r = grid_rect(*food)
    pygame.draw.circle(surf, FOOD_CLR, r.center, GRID // 2 - 2)


def draw_path(surf: pygame.Surface, path: list) -> None:
    for (px, py) in path:
        r = grid_rect(px, py)
        pygame.draw.circle(surf, PATH_CLR, r.center, GRID // 6)


def draw_panel(surf: pygame.Surface, font: pygame.font.Font,
               p_score: int, ai_score: int) -> None:
    pygame.draw.rect(surf, PANEL_CLR, (0, 0, WINDOW_W, PANEL_H))
    pygame.draw.line(surf, GRID_CLR, (0, PANEL_H), (WINDOW_W, PANEL_H), 2)

    p_lbl   = font.render(f"Player: {p_score}", True, P_HEAD)
    ai_lbl  = font.render(f"AI:     {ai_score}", True, AI_HEAD)
    win_lbl = font.render(f"First to {WIN_SCORE}", True, DIM_CLR)

    surf.blit(p_lbl,  (16,  (PANEL_H - p_lbl.get_height())  // 2))
    surf.blit(ai_lbl, (220, (PANEL_H - ai_lbl.get_height()) // 2))
    surf.blit(win_lbl, (400, (PANEL_H - win_lbl.get_height()) // 2))


def draw_end_screen(surf: pygame.Surface,
                    big: pygame.font.Font, sm: pygame.font.Font,
                    winner: str, p_score: int, ai_score: int) -> None:
    overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    surf.blit(overlay, (0, 0))

    clr  = WIN_CLR_P if winner == "Player" else WIN_CLR_AI
    txt1 = big.render(f"{winner} Wins!", True, clr)
    txt2 = sm.render(f"Player {p_score}  –  AI {ai_score}", True, TEXT_CLR)
    txt3 = sm.render("R – Restart    Q – Quit", True, DIM_CLR)

    cx, cy = WINDOW_W // 2, WINDOW_H // 2
    surf.blit(txt1, txt1.get_rect(center=(cx, cy - 55)))
    surf.blit(txt2, txt2.get_rect(center=(cx, cy + 5)))
    surf.blit(txt3, txt3.get_rect(center=(cx, cy + 55)))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("Snake Battle  –  Human vs AI")
    clock  = pygame.time.Clock()

    big_font  = pygame.font.SysFont("consolas", 52, bold=True)
    med_font  = pygame.font.SysFont("consolas", 26)
    sm_font   = pygame.font.SysFont("consolas", 20)

    (p_snake, p_dir,
     ai_snake, food,
     p_score, ai_score) = init_game()

    pending_p_dir = p_dir
    ai_path       = []
    winner        = None
    ai_move_counter = 0

    while True:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()

                if event.key == pygame.K_r and winner:
                    (p_snake, p_dir,
                     ai_snake, food,
                     p_score, ai_score) = init_game()
                    pending_p_dir = p_dir
                    ai_path       = []
                    winner        = None
                    continue

                if not winner:
                    key_map = {
                        pygame.K_UP:    UP,
                        pygame.K_DOWN:  DOWN,
                        pygame.K_LEFT:  LEFT,
                        pygame.K_RIGHT: RIGHT,
                    }
                    new_dir = key_map.get(event.key)
                    if new_dir and new_dir != OPPOSITE.get(p_dir):
                        pending_p_dir = new_dir

        if winner:
            draw_bg(screen)
            draw_path(screen, ai_path)
            draw_food(screen, food)
            draw_snake(screen, p_snake,  P_HEAD,  P_BODY)
            draw_snake(screen, ai_snake, AI_HEAD, AI_BODY)
            draw_panel(screen, sm_font, p_score, ai_score)
            draw_end_screen(screen, big_font, med_font, winner, p_score, ai_score)
            pygame.display.flip()
            clock.tick(FPS)
            continue

        ai_next, ai_path = ai_next_cell(ai_snake, p_snake, food)

        p_dir  = pending_p_dir
        p_head = (p_snake[0][0] + p_dir[0],
                  p_snake[0][1] + p_dir[1])
        p_snake.appendleft(p_head)
        p_ate  = (p_head == food)
        if not p_ate:
            p_snake.pop()

        ai_ate = False
        ai_move_counter += 1
        if ai_move_counter >= AI_MOVE_DELAY:
            ai_move_counter = 0
            if ai_next:
                ai_snake.appendleft(ai_next)
                ai_ate = (ai_next == food)
            if not ai_ate:
                ai_snake.pop()

        def is_dead(snake: deque, other: deque) -> bool:
            head = snake[0]
            if not (0 <= head[0] < COLS and 0 <= head[1] < ROWS):
                return True
            if head in list(snake)[1:]:
                return True
            if head in set(other):
                return True
            return False

        p_dead  = is_dead(p_snake,  ai_snake)
        ai_dead = is_dead(ai_snake, p_snake) or (ai_next is None)

        if p_dead and ai_dead:
            winner = "Nobody – it's a draw!"
        elif p_dead:
            winner = "AI"
        elif ai_dead:
            winner = "Player"

        if not winner:
            if p_ate:
                p_score += 1
                food     = spawn_food(p_snake, ai_snake)
                ai_path  = []
            elif ai_ate:
                ai_score += 1
                food      = spawn_food(p_snake, ai_snake)
                ai_path   = []

            if p_score  >= WIN_SCORE:
                winner = "Player"
            elif ai_score >= WIN_SCORE:
                winner = "AI"

        draw_bg(screen)
        if ai_path:
            draw_path(screen, ai_path[1:])
        draw_food(screen, food)
        draw_snake(screen, p_snake,  P_HEAD,  P_BODY)
        draw_snake(screen, ai_snake, AI_HEAD, AI_BODY)
        draw_panel(screen, sm_font, p_score, ai_score)

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
