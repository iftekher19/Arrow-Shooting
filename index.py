from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math

# --- Player Movement & Boundaries ---
PLAYER_BOUNDARY = 200
player_x, player_z = 0, 0
disqualified = False

def keyboardListener(key, x, y):
    global player_x, player_z, disqualified
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

# --- Drawing Arena (Grid + Walls + Boundary Circle) ---
def draw_ground():
    glBegin(GL_QUADS)
    glColor3f(0.2,0.6,0.2)
    glVertex3f(-600,0,-1000)
    glVertex3f(600,0,-1000)
    glColor3f(0.3,0.8,0.3)
    glVertex3f(600,0,100)
    glVertex3f(-600,0,100)
    glEnd()

    glColor3f(0.35,0.65,0.35)
    for d in range(100,800,100):
        glBegin(GL_LINES)
        glVertex3f(-400,0.5,-d)
        glVertex3f(400,0.5,-d)
        glEnd()

def draw_walls():
    glColor3f(0.8,0.8,0.8)
    wall_height, wall_thickness = 25, 6
    for pos in [(0,-PLAYER_BOUNDARY,True),(0,PLAYER_BOUNDARY,True),
                (PLAYER_BOUNDARY,0,False),(-PLAYER_BOUNDARY,0,False)]:
        glPushMatrix()
        if pos[2]:
            glTranslatef(pos[0], wall_height/2, pos[1])
            glScalef(PLAYER_BOUNDARY*2, wall_height, wall_thickness)
        else:
            glTranslatef(pos[0], wall_height/2, pos[1])
            glScalef(wall_thickness, wall_height, PLAYER_BOUNDARY*2)
        glutSolidCube(1)
        glPopMatrix()

    # Red circle boundary on ground
    glColor3f(0.9,0.2,0.2)
    glBegin(GL_LINE_LOOP)
    for i in range(100):
        angle = 2*math.pi*i/100
        glVertex3f(PLAYER_BOUNDARY*math.cos(angle),0.2,PLAYER_BOUNDARY*math.sin(angle))
    glEnd()