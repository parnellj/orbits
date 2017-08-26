import pygame
import math, sys, random
import os
import numpy as np
from datetime import datetime as datetime

DEBUG_CONSOLE_ON = False
DEBUG_ON = False
IS_RUNNING = True
SCREEN_X_MAX = SCREEN_Y_MAX = 800
SCREEN_X_CENTER = SCREEN_Y_CENTER = 400  #screen center is at (50, 50) AU
COORD_BOUNDS = [-50, 50, -50, 50]  #-x, +x, -y, +y
X_BOUND = (SCREEN_X_MAX / (COORD_BOUNDS[1] - COORD_BOUNDS[0]))
Y_BOUND = (SCREEN_Y_MAX / (COORD_BOUNDS[3] - COORD_BOUNDS[2]))
OBJSIZE = 2

def fitScreen(objects):
    maximum = max([max(a.dx_au for a in objects) + 1 * 2,
        max(a.dy_au for a in objects) + 1 * 2,
        -min(a.dx_au for a in objects) - 1 * 2,
        -min(a.dy_au for a in objects) - 1 * 2])
    global COORD_BOUNDS, X_BOUND, Y_BOUND
    COORD_BOUNDS = [-maximum, maximum, -maximum, maximum]
    X_BOUND = (SCREEN_X_MAX / (COORD_BOUNDS[1] - COORD_BOUNDS[0]))
    Y_BOUND = (SCREEN_Y_MAX / (COORD_BOUNDS[3] - COORD_BOUNDS[2]))

def userScreenResize(x):
    global COORD_BOUNDS, X_BOUND, Y_BOUND
    COORD_BOUNDS = [-x, x, -x, x]
    X_BOUND = (SCREEN_X_MAX / (2 * x))
    Y_BOUND = (SCREEN_Y_MAX / (2 * x))

#N.B. For some reason the current implementation rotates the perspective!
def userScreenShift(x=0, y=0):
    global COORD_BOUNDS, X_BOUND, Y_BOUND
    COORD_BOUNDS[0] += x
    COORD_BOUNDS[1] += x
    COORD_BOUNDS[2] += y
    COORD_BOUNDS[3] += y
    X_BOUND = (SCREEN_X_MAX / (2 * COORD_BOUNDS[1]))
    Y_BOUND = (SCREEN_Y_MAX / (2 * COORD_BOUNDS[3]))

#simply mark the x and y min and max on the screen, for reference
def renderGrid():
    output = [font.render(str(coord), 1, colors['WHITE'], colors['BLACK']) for coord in COORD_BOUNDS]
    screen.blit(output[0], (0, SCREEN_Y_CENTER))
    screen.blit(output[1], (SCREEN_X_MAX - 20, SCREEN_Y_CENTER))
    screen.blit(output[2], (SCREEN_X_CENTER, SCREEN_Y_MAX - 15))
    screen.blit(output[3], (SCREEN_X_CENTER, 1))

def render(objects):
    for object in objects:
        pygame.draw.circle(screen, object.color, [object.display_x, object.display_y], OBJSIZE)

TIMES = {'second' : 1, 'minute' : 60, 'hour' : 3600, 'day' : 86400,
    'week' : 604800, 'month' : 2.63e6, 'year' : 3.15569e7}

colors = {'WHITE': (255, 255, 255), 'BLACK': (0, 0, 0),
          'RED': (255, 0, 0), 'GREEN': (0, 255, 0), 'BLUE': (0, 0, 255),
          'PURPLE': (128, 0, 128), 'ORANGE': (255, 70, 0), 'YELLOW': (255, 255, 0),
          'TURQUOISE': (64, 208, 192), 'GRAY8': (128, 128, 128), 'GRAY4': (64, 64, 64),
          'GRAYC': (192, 192, 192), 'GOLD': (255, 199, 0), 'MAROON': (128, 0, 0)}

