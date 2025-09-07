from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import time
import numpy as np

# Game constants
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
GRAVITY = -9.8
PLAYER_BOUNDARY = 200
MAX_ARROW_POWER = 100
POWER_CHARGE_RATE = 50
ARROW_SPEED_FACTOR = 4.0

# Game state
camera_mode = 0 
camera_smooth = [0, 0, 0]
camera_look_smooth = [0, 0, 0]  
camera_up_smooth = [0, 1, 0]  
bow_vertical_angle = 0
arrow_power = 0
charging = False
arrows = []
targets = []
score = 0
arrows_left = 20
game_over = False
particles = []
level = 0
hits = 0
player_x = 0
player_z = 0
disqualified = False
cheat_mode = False
auto_aim = False
last_time = time.time()
last_shoot_time = 0  

class Target:
    def __init__(self, x, y, z, size, points):
        self.x = x
        self.y = y
        self.z = z
        self.center_x = x  
        self.center_z = z  
        self.original_size = size
        self.size = size
        self.points = points
        self.hit = False
        self.hit_animation = 0
        self.speed = 0
        self.direction = [random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)]  
        length = math.sqrt(self.direction[0]**2 + self.direction[1]**2 + self.direction[2]**2)
        if length > 0:
            self.direction[0] /= length
            self.direction[1] /= length
            self.direction[2] /= length
        self.respawn_timer = 0
        self.movement_pattern = random.choice(['none', 'horizontal', 'vertical', 'circular'])
        self.movement_phase = random.uniform(0, 2 * math.pi)

class Arrow:
    def __init__(self, x, y, z, vx, vy, vz):
        self.x = x
        self.y = y
        self.z = z
        self.vx = vx
        self.vy = vy
        self.vz = vz
        self.stuck = False
        self.trail = []
        self.lifetime = 5.0
        self.missed = False
        self.rotation = 0

class Particle:
    def __init__(self, x, y, z, vx, vy, vz, color, lifetime, size=2.0):
        self.x = x
        self.y = y
        self.z = z
        self.vx = vx
        self.vy = vy
        self.vz = vz
        self.color = color
        self.lifetime = lifetime
        self.size = size

