import cv2 as cv
import mediapipe as mp
import random
import math
import time
import pygame

# ---------------------- Game Setup ----------------------
width, height = 1200, 800
aim_len = 200
bullet_vel = 10
score = 0
total_enemys = 10

# Init pygame
pygame.init()
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Hand-Tracked Shooter")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 40)

# ---------------------- Camera Setup ----------------------
cam = cv.VideoCapture(0)
cam.set(cv.CAP_PROP_FRAME_HEIGHT, height)
cam.set(cv.CAP_PROP_FRAME_WIDTH, width)
cam.set(cv.CAP_PROP_FPS, 30)
cam.set(cv.CAP_PROP_FOURCC, cv.VideoWriter_fourcc(*'MJPG'))

# ---------------------- Mediapipe Setup ----------------------
hands = mp.solutions.hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# ---------------------- Game Classes ----------------------
Bullets = []
Enemys = []

class Bullet:
    def __init__(self, xpos, ypos, velx, vely):
        self.xpos = xpos
        self.ypos = ypos
        self.velx = velx
        self.vely = vely
        self.radius = 5
        self.clr = (255, 0, 0)
        Bullets.append(self)

    def draw(self):
        pygame.draw.circle(screen, self.clr, (int(self.xpos), int(self.ypos)), self.radius)

    def update(self):
        self.xpos += self.velx
        self.ypos += self.vely
        if self.xpos > width or self.xpos < 0 or self.ypos > height or self.ypos < 0:
            Bullets.remove(self)

class Enemy:
    def __init__(self):
        self.xpos = random.randint(100, width-100)
        self.ypos = random.randint(100, 300)
        self.radius = 20
        self.clr = (0, 255, 0)
        self.velx = 0
        self.vely = 0
        Enemys.append(self)

    def draw(self):
        pygame.draw.circle(screen, self.clr, (self.xpos, self.ypos), self.radius)

    def update(self):
        for bullet in Bullets:
            if math.hypot(self.xpos - bullet.xpos, self.ypos - bullet.ypos) < self.radius + bullet.radius:
                Enemys.remove(self)
                Bullets.remove(bullet)
                break

# Create enemies
for _ in range(total_enemys):
    Enemy()

# ---------------------- Hand Tracking Function ----------------------
def get_hand_landmarks():
    ret, frame = cam.read()
    if not ret:
        return []

    frame = cv.flip(frame, 1)  # Mirror for natural control
    frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    if results.multi_hand_landmarks:
        landmarks = []
        for lm in results.multi_hand_landmarks[0].landmark:
            landmarks.append((int(lm.x * width), int(lm.y * height)))
        return landmarks
    return []

# ---------------------- Game Loop ----------------------
current_state = "open"
prev_state = "open"
last_fire = time.time()

running = True
while running:
    screen.fill((0, 0, 0))

    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Hand tracking
    data = get_hand_landmarks()

    if len(data) == 21:
        pt1 = data[0]
        pt2 = ((data[9][0] + data[13][0]) // 2, (data[9][1] + data[13][1]) // 2)

        dist_0_12 = math.hypot(data[0][0] - data[12][0], data[0][1] - data[12][1])
        dist_0_9 = math.hypot(data[0][0] - data[9][0], data[0][1] - data[9][1])

        if dist_0_12 > dist_0_9:
            current_state = 'open'
        else:
            current_state = 'close'

        current_fire = time.time()
        if prev_state == "close" and current_state == "open" and current_fire - last_fire >= 1:
            last_fire = time.time()
            dist_pt2_pt1 = math.hypot(pt1[0] - pt2[0], pt1[1] - pt2[1])
            vel_x = bullet_vel * (pt2[0] - pt1[0]) / dist_pt2_pt1
            vel_y = bullet_vel * (pt2[1] - pt1[1]) / dist_pt2_pt1
            Bullet(pt2[0], pt2[1], vel_x, vel_y)

        prev_state = current_state

        # Draw aiming line
        pygame.draw.line(screen, (255, 0, 0), pt1, pt2, 2)

    # Update and draw enemies & bullets
    for enemy in Enemys[:]:
        enemy.update()
        enemy.draw()

    for bullet in Bullets[:]:
        bullet.update()
        bullet.draw()

    # Draw score
    score = total_enemys - len(Enemys)
    score_text = font.render(f"Score: {score}", True, (255, 0, 255))
    screen.blit(score_text, (width - 200, height - 50))

    pygame.display.flip()
    clock.tick(30)

cam.release()
pygame.quit()