# Physical Constants
AU = 1.49597871e11  #m
G = 6.67384e-11  #m^3 * kg^-1 * s^-2
M_SOL = 1.9891e30  #kg
NAMES = ['Me', 'V', 'E', 'Ma', 'J', 'S', 'U', 'N', 'P']
MASSES = [.330e24, 4.87e24, 5.97e24, .642e24, 1898e24, 568e24, 86.8e24, 102e24, .0131e24]
RADII = [2.440e6, 6052e6, 6378e6, 3.396e6, 7.1492e7, 6.0268e7, 2.5550e7, 2.4750e7, 1.195e6]
DIST = [4.600e10, 1.0750e11, 1.4710e11, 2.0660e11, 7.4050e11, 1.35260e12, 2.74130e12, 4.44450e12, 4.43500e12]
DIST_AU = [.387, .723, 1.000, 1.524, 5.203, 9.523, 19.208, 30.087, 39.746]
DIST_AU = [x / AU for x in DIST]
VELOCS = [5.897e4, 3.525e4, 3.029e4, 2.650e4, 1.371e4, 1.018e4, 7.11e3, 5.50e3, 6.10e3]
COLORS = [colors['RED'], colors['GOLD'], colors['GREEN'], colors['MAROON'], colors['ORANGE'],
          colors['YELLOW'], colors['TURQUOISE'], colors['BLUE'], colors['PURPLE']]

MOON_NAMES = ['CALLISTO', 'GANYMEDE', 'EUROPA', 'IO']
MOON_PLANET = ['J', 'J', 'J', 'J']
MOON_MASSES = [107.6e21, 148.2e21, 48.0e21, 89.3e21]
MOON_RADII = [2.4105e6, 2.681e6, 1.561e6, 1.765e6]
MOON_DIST = [1.883e9, 1.070e9, 6.71e8, 4.22e8]
MOON_DIST = [x + DIST[4] for x in MOON_DIST]
MOON_DIST_AU = [x / AU for x in MOON_DIST]
MOON_VELOCS_BASE = [8.2e3, 10.9e3, 13.7e3, 17.3e3]
MOON_VELOCS = [x + VELOCS[4] for x in MOON_VELOCS_BASE]

#Color names
pygame.init()
screen = pygame.display.set_mode([SCREEN_X_MAX, SCREEN_Y_MAX])
font = pygame.font.Font(None, 15)
done = False
clock = pygame.time.Clock()

timescale = TIMES['hour']
max_calcs = 100                 #per body per timestep

class Body:
    count = 0
    #position (dx/dy) * AU, velocity (vx/vy) * m/s,
    #acceleration (ax/ay) * m/s^2, radius * m, and mass * kg
    def __init__(self, name="", dx=0, dy=0, vx=0, vy=0, radius=0, m=0, color=colors['WHITE'], reference_body="Sol"):
        self.id = Body.count
        if name == "":
            self.name = "Body #" + str(self.id)
        else:
            self.name = name
        Body.count += 1
        self.dx_au = dx
        self.dy_au = dy
        self.dx = dx * AU
        self.dy = dy * AU
        self.vx = vx
        self.vy = vy
        self.ax = self.ay = 0
        self.radius = radius
        self.m = m
        self.display_x = self.display_y = 0
        self.color = color
        self.mapDisplayCoords()
        self.reference_body = reference_body

    #receives a list of bodies and sums the force of each of those bodies
    def sumForces(self, bodies):
        for body in bodies:
            if body.name == self.name or body.m <= 0:
                continue
            diffx = self.dx - body.dx
            diffy = self.dy - body.dy
            distance = math.sqrt(diffx ** 2 + diffy ** 2)
            calculations = int(min(max_calcs/(math.log10(distance)), max_calcs))
            segment_timescale = timescale / calculations
            for x in xrange(0, timescale, segment_timescale):
                g = ((G * body.m) / distance ** 2) * segment_timescale
                theta = math.atan2(diffy, diffx)
                self.ax -= (g * math.cos(theta))
                self.ay -= (g * math.sin(theta))
            #if self.name == "GANYMEDE":
            #    print (body.name + " ax/ay: " + str(self.ax) + "/" + str(self.ay) + " d: " + str(distance) +
            #           " g: " + str(g) + " segTime: " + str(segment_timescale))

    #discharge the current acceleration into the velocity
    def applyForce(self):
        self.vx += self.ax
        self.vy += self.ay
        self.ax = self.ay = 0

    #apply the velocity to the object's displacement
    def applyVelocity(self):
        self.dx += self.vx * timescale
        self.dy += self.vy * timescale
        self.dx_au = self.dx / AU
        self.dy_au = self.dy / AU

    def mapDisplayCoords(self):
        self.display_x = min(SCREEN_X_MAX, max(0, int(self.dx_au * X_BOUND) + SCREEN_X_CENTER))
        self.display_y = min(SCREEN_Y_MAX, max(0, int(self.dy_au * Y_BOUND) + SCREEN_Y_CENTER))



    def makeDebugLines(self):
        return [font.render("name: " + self.name, 1, colors['WHITE'], colors['BLACK']),
                font.render("dx/dy: " + str(self.dx) + " " + str(self.dy), 1, colors['WHITE'], colors['BLACK']),
                font.render("dx/dy AU: " + str(self.dx_au) + " " + str(self.dy_au), 1, colors['WHITE'], colors['BLACK']),
                font.render("display x/y: " + str(self.display_x) + " " + str(self.display_y), 1, colors['WHITE'], colors['BLACK']),
                font.render("AU mag: " + str(math.sqrt((self.dx_au ** 2) + (self.dy_au ** 2))), 1, colors['WHITE'], colors['BLACK']),
                font.render("vx/vy: " + str(self.vx) + " " + str(self.vy), 1, colors['WHITE'], colors['BLACK']),
                font.render("ax/ay: " + str(self.ax) + " " + str(self.ay), 1, colors['WHITE'], colors['BLACK'])]

