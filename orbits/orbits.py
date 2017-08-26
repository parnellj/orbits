__author__ = 'Justin'

import sys, math, random
import os
import numpy as np
import pygame
from datetime import datetime

"""
It occurs to me, thanks to Cameron's insight, that gravitic forces all need to be calculated and then
applied simultaneously, before the force vector is applied to velocity.  This will be accomplished by
splitting the function in the Body() class into the following:

1. calculateForce()
2. applyForce()
"""

pygame.init()

WINSIZE = [1000, 1000]
WINCENTER = [500, 500]
WINSCALE = [5e8,5e8]        #max display distance in meters
spacescale = 2
TIMESCALES = [1, 60, 3600, 86400, 604800, 2419200, 29030400] #second, minute, hour, day, week, month, year
TIMESCALE_NAMES = ['second', 'minute', 'hour', 'day', 'week', 'month', 'year']
OBJSIZE = 1
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)           # 			
GREEN = (0, 255, 0)         # earth
BLUE = (0, 0, 255)          # neptune
YELLOW = (255, 255, 0)      # sun
DARK_RED = (175, 50, 75)    # mars
DULL_YELLOW = (175, 150, 50)# venus
TEAL = (43, 244, 251)       # uranus
RED_ORANGE = (196, 104, 34) # jupiter
TAN = (232, 181, 142)       # saturn
PURPLE = (102, 32, 223)     # pluto

G = 6.673e-11
#Mercury | Venus | Earth | Mars | Jupiter | Saturn | Uranus | Neptune | Pluto
NAMES = ['Me', 'V', 'E', 'Ma', 'J', 'S', 'U', 'N', 'P']
MASSES = [.330, 4.87, 5.97, .642, 1898, 568, 86.8, 102, .0131]                      #e24 kilograms
RADII = [2440, 6052, 6378, 3396, 71492, 60268, 25550, 24750, 1195]                  #e3 meters
DIST = [46.00, 107.50, 147.10, 206.60, 740.50, 1352.60, 2741.30, 4444.50, 4435.00]  #periapses, e9 meters
VELOCS = [58.97, 35.25, 30.29, 26.50, 13.71, 10.18, 7.11, 5.50, 6.10]               #periapses, e3 meters/sec
COLORS = [RED, DULL_YELLOW, GREEN, DARK_RED, RED_ORANGE, TAN, BLUE, TEAL, PURPLE]
M_EARTH = 5.972e+24 #kg
R_EARTH = 6.371e+6  #meters

timescale_i = 2
timescale = TIMESCALES[timescale_i]


class Body:
    count = 0
    def __init__(self, name=' ', coordinates=[0.0,0.0], velocity=[0.0,0.0], acceleration=[0.0,0.0], mass=0.0, radius=10.0, color=BLACK):
        self.id = Body.count
        Body.count += 1
        self.name = name
        self.coordinates = coordinates
        self.velocity = velocity
        self.velocity_mag = math.sqrt(velocity[0] ** 2 + velocity[1] ** 2)
        self.acceleration = acceleration
        self.acceleration_mag = math.sqrt(acceleration[0] ** 2 + acceleration[1] ** 2)
        self.mass = mass
        self.radius = radius
        self.display_position = (((np.array(self.coordinates) / WINSCALE / 2) * WINSIZE) + WINCENTER).astype(int)
        self.display_radius = OBJSIZE
        self.color = color

    def sum_forces(self,attractors,timescale=1):
        self.acceleration = [0.0, 0.0]
        self.acceleration_mag = 0.0
        for attractor in attractors:
            assert isinstance(attractor, Body)
            if attractor.id != self.id and attractor.mass > 0:
                self.calculate_force(attractor,timescale)

    def apply_forces(self):
        #apply acceleration against current velocity vector and magnitude (angle = theta for static attractor)
        self.velocity_mag += self.acceleration_mag
        self.velocity += (self.acceleration * timescale)
        #apply velocity against current displacement
        self.coordinates += (self.velocity * timescale)

    def calculate_force(self,attractor,timescale=1):
        assert isinstance(attractor, Body)
        #r - unsigned euclidean distance between self and attractor
        diff = np.array(self.coordinates) - np.array(attractor.coordinates)
        r = math.sqrt(np.dot(diff, diff))
        #g - gravitational field of attractor, as acceleration
        g = G * (attractor.mass / r**2)
        #theta - angle of self from the polar axis
        theta = math.atan2(diff[1],diff[0])
        #add g to acceleration vector and magnitude
        self.acceleration_mag -= (g * timescale)
        self.acceleration += -np.array((g * math.cos(theta), g * math.sin(theta)))

    def update_display(self):
        self.display_position = (((np.array(self.coordinates) / spacescale / WINSCALE) * WINSIZE) + WINCENTER).astype(int)
    
    def draw(self):
        pygame.draw.circle(screen,self.color,self.display_position,self.display_radius)
        pygame.draw.line(screen, RED, self.display_position, self.display_position+self.acceleration)
        #pygame.draw.line(screen, BLUE, self.display_position, self.display_position+(self.velocity/250))
        label=["acceleration magnitude","acceleration vector","velocity vector"]
        output = font.render(self.name,0,BLACK,WHITE)
        screen.blit(output,(10,(self.id * 60)))
        for x in xrange(len(label)):
            output = font.render(label[x]+": "+str(self.acceleration_mag),0,BLACK,WHITE)
            screen.blit(output, (15,(self.id*60)+(15*x)+15))