def init_game():
    global targets, arrows, score, arrows_left, game_over, particles, level, hits
    global player_x, player_z, disqualified, cheat_mode, auto_aim, last_time, last_shoot_time
    targets.clear()
    arrows.clear()
    particles.clear()
    score = 0
    arrows_left = 20
    game_over = False
    level = 0
    hits = 0
    player_x = 0
    player_z = 0
    disqualified = False
    cheat_mode = False
    auto_aim = False
    last_time = time.time()  
    last_shoot_time = 0
    
    # Create targets with better positioning
    targets.append(Target(0, 100, -300, 50, 10))
    targets.append(Target(-120, 120, -350, 45, 15))
    targets.append(Target(120, 120, -350, 45, 15))
    targets.append(Target(-180, 140, -500, 40, 25))
    targets.append(Target(180, 140, -500, 40, 25))
    targets.append(Target(0, 160, -600, 35, 30))

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_bow():
    glPushMatrix()
    glTranslatef(player_x, 50, player_z)
    
    # Apply aiming rotations
    glRotatef(bow_angle, 0, 1, 0)
    glRotatef(bow_vertical_angle, 1, 0, 0)
    
    # Rotate bow to be horizontal
    glRotatef(90, 0, 0, 1)
    
    # Bow grip - more detailed
    glColor3f(0.4, 0.2, 0.1)
    glPushMatrix()
    glRotatef(90, 0, 1, 0)
    gluCylinder(gluNewQuadric(), 2.5, 2.5, 20, 16, 16)
    glPopMatrix()
    
    # Upper limb
    glColor3f(0.6, 0.3, 0.15)
    glPushMatrix()
    glTranslatef(10, 0, 0)
    glRotatef(-25, 0, 0, 1)
    glRotatef(90, 0, 1, 0)
    gluCylinder(gluNewQuadric(), 1.8, 1.2, 30, 16, 16)
    glPopMatrix()
    
    # Lower limb
    glPushMatrix()
    glTranslatef(10, 0, 0)
    glRotatef(25, 0, 0, 1)
    glRotatef(90, 0, 1, 0)
    gluCylinder(gluNewQuadric(), 1.8, 1.2, 30, 16, 16)
    glPopMatrix()
    
    # String - more realistic curve
    glColor3f(0.9, 0.9, 0.9)
    glLineWidth(2.0)
    glBegin(GL_LINE_STRIP)
    glVertex3f(10 + 25, 15, 0)
    glVertex3f(10 + 25, 0, 3)
    glVertex3f(10 + 25, -15, 0)
    glEnd()
    glLineWidth(1.0)
    
    # Draw arrow when charging
    if charging:
        pullback = arrow_power * 0.25
        glColor3f(0.7, 0.35, 0.15)
        glBegin(GL_LINES)
        glVertex3f(10 + 25 - pullback, 0, 0)
        glVertex3f(10 + 25 + 35, 0, 0)
        glEnd()
        
        # Arrowhead
        glColor3f(0.8, 0.8, 0.8)
        glPushMatrix()
        glTranslatef(10 + 25 + 35, 0, 0)
        glutSolidCone(2.5, 6, 16, 16)
        glPopMatrix()
        
        # Fletching
        glColor3f(0.9, 0.2, 0.2)
        glPushMatrix()
        glTranslatef(10 + 25 - pullback, 0, 0)
        glBegin(GL_TRIANGLES)
        glVertex3f(0, 0, 0)
        glVertex3f(-4, 4, 6)
        glVertex3f(4, 4, 6)
        glEnd()
        glPopMatrix()
    
    # Aiming sight - professional design
    glDisable(GL_LIGHTING)
    glColor3f(1, 0, 0)
    glPushMatrix()
    glTranslatef(0, 0, -150)
    
    # Center dot
    glPointSize(12)
    glBegin(GL_POINTS)
    glVertex3f(0, 0, 0)
    glEnd()
    
    # Crosshair with circle
    glLineWidth(2.0)
    glBegin(GL_LINES)
    glVertex3f(-20, 0, 0)
    glVertex3f(-8, 0, 0)
    glVertex3f(8, 0, 0)
    glVertex3f(20, 0, 0)
    glVertex3f(0, -20, 0)
    glVertex3f(0, -8, 0)
    glVertex3f(0, 8, 0)
    glVertex3f(0, 20, 0)
    glEnd()
    
    # Circle
    glBegin(GL_LINE_LOOP)
    for i in range(32):
        angle = 2 * math.pi * i / 32
        glVertex3f(15 * math.cos(angle), 15 * math.sin(angle), 0)
    glEnd()
    
    glLineWidth(1.0)
    glPopMatrix()
    glEnable(GL_LIGHTING)
    
    # Power bar - better design
    if charging:
        # Background
        glColor3f(0.3, 0.3, 0.3)
        glPushMatrix()
        glTranslatef(0, -50, 0)
        glScalef(40, 5, 5)
        glutSolidCube(1)
        glPopMatrix()
        
        # Fill with gradient
        power_ratio = arrow_power / MAX_ARROW_POWER
        glColor3f(1, 1 - power_ratio, 0)
        glPushMatrix()
        glTranslatef(-20 + power_ratio * 20, -50, 0)
        glScalef(power_ratio * 40, 5, 5)
        glutSolidCube(1)
        glPopMatrix()
    
    glPopMatrix()

def draw_arrow(arrow):
    if len(arrow.trail) < 2:
        pass  # Don't draw trail
    else:
        glDisable(GL_LIGHTING)
        glLineWidth(3.0)
        glBegin(GL_LINE_STRIP)
        for i, pos in enumerate(arrow.trail):
            alpha = i / len(arrow.trail)
            glColor3f(1, 0.7 * alpha, 0.3 * alpha)
            glVertex3f(*pos)
        glEnd()
        glLineWidth(1.0)
        glEnable(GL_LIGHTING)
    
    glPushMatrix()
    glTranslatef(arrow.x, arrow.y, arrow.z)
    
    # Calculate arrow rotation based on velocity
    if arrow.vx != 0 or arrow.vz != 0:
        yaw = math.degrees(math.atan2(arrow.vx, arrow.vz))
    else:
        yaw = 0
    pitch = math.degrees(math.atan2(arrow.vy, math.sqrt(arrow.vx**2 + arrow.vz**2)))
    
    # Apply rotations
    glRotatef(-yaw, 0, 1, 0)
    glRotatef(pitch, 1, 0, 0)
    glRotatef(arrow.rotation, 0, 0, 1)
    
    # Arrow shaft
    glColor3f(0.7, 0.35, 0.15)
    gluCylinder(gluNewQuadric(), 1.2, 1.2, 35, 16, 16)
    
    # Arrowhead
    glColor3f(0.85, 0.85, 0.85)
    glTranslatef(0, 0, 35)
    glutSolidCone(2.5, 6, 16, 16)
    
    # Fletching
    glColor3f(0.9, 0.2, 0.2)
    glTranslatef(0, 0, -35)
    glBegin(GL_TRIANGLES)
    glVertex3f(0, 0, 0)
    glVertex3f(-4, 4, 6)
    glVertex3f(4, 4, 6)
    glEnd()
    
    glPopMatrix()