planets = [Body("Sol", 0, 0, 0, 0, 100, M_SOL)]

for x in xrange(len(VELOCS)):
    planets.append(Body(NAMES[x], DIST_AU[x], 0, 0, VELOCS[x], 100, MASSES[x], COLORS[x]))

for x in xrange(len(MOON_VELOCS)):
    planets.append(Body(MOON_NAMES[x], MOON_DIST_AU[x], 0, 0, MOON_VELOCS[x], 100, MOON_MASSES[x], colors['WHITE'], "J"))

fitScreen(planets)
renderGrid()
time_elapsed = 0

def updateSim():
    #screen.fill(colors['BLACK'])
    renderGrid()
    for obj in planets:
        obj.sumForces(planets)
        if DEBUG_ON:
            column = [a.makeDebugLines() for a in planets]
    for obj in planets:
        obj.applyForce()
        obj.applyVelocity()
        obj.mapDisplayCoords()
    if DEBUG_ON:
        for x in xrange(len(column)):
            for y in xrange(len(column[x])):
                screen.blit(column[x][y], ((x) * 150, 15 * y))
    render(planets)
    global time_elapsed
    time_elapsed += timescale / 3600
    output = font.render(str(time_elapsed) + " hours", 1, colors['WHITE'], colors['BLACK'])
    screen.blit(output, (10, 10))
    pygame.display.flip()

while not done:
    SINGLE_TICK = False

    for event in pygame.event.get(pygame.QUIT):
        done = True
    for event in pygame.event.get(pygame.KEYDOWN):
        if event.key == pygame.K_KP_MINUS:
            userScreenResize(COORD_BOUNDS[1] + 1)
        elif event.key == pygame.K_KP_PLUS:
            userScreenResize(COORD_BOUNDS[1] - 1)
        elif event.key == pygame.K_KP8:
            OBJSIZE += 1
        elif event.key == pygame.K_KP2 and OBJSIZE > 1:
            OBJSIZE -= 1
        elif event.key == pygame.K_KP7:
            max_calcs += int(max_calcs * .1)
        elif event.key == pygame.K_KP9:
            max_calcs -= int(max_calcs * .1)
        elif event.key == pygame.K_KP_PERIOD:
            IS_RUNNING = ~IS_RUNNING
        elif event.key == pygame.K_SPACE:
            SINGLE_TICK = True
        elif event.key ==pygame.K_LEFT:
            userScreenShift(-1, 0)
        elif event.key == pygame.K_RIGHT:
            userScreenShift(1, 0)
        elif event.key == pygame.K_UP:
            userScreenShift(0, 1)
        elif event.key == pygame.K_DOWN:
            userScreenShift(0, -1)
        elif event.key == pygame.K_ESCAPE:
            done = True
        elif event.key == pygame.K_KP5:
            screen.fill(colors['BLACK'])
    #clock.tick(1)

    if IS_RUNNING or SINGLE_TICK:
        updateSim()
        SINGLE_TICK = False