screen = pygame.display.set_mode(WINSIZE)
done = False
clock = pygame.time.Clock()

#define a series of random massed particles
def make_particles (count):
    particles = [Body() for x in xrange(count)]
    for x in xrange(len(particles)):
        coords = [random.choice(range(-4,-1) + range(1,4)), random.choice(range(-5,-1) + range(1,5))]
        velocs = [random.choice(range(-4000,1) + range(1,4000)), random.choice(range(-4000,1) + range(1,4000))]
        m = random.randint(1,200)
        r = random.randint(1,100)
        c = (random.randint(50,255),random.randint(50,255),random.randint(50,255))
        particles[x] = Body(np.array(coords)*1e7,velocs,[0.0,0.0],m,r,c)
    return particles

#make the nine planets according to predefined tables
def make_planets ():
    planets = [Body() for x in xrange(len(NAMES))]
    for x in xrange(len(planets)):
        planets[x] = Body(NAMES[x],[DIST[x]*1e9,0.0],[0.0,-VELOCS[x]*1e3],[0.0,0.0],MASSES[x]*1e24,RADII[x]*1e3,COLORS[x])
    return planets

earth = Body('Earth',[0.0,0.0],[0.0,0.0],[0.0,0.0],M_EARTH,R_EARTH, GREEN)
moon = Body('Moon',[384399000,0],[0.0,-1022.0],[0.0,0.0],7.3477e22,1.738e6, BLACK)
sol = Body('Sol',[0.0,0.0],[0.0,0.0],[0.0,0.0],1.988e30,6.96e8,RED)

binary_star = [Body('Star_1', [1.0e11, 0.0],[0.0,4000.0],[0.0,0.0],1.9891e30,695.5e6,GREEN),
               Body('Star_2', [-1.0e11,0.0],[0.0,-4000.0],[0.0,0.0],1.981e30,695.5e6,RED),
              Body('Star_3', [0.0,0.0],[0.0,0.0],[0.0,0.0],0,BLACK)]

particles = make_particles(0)
planets = make_planets()

WINSCALE = [max(DIST)*spacescale*1e9,max(DIST)*spacescale*1e9]
toggle = False
sim_time = 0

font = pygame.font.Font(None,15)
screen.fill(WHITE)

while not done:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True

    #clock.tick(10)
    screen.fill(WHITE)
    #basic input for rescaling the display and shifting the timescale
    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
        spacescale *= 2
    elif keys[pygame.K_DOWN]:
        spacescale /= 2
    elif keys[pygame.K_LEFT] and (timescale_i > 0):
        timescale_i -= 1
        timescale = TIMESCALES[timescale_i]
    elif keys[pygame.K_RIGHT] and (timescale_i < (len(TIMESCALES)-1)):
        timescale_i += 1
        timescale = TIMESCALES[timescale_i]

    for particle in binary_star:
        particle.sum_forces(binary_star,timescale)

    for particle in binary_star:
        particle.apply_forces()
        particle.update_display()
        particle.draw()

    pygame.display.flip()