def draw_target(target):
    if target.hit:
        # Draw hit effect
        if target.hit_animation > 0:
            glPushMatrix()
            glTranslatef(target.x, target.y, target.z)
            glColor4f(1, 1, 0, target.hit_animation)
            glutSolidSphere(target.size * (1.5 - target.hit_animation), 16, 16)
            glPopMatrix()
            target.hit_animation -= 0.03
        return
    
    glPushMatrix()
    glTranslatef(target.x, target.y, target.z)
    
    # Target stand - more detailed
    glColor3f(0.5, 0.3, 0.1)
    glPushMatrix()
    glTranslatef(0, -target.size - 30, 0)
    glRotatef(90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 4, 4, target.y + target.size + 30, 16, 16)
    glPopMatrix()
    
    # Target face - professional design
    glColor3f(0.95, 0.95, 0.95)
    glPushMatrix()
    glRotatef(90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), target.size, target.size, 3, 32, 1)
    glPopMatrix()
    
    glTranslatef(0, 0, 1.5)
    
    # Target rings with proper proportions
    # Bullseye (center) - gold
    glColor3f(1.0, 0.8, 0.0)
    gluDisk(gluNewQuadric(), 0, target.size * 0.15, 32, 1)
    
    # Inner ring - red
    glColor3f(0.9, 0.1, 0.1)
    gluDisk(gluNewQuadric(), target.size * 0.15, target.size * 0.35, 32, 1)
    
    # Middle ring - blue
    glColor3f(0.1, 0.3, 0.8)
    gluDisk(gluNewQuadric(), target.size * 0.35, target.size * 0.65, 32, 1)
    
    # Outer ring - black
    glColor3f(0.1, 0.1, 0.1)
    gluDisk(gluNewQuadric(), target.size * 0.65, target.size * 0.85, 32, 1)
    
    # Outermost ring - white
    glColor3f(0.95, 0.95, 0.95)
    gluDisk(gluNewQuadric(), target.size * 0.85, target.size, 32, 1)
    
    glPopMatrix()

def draw_ground():
    # Ground with better texture-like appearance
    glBegin(GL_QUADS)
    glColor3f(0.2, 0.6, 0.2)  
    glVertex3f(-600, 0, -1000)
    glVertex3f(600, 0, -1000)
    glColor3f(0.3, 0.8, 0.3)  
    glVertex3f(600, 0, 100)
    glVertex3f(-600, 0, 100)
    glEnd()
    
    # Grid lines - more subtle
    glColor3f(0.35, 0.65, 0.35)
    glLineWidth(1.0)
    for d in range(100, 800, 100):
        glBegin(GL_LINES)
        glVertex3f(-400, 0.5, -d)
        glVertex3f(400, 0.5, -d)
        glEnd()
    
    # Distance markers
    for d in range(100, 800, 100):
        for x in range(-400, 401, 100):
            glBegin(GL_LINES)
            glVertex3f(x, 0.5, -d)
            glVertex3f(x, 4, -d)
            glEnd()

def draw_walls():
    glColor3f(0.8, 0.8, 0.8)  # Light gray walls
    wall_height = 25
    wall_thickness = 6
    
    # Draw boundary walls
    glPushMatrix()
    glTranslatef(0, wall_height/2, -PLAYER_BOUNDARY)
    glScalef(PLAYER_BOUNDARY*2, wall_height, wall_thickness)
    glutSolidCube(1)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(0, wall_height/2, PLAYER_BOUNDARY)
    glScalef(PLAYER_BOUNDARY*2, wall_height, wall_thickness)
    glutSolidCube(1)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(PLAYER_BOUNDARY, wall_height/2, 0)
    glScalef(wall_thickness, wall_height, PLAYER_BOUNDARY*2)
    glutSolidCube(1)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(-PLAYER_BOUNDARY, wall_height/2, 0)
    glScalef(wall_thickness, wall_height, PLAYER_BOUNDARY*2)
    glutSolidCube(1)
    glPopMatrix()
    
    # Draw boundary circle on ground
    glColor3f(0.9, 0.2, 0.2) 
    glLineWidth(3.0)
    glBegin(GL_LINE_LOOP)
    for i in range(100):
        angle = 2 * math.pi * i / 100
        glVertex3f(PLAYER_BOUNDARY * math.cos(angle), 0.2, PLAYER_BOUNDARY * math.sin(angle))
    glEnd()
    glLineWidth(1.0)

def update_particles(dt):
    global particles
    for particle in particles[:]:
        particle.x += particle.vx * dt
        particle.y += particle.vy * dt
        particle.z += particle.vz * dt
        particle.vy += GRAVITY * dt
        particle.lifetime -= dt
        
        if particle.lifetime <= 0:
            particles.remove(particle)

def draw_particles():
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)  
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glPointSize(4.0)
    glBegin(GL_POINTS)
    for particle in particles:
        alpha = min(1.0, particle.lifetime)
        glColor4f(particle.color[0], particle.color[1], particle.color[2], alpha)
        glVertex3f(particle.x, particle.y, particle.z)
    glEnd()
    glDisable(GL_BLEND)
    glEnable(GL_LIGHTING)

def create_hit_effect(x, y, z, hit_zone):
    # Different effects based on hit zone
    if hit_zone == "bullseye":
        # Gold explosion for bullseye
        for _ in range(40):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(30, 70)
            vx = math.cos(angle) * speed
            vy = random.uniform(30, 60)
            vz = math.sin(angle) * speed
            color = (1.0, random.uniform(0.7, 1.0), 0.0)
            particles.append(Particle(x, y, z, vx, vy, vz, color, random.uniform(0.8, 1.5), 4.0))
    elif hit_zone == "inner":
        # Red explosion for inner ring
        for _ in range(30):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(20, 50)
            vx = math.cos(angle) * speed
            vy = random.uniform(20, 40)
            vz = math.sin(angle) * speed
            color = (0.9, random.uniform(0.1, 0.3), 0.1)
            particles.append(Particle(x, y, z, vx, vy, vz, color, random.uniform(0.6, 1.2), 3.0))
    else:
        # Blue explosion for outer rings
        for _ in range(20):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(15, 35)
            vx = math.cos(angle) * speed
            vy = random.uniform(15, 30)
            vz = math.sin(angle) * speed
            color = (0.1, 0.3, 0.8)
            particles.append(Particle(x, y, z, vx, vy, vz, color, random.uniform(0.5, 1.0), 2.5))

def create_miss_effect(x, y, z):
    # Dust cloud effect
    for _ in range(15):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(5, 15)
        vx = math.cos(angle) * speed
        vy = random.uniform(5, 15)
        vz = math.sin(angle) * speed
        color = (0.7, 0.6, 0.4)
        particles.append(Particle(x, y, z, vx, vy, vz, color, random.uniform(0.3, 0.8), 2.0))

def update_targets(dt):
    global hits, level  
    
    for target in targets:
        if target.hit:
            target.respawn_timer += dt
            if target.respawn_timer >= 2.0:  # Respawn after 2 seconds
                target.hit = False
                target.respawn_timer = 0
                # Increase difficulty with level
                target.speed = 1.0 + (level * 0.7)
                target.size = max(target.original_size * (1 - level * 0.12), target.original_size * 0.4)
        elif target.speed > 0:
            # Update position based on movement pattern
            if target.movement_pattern == 'horizontal':
                target.x += target.direction[0] * target.speed * dt
                if target.x < -450 or target.x > 450:
                    target.direction[0] *= -1
            elif target.movement_pattern == 'vertical':
                target.y += target.direction[1] * target.speed * dt
                if target.y < 50 or target.y > 200:
                    target.direction[1] *= -1
            elif target.movement_pattern == 'circular':
                target.movement_phase += dt * target.speed / 50  
                radius = 50
                target.x = target.center_x + radius * math.cos(target.movement_phase)  
                target.z = target.center_z + radius * math.sin(target.movement_phase)  

def update_arrows(dt):
    global arrows, score, arrows_left, game_over, hits, level
    
    for arrow in arrows[:]:
        if arrow.stuck:
            arrow.lifetime -= dt 
            if arrow.lifetime <= 0:
                arrows.remove(arrow)
            continue
            
        # Update position with physics
        arrow.x += arrow.vx * dt
        arrow.y += arrow.vy * dt
        arrow.z += arrow.vz * dt
        
        # Apply gravity
        arrow.vy += GRAVITY * dt
        
        # Add rotation effect
        arrow.rotation += 5 * dt
        
        # Add to trail
        arrow.trail.append((arrow.x, arrow.y, arrow.z))
        if len(arrow.trail) > 25:
            arrow.trail.pop(0)
        
        # Ground collision
        if arrow.y <= 0:
            arrow.stuck = True
            arrow.y = 0
            arrow.missed = True
            create_miss_effect(arrow.x, 0, arrow.z)
        
        # Wall collision
        if (abs(arrow.x) > PLAYER_BOUNDARY or abs(arrow.z) > PLAYER_BOUNDARY) and not arrow.missed:
            arrow.stuck = True
            arrow.missed = True
            create_miss_effect(arrow.x, arrow.y, arrow.z)
        
        # Target collision with precise detection (Fix: Check in YZ plane assuming target orientation)
        for target in targets:
            if not target.hit:
                dx = arrow.x - target.x
                dy = arrow.y - target.y
                dz = arrow.z - target.z
                
                # Distance in YZ plane
                dist_yz = math.sqrt(dy**2 + dz**2)
                
                if abs(dx) < 8 and dist_yz < target.size:  
                    target.hit = True
                    target.hit_animation = 1.0
                    arrow.stuck = True
                    
                    # Determine hit zone and score
                    if dist_yz < target.size * 0.15: 
                        score += target.points * 5
                        create_hit_effect(target.x, target.y, target.z, "bullseye")
                    elif dist_yz < target.size * 0.35:  
                        score += target.points * 3
                        create_hit_effect(target.x, target.y, target.z, "inner")
                    elif dist_yz < target.size * 0.65:  
                        score += target.points * 2
                        create_hit_effect(target.x, target.y, target.z, "middle")
                    else:  # Outer
                        score += target.points
                        create_hit_effect(target.x, target.y, target.z, "outer")
                    
                    hits += 1
                    level = hits // 6
                    break
        
        arrow.lifetime -= dt
        if arrow.lifetime <= 0 or arrow.z < -1200:
            if arrow in arrows:
                arrows.remove(arrow)

def shoot_arrow():
    global arrows_left
    if arrows_left <= 0:
        return
        
    arrows_left -= 1
    
    # Calculate initial velocity based on power and angles
    speed = arrow_power * ARROW_SPEED_FACTOR
    
    angle_rad = math.radians(bow_angle)
    vertical_angle_rad = math.radians(bow_vertical_angle)
    
    dx = math.sin(angle_rad) * math.cos(vertical_angle_rad)
    dy = math.sin(vertical_angle_rad)
    dz = -math.cos(angle_rad) * math.cos(vertical_angle_rad)
    
    vx = speed * dx
    vy = speed * dy
    vz = speed * dz
    
    # Starting position at bow 
    bow_tip_length = 10 + 25 + 35
    offset_x = bow_tip_length * dx
    offset_y = bow_tip_length * dy
    offset_z = bow_tip_length * dz
    
    # Apply bow's 90-degree rotation (around Z)
    rotated_x = offset_y  
    rotated_y = -offset_x
    rotated_z = offset_z
    
    start_x = player_x + rotated_x
    start_y = 50 + rotated_y
    start_z = player_z + rotated_z
    
    arrows.append(Arrow(start_x, start_y, start_z, vx, vy, vz))

def keyboardListener(key, x, y):
    global bow_angle, bow_vertical_angle, charging, arrow_power, camera_mode
    global player_x, player_z, disqualified, cheat_mode, auto_aim
    
    # Player movement 
    if key == b'w':
        player_z -= 5
        if math.sqrt(player_x**2 + player_z**2) > PLAYER_BOUNDARY:
            player_z += 5
            disqualified = True
        else:
            disqualified = False  
    elif key == b's':
        player_z += 5
        if math.sqrt(player_x**2 + player_z**2) > PLAYER_BOUNDARY:
            player_z -= 5
            disqualified = True
        else:
            disqualified = False
    elif key == b'a':
        player_x -= 5
        if math.sqrt(player_x**2 + player_z**2) > PLAYER_BOUNDARY:
            player_x += 5
            disqualified = True
        else:
            disqualified = False
    elif key == b'd':
        player_x += 5
        if math.sqrt(player_x**2 + player_z**2) > PLAYER_BOUNDARY:
            player_x -= 5
            disqualified = True
        else:
            disqualified = False
    
    # Bow rotation
    elif key == b'j':
        bow_angle -= 3
    elif key == b'l':
        bow_angle += 3
    elif key == b'i':
        bow_vertical_angle = min(bow_vertical_angle + 2, 85)
    elif key == b'k':
        bow_vertical_angle = max(bow_vertical_angle - 2, -85)
    elif key == b' ':
        if not charging and arrows_left > 0:
            charging = True
            arrow_power = 0
    elif key == b'f':
        camera_mode = 3
    elif key == b't':
        camera_mode = 0
    elif key == b'r':
        init_game()
    elif key == b'c':
        cheat_mode = not cheat_mode
        auto_aim = not auto_aim

def keyboardUpListener(key, x, y):
    global charging, arrow_power
    if key == b' ' and charging:
        shoot_arrow()
        charging = False
        arrow_power = 0

def mouseListener(button, state, x, y):
    global charging, arrow_power, camera_mode
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        if not charging and arrows_left > 0:
            charging = True
            arrow_power = 0
    elif button == GLUT_LEFT_BUTTON and state == GLUT_UP:
        if charging:
            shoot_arrow()
            charging = False
            arrow_power = 0
    elif button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        camera_mode = (camera_mode + 1) % 4

def reshape(width, height):
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, width / height, 0.1, 1500)
    glMatrixMode(GL_MODELVIEW)

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, WINDOW_WIDTH / WINDOW_HEIGHT, 0.1, 1500)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    # Target positions for each camera mode
    if camera_mode == 0:  # Third-person behind bow
        target_pos = (player_x, 100, player_z + 200)
        target_look = (player_x, 50, player_z - 200)
        target_up = (0, 1, 0)
    elif camera_mode == 1:  # Side view
        target_pos = (player_x + 400, 200, player_z)
        target_look = (player_x, 50, player_z - 200)
        target_up = (0, 1, 0)
    elif camera_mode == 2:  # Top view
        target_pos = (player_x, 600, player_z - 200)
        target_look = (player_x, 0, player_z - 200)
        target_up = (0, 0, -1)
    elif camera_mode == 3:  # First-person view
        angle_rad = math.radians(bow_angle)
        vertical_angle_rad = math.radians(bow_vertical_angle)
        dx = math.sin(angle_rad) * math.cos(vertical_angle_rad)
        dy = math.sin(vertical_angle_rad)
        dz = -math.cos(angle_rad) * math.cos(vertical_angle_rad)
        target_pos = (player_x, 50, player_z)
        target_look = (player_x + dx*100, 50 + dy*100, player_z + dz*100)
        target_up = (0, 1, 0)
    
    # Smooth camera transition (Fix: Smooth position, look, and up)
    for i in range(3):
        camera_smooth[i] += (target_pos[i] - camera_smooth[i]) * 0.1
        camera_look_smooth[i] += (target_look[i] - camera_look_smooth[i]) * 0.1
        camera_up_smooth[i] += (target_up[i] - camera_up_smooth[i]) * 0.1
    
    gluLookAt(
        camera_smooth[0], camera_smooth[1], camera_smooth[2],
        camera_look_smooth[0], camera_look_smooth[1], camera_look_smooth[2],
        camera_up_smooth[0], camera_up_smooth[1], camera_up_smooth[2]
    )

def idle():
    global arrow_power, game_over, last_time, auto_aim, last_shoot_time
    
    current_time = time.time()
    dt = current_time - last_time
    last_time = current_time
    
    dt = min(dt, 0.1)
    
    # Handle auto-aim in cheat mode 
    if auto_aim and arrows_left > 0 and not charging and current_time - last_shoot_time > 1.0:  # Shoot every 1 second
        closest_target = None
        min_distance = float('inf')
        
        for target in targets:
            if not target.hit:
                dx = target.x - player_x
                dy = target.y - 50
                dz = target.z - player_z
                distance = math.sqrt(dx**2 + dy**2 + dz**2)
                
                if distance < min_distance:
                    min_distance = distance
                    closest_target = target
        
        if closest_target:
            dx = closest_target.x - player_x
            dy = closest_target.y - 50
            dz = closest_target.z - player_z
            
            bow_angle = math.degrees(math.atan2(dx, -dz))
            
            horizontal_distance = math.sqrt(dx**2 + dz**2)
            bow_vertical_angle = math.degrees(math.atan2(dy, horizontal_distance))
            
            bow_vertical_angle = max(-85, min(85, bow_vertical_angle))
            
            arrow_power = MAX_ARROW_POWER
            shoot_arrow()
            arrow_power = 0
            last_shoot_time = current_time  
    
    if charging:
        arrow_power = min(arrow_power + POWER_CHARGE_RATE * dt, MAX_ARROW_POWER)
    
    update_arrows(dt)
    update_targets(dt)
    update_particles(dt)
    
    # Check game over 
    active_arrows = [a for a in arrows if not a.stuck]
    if arrows_left == 0 and len(active_arrows) == 0:
        game_over = True
    
    glutPostRedisplay()

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    
    # Set up lighting 
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_NORMALIZE)
    glLightfv(GL_LIGHT0, GL_POSITION, (0, 500, 0, 1))
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.4, 0.4, 0.4, 1))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.8, 0.8, 0.8, 1))
    
    setupCamera()
    
    # Draw game elements
    draw_ground()
    draw_walls()
    draw_bow()
    
    for target in targets:
        draw_target(target)
    
    for arrow in arrows:
        draw_arrow(arrow)
    
    draw_particles()
    
    # Draw UI with better design (Moved after 3D for proper overlay)
    draw_text(20, WINDOW_HEIGHT - 40, f"Score: {score}")
    draw_text(20, WINDOW_HEIGHT - 80, f"Arrows: {arrows_left}")
    draw_text(20, WINDOW_HEIGHT - 120, f"Level: {level}")
    
    if charging:
        draw_text(20, WINDOW_HEIGHT - 160, "Power:")
        glColor3f(1, 1 - arrow_power/MAX_ARROW_POWER, 0)
        glBegin(GL_QUADS)
        glVertex2f(100, WINDOW_HEIGHT - 170)
        glVertex2f(100 + arrow_power * 2, WINDOW_HEIGHT - 170)
        glVertex2f(100 + arrow_power * 2, WINDOW_HEIGHT - 150)
        glVertex2f(100, WINDOW_HEIGHT - 150)
        glEnd()
    
    if game_over:
        draw_text(WINDOW_WIDTH/2 - 150, WINDOW_HEIGHT/2, f"GAME OVER! Score: {score}")
        draw_text(WINDOW_WIDTH/2 - 100, WINDOW_HEIGHT/2 - 40, "Press R to restart")
    
    if disqualified:
        draw_text(WINDOW_WIDTH/2 - 150, WINDOW_HEIGHT/2, "DISQUALIFIED!")
        draw_text(WINDOW_WIDTH/2 - 100, WINDOW_HEIGHT/2 - 40, "Press R to restart")
    
    if cheat_mode:
        draw_text(WINDOW_WIDTH - 200, WINDOW_HEIGHT - 40, "AUTO-AIM MODE")
    
    # Controls
    draw_text(20, 150, "Controls:")
    draw_text(20, 120, "WASD - Move")
    draw_text(20, 90, "JL - Rotate")
    draw_text(20, 60, "IK - Aim Up/Down")
    draw_text(20, 30, "SPACE/Click - Shoot")
    
    draw_text(250, 150, "F - First-person")
    draw_text(250, 120, "T - Third-person")
    draw_text(250, 90, "C - Auto-aim")
    draw_text(250, 60, "R - Restart")
    
    glutSwapBuffers()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Professional Archery Game")
    
    # Set up OpenGL
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glClearColor(0.5, 0.7, 0.9, 1.0)  # Sky blue background
    
    # Initialize game
    init_game()
    
    # Set up callbacks
    glutDisplayFunc(showScreen)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboardListener)
    glutKeyboardUpFunc(keyboardUpListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    
    glutMainLoop()

if __name__ == "__main__":
    main()