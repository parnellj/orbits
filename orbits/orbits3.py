import math

import numpy as np
import pygame

TIMES = [1, 60, 3600, 86400, 604800, 2630000, 31556900]

COLORS = {'WHITE': (255, 255, 255), 'BLACK': (0, 0, 0),
          'RED': (255, 0, 0), 'GREEN': (0, 255, 0), 'BLUE': (0, 0, 255),
          'PURPLE': (128, 0, 128), 'ORANGE': (255, 70, 0),
          'YELLOW': (255, 255, 0),
          'TURQUOISE': (64, 208, 192), 'GRAY8': (128, 128, 128),
          'GRAY4': (64, 64, 64),
          'GRAYC': (192, 192, 192), 'GOLD': (255, 199, 0),
          'MAROON': (128, 0, 0)}

# Physical Values
AU = 1.49597871e11  # m
G = 6.67384e-11  # m^3 * kg^-1 * s^-2
M_SOL = 1.9891e30  # kg

NAMES = ['Me', 'V', 'E', 'Ma', 'J', 'S', 'U', 'N', 'P']
MASSES = [.330e24, 4.87e24, 5.97e24, .642e24, 1898e24, 568e24, 86.8e24, 102e24,
          .0131e24]
RADII = [2.440e6, 6052e6, 6378e6, 3.396e6, 7.1492e7, 6.0268e7, 2.5550e7,
         2.4750e7, 1.195e6]
DIST = [4.600e10, 1.0750e11, 1.4710e11, 2.0660e11, 7.4050e11, 1.35260e12,
        2.74130e12, 4.44450e12, 4.43500e12]
DIST_AU = [.387, .723, 1.000, 1.524, 5.203, 9.523, 19.208, 30.087, 39.746]
DIST_AU = [x / AU for x in DIST]
VELOCS = [5.897e4, 3.525e4, 3.029e4, 2.650e4, 1.371e4, 1.018e4, 7.11e3, 5.50e3,
          6.10e3]
COL = [COLORS['RED'], COLORS['GOLD'], COLORS['GREEN'], COLORS['MAROON'],
       COLORS['ORANGE'],
       COLORS['YELLOW'], COLORS['TURQUOISE'], COLORS['BLUE'], COLORS['PURPLE']]

MOON_NAMES = ['CALLISTO', 'GANYMEDE', 'EUROPA', 'IO', 'LUNA']
MOON_PLANET = ['J', 'J', 'J', 'J', 'E']
MOON_MASSES = [107.6e21, 148.2e21, 48.0e21, 89.3e21, 7.34e22]
MOON_RADII = [2.4105e6, 2.681e6, 1.561e6, 1.765e6, 3.476e6]
MOON_DIST = [1.883e9, 1.070e9, 6.71e8, 4.22e8, 3.844e8]
MOON_DIST_AU = [x / AU for x in MOON_DIST]
MOON_VELOCS = [8.2e3, 10.9e3, 13.7e3, 17.3e3, 1.023e3]

pygame.init()

# Runtime values
DEBUG_CONSOLE_ON = False
DEBUG_ON = False
IS_RUNNING = True
AUTO_UPDATE = True
DONE = False
clock = pygame.time.Clock()
timescale_i = 3
timescale = TIMES[timescale_i]
zoomlevel = 1
max_calcs = 50  # per body per timestep
refresh_bound_rate = 1000  # refresh bounds after this many sim steps
following = False
follow_i = 0

# SCREEN_X_MAX = SCREEN_Y_MAX = 800
# SCREEN_DEFAULT = [SCREEN_X_MAX, SCREEN_Y_MAX]

# SCREEN_X_CENTER = SCREEN_Y_CENTER = 400  #screen center is at (50, 50) AU
# SCREEN_CENTER_DEFAULT = [SCREEN_X_CENTER, SCREEN_Y_CENTER]

# COORD_BOUNDS = [-50, 50, -50, 50]  #-x, +x, -y, +y

# X_BOUND = (SCREEN_X_MAX / (COORD_BOUNDS[1] - COORD_BOUNDS[0]))
# Y_BOUND = (SCREEN_Y_MAX / (COORD_BOUNDS[3] - COORD_BOUNDS[2]))
OBJSIZE = 2


class Display:
    """
    A display object for the pygame
    """

    def __init__(self, pX=800, pY=800, minX=-50.0, maxX=50.0, minY=-50.0,
                 maxY=50.0, fontsize=15):
        """
        Creates display object with passed graphic and spatial bounds.

        Specifically there are two sets of coordinates at work: those of the
        PyGame window (pX, pY), in pixels,  and those of the positions of the
        objects in space (minX - maxY), in AU.  The latter need to map to the former,
        which math is accomplished later on.

        :param pX: Pygame window X size
        :param pY: Pygame window Y size
        :param minX: Min (spatial) X position
        :param maxX: Max (spatial) X position
        :param minY: Min (spatial) Y position
        :param maxY: Max (spatial) Y position
        :param fontsize: Size of font
        :return:
        """
        self.COORD_BOUNDS = np.array([minX, maxX, minY, maxY])
        self.COORD_RANGE = self.COORD_BOUNDS[(1, 3),] - self.COORD_BOUNDS[
            (0, 2),]
        self.COORD_CENTER = (self.COORD_RANGE / 2) + self.COORD_BOUNDS[(0, 2),]
        self.PX_BOUNDS = np.array([0, pX, 0, pY])
        self.PX_RANGE = np.array([pX, pY])
        self.PX_CENTER = (self.PX_RANGE / 2).astype(int)
        self.PX_PER_COORD = (self.PX_RANGE / self.COORD_RANGE).astype(int)
        self.screen = pygame.display.set_mode(self.PX_RANGE)
        self.font = pygame.font.Font(None, fontsize)

    def fit(self, set):
        """
        Get new xy bounds based on position of objects in set + padding.
        :param set: A set of celestial bodies
        :type set: Body
        :return: None
        :rtype: None
        """
        new_bounds = np.array([min(a.dx_au for a in set),
                               max(a.dx_au for a in set),
                               min(a.dy_au for a in set),
                               max(a.dy_au for a in set)])
        new_bounds += np.array([-1, 1, -1, 1])
        self.COORD_BOUNDS = new_bounds
        self.boundCalcs()

    def follow(self, object, p=1.0):
        """
        Set spatial dimensions to the position of object, with padding p.
        :param object: A celestial object
        :type object: Body
        :param p: padding in AU
        :type p: float
        :return: None
        :rtype: None
        """
        self.COORD_BOUNDS = np.array([object.dx_au - p,
                                      object.dx_au + p,
                                      object.dy_au - p,
                                      object.dy_au + p])
        self.boundCalcs()

    def zoom(self, r=1.0, x=1.0, y=1.0):
        """
        Multiply current bounds by the factors x, y, and r
        :param r: Overall zoom
        :type r: float
        :param x: x zoom (fractional to zoom out)
        :type x: float
        :param y: y zoom (fractional to zoom out)
        :type y: float
        :return: None
        :rtype: None
        """
        self.COORD_BOUNDS = np.append(self.COORD_BOUNDS[0:2] * x * r,
                                      self.COORD_BOUNDS[2:4] * y * r)
        self.boundCalcs()

    def shift(self, x=1.0, y=1.0):
        """
        Shifts display linearly by x or y AU
        :param x: x shift (AU) (negative for left)
        :type x: float
        :param y: y shift (AU) (negative for up)
        :type y: float
        :return: None
        :rtype: None
        """
        self.COORD_BOUNDS = np.append(self.COORD_BOUNDS[0:2] + x,
                                      self.COORD_BOUNDS[2:4] + y)
        self.boundCalcs()

    def forceBounds(self, xmin=-10, xmax=10, ymin=-10, ymax=10):
        """
        Force boundaries to xmin, xmax, ymin, and ymax
        :param xmin: x min (AU)
        :type xmin: float
        :param xmax: xmax (AU)
        :type xmax: float
        :param ymin: ymin (AU)
        :type ymin: float
        :param ymax: ymax (AU)
        :type ymax: float
        :return: None
        :rtype: None
        """
        self.COORD_BOUNDS = np.array([xmin, xmax, ymin, ymax])
        self.boundCalcs()

    def boundCalcs(self):
        """
        Define range and center of coordinates, redefine pixel:AU factor.
        :return: None
        :rtype: None
        """
        self.COORD_RANGE = self.COORD_BOUNDS[(1, 3),] - self.COORD_BOUNDS[
            (0, 2),]
        self.COORD_CENTER = (self.COORD_RANGE / 2) + self.COORD_BOUNDS[(0, 2),]
        self.PX_PER_COORD = (self.PX_RANGE / self.COORD_RANGE).astype(int)

    def renderGrid(self):
        """
        Print bounds on edges of screen
        :return: None
        :rtype: None
        """
        output = [
            self.font.render(str(coord), 1, COLORS['WHITE'], COLORS['BLACK'])
            for coord in self.COORD_BOUNDS]
        output_pos = [(0, self.PX_CENTER[1]),
                      (self.PX_RANGE[0] - 50, self.PX_CENTER[1]),
                      (self.PX_CENTER[0], 0),
                      (self.PX_CENTER[0], self.PX_RANGE[1] - 15)]
        for x in xrange(len(output)):
            self.screen.blit(output[x], output_pos[x])

    def renderObjects(self, set):
        """
        Render either one or several celestial objects.
        :param set: One or several celestial objects.
        :type set: list
        :return: None
        :rtype: None
        """
        if type(set) is list:
            for o in set:
                pygame.draw.circle(self.screen, o.color,
                                   [o.display_x, o.display_y], OBJSIZE)
        else:
            pygame.draw.circle(self.screen, set.color,
                               [set.display_x, set.display_y], OBJSIZE)


class Body:
    """
    Describes a celestial body, affected by gravity and with gravity of its own.
    """
    count = 0

    # position (dx/dy) * AU, velocity (vx/vy) * m/s,
    # acceleration (ax/ay) * m/s^2, radius * m, and mass * kg
    def __init__(self, name="", dx=0, dy=0, vx=0, vy=0, radius=0, m=0,
                 color=COLORS['WHITE'], reference_body='Sol'):
        """

        :param name:
        :type name:
        :param dx:
        :type dx:
        :param dy:
        :type dy:
        :param vx:
        :type vx:
        :param vy:
        :type vy:
        :param radius:
        :type radius:
        :param m:
        :type m:
        :param color:
        :type color:
        :param reference_body:
        :type reference_body:
        :return:
        :rtype:
        """
        self.id = Body.count
        if name == '':
            self.name = 'Body #' + str(self.id)
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

    def sumForces(self, bodies):
        """
        Sum all the gravitational forces acting on the current body.

        Disregarding self and zero mass bodies, calculate each force acting
        on the current body.  The number of calculations depends on the
        timescale and max_calcs values, as well as the distance: closer
        bodies have more calculations because the forces are greater.

        :param bodies: a set of celestial objects with gravity.
        :type bodies: list[Body]
        :return: None
        :rtype: None
        """
        for body in bodies:
            if body.name == self.name or body.m <= 0:
                continue
            diffx = self.dx - body.dx
            diffy = self.dy - body.dy
            distance = math.sqrt(diffx ** 2 + diffy ** 2)

            # As written, this is needless subdivision
            #calculations = int(
            #    min(math.ceil(max_calcs / (math.log10(distance))), max_calcs))
            #segment_timescale = timescale / calculations
            segment_timescale = timescale / 100
            for x in xrange(0, int(timescale), segment_timescale):
                g = ((G * body.m) / distance ** 2) * segment_timescale
                theta = math.atan2(diffy, diffx)
                self.ax -= (g * math.cos(theta))
                self.ay -= (g * math.sin(theta))
                # if self.name == "GANYMEDE":
                #    print (body.name + " ax/ay: " + str(self.ax) + "/" + str(self.ay) + " d: " + str(distance) +
                #           " g: " + str(g) + " segTime: " + str(segment_timescale))

    def applyForce(self):
        """
        Discharge accelerations into the velocity vectors

        The acceleration is always AU/timestep^2, velocity is always AU/timestep
        :return:
        :rtype:
        """
        self.vx += self.ax
        self.vy += self.ay
        self.ax = self.ay = 0

    def applyVelocity(self):
        """
        Discharge velocity into displacement vectors

               AU
        v = -------- * timestep = AU
            timestep
        :return:
        :rtype:
        """
        self.dx += self.vx * timescale
        self.dy += self.vy * timescale
        self.dx_au = self.dx / AU
        self.dy_au = self.dy / AU

    def mapDisplayCoords(self):
        """

        :return:
        :rtype:
        """
        # self.display_x = int(self.dx_au * sc.PX_PER_COORD[0]) + sc.PX_CENTER[0]
        # self.display_y = int(self.dy_au * sc.PX_PER_COORD[1]) + sc.PX_CENTER[1]
        self.display_x = int(
            (self.dx_au - sc.COORD_CENTER[0]) * sc.PX_PER_COORD[0]) + \
                         sc.PX_CENTER[0]
        self.display_y = int(
            (self.dy_au - sc.COORD_CENTER[1]) * sc.PX_PER_COORD[1]) + \
                         sc.PX_CENTER[1]

    def makeDebugLines(self):
        """
        Unused
        :return: None
        :rtype: None
        """
        return [sc.font.render("name: " + self.name, 1, COLORS['WHITE'],
                               COLORS['BLACK']),
                sc.font.render("dx/dy: " + str(self.dx) + " " + str(self.dy), 1,
                               COLORS['WHITE'], COLORS['BLACK']),
                sc.font.render(
                    "dx/dy AU: " + str(self.dx_au) + " " + str(self.dy_au), 1,
                    COLORS['WHITE'], COLORS['BLACK']),
                sc.font.render(
                    "display x/y: " + str(self.display_x) + " " + str(
                        self.display_y), 1, COLORS['WHITE'], COLORS['BLACK']),
                sc.font.render("AU mag: " + str(
                    math.sqrt((self.dx_au ** 2) + (self.dy_au ** 2))), 1,
                               COLORS['WHITE'], COLORS['BLACK']),
                sc.font.render("vx/vy: " + str(self.vx) + " " + str(self.vy), 1,
                               COLORS['WHITE'], COLORS['BLACK']),
                sc.font.render("ax/ay: " + str(self.ax) + " " + str(self.ay), 1,
                               COLORS['WHITE'], COLORS['BLACK'])]


sc = Display(800, 800, -3.0, 50.0, 3.0, 50.0)
objects = [Body('Sol', 0, 0, 0, 0, 100, M_SOL)]

# Choice of VELOCS is arbitrary.  A dict() would be much more elegant...
for x in xrange(len(VELOCS)):
    objects.append(
        Body(NAMES[x], DIST_AU[x], 0, 0, VELOCS[x], 100, MASSES[x], COL[x]))

planets = {}

for p in objects:
    planets[p.name] = p

# Compile data for satellites
for x in xrange(len(MOON_VELOCS)):
    objects.append(
        Body(MOON_NAMES[x], MOON_DIST_AU[x], 0, 0, MOON_VELOCS[x], 100,
             MOON_MASSES[x], COLORS['WHITE'], MOON_PLANET[x]))

# Each satellite's position is offset by its reference body (planet, Sol)
for o in objects:
    o.dx += planets[o.reference_body].dx
    o.dy += planets[o.reference_body].dy
    o.vy += planets[o.reference_body].vy
    o.vx += planets[o.reference_body].vx

sc.fit(objects)
sc.renderGrid()
sc.forceBounds(-50, 50, -50, 50)
time_elapsed = 0
sim_steps = 0

def updateSim(bodies):
    """
    Calls all the update methods for object positions, display, and time.

    The heavy lifting is done in each Body's force calculation methods.  The
    current method serves to bring all of the different update steps together.
    :param bodies: a set of celestial bodies.
    :type bodies: list[Body]
    :return: None
    :rtype: None
    """
    if AUTO_UPDATE:
        if sim_steps % refresh_bound_rate == 0:
            sc.fit(bodies)
    sc.screen.fill(COLORS['BLACK'])
    sc.renderGrid()
    for obj in bodies:
        obj.sumForces(bodies)
        if DEBUG_ON:
            column = [a.makeDebugLines() for a in bodies]
    for obj in bodies:
        obj.applyForce()
        obj.applyVelocity()
        obj.mapDisplayCoords()
    if DEBUG_ON:
        for x in xrange(len(column)):
            for y in xrange(len(column[x])):
                sc.screen.blit(column[x][y], ((x) * 150, 15 * y))
    sc.renderObjects(bodies)
    global time_elapsed
    time_elapsed += timescale / (3600 * 24)
    output = sc.font.render(str(time_elapsed) + " days", 1, COLORS['WHITE'],
                            COLORS['BLACK'])
    sc.screen.blit(output, (10, 10))
    pygame.display.flip()

# Main loop.  Note the control scheme in the block comment below.
while not DONE:
    SINGLE_TICK = False
    for event in pygame.event.get(pygame.QUIT):
        DONE = True
    for event in pygame.event.get(pygame.KEYDOWN):
        """
        NL  /   *   -
        7   8   9
        4   5   6   +
        1   2   3   <enter>
            0   .

        N/A     Zoom+   Zoom-   Speed-
        Calc-   Up      Calc+
        Left    Reset   Right   Speed+
        Obj-    Down    Obj+    Pause
                Step    Reset

        """
        if event.key == pygame.K_KP_DIVIDE:
            zoomlevel /= 2.0
            sc.zoom(zoomlevel)
        elif event.key == pygame.K_KP_MULTIPLY:
            zoomlevel *= 2.0
            sc.zoom(zoomlevel)
        elif event.key == pygame.K_KP_MINUS:
            timescale_i -= max(0, timescale_i > 0)
            timescale = TIMES[timescale_i]
        elif event.key == pygame.K_KP7:
            max_calcs -= max(0, max_calcs > 2)
        elif event.key == pygame.K_KP8:
            sc.shift(0.0, 1.0)
        elif event.key == pygame.K_KP9:
            max_calcs += 1
        elif event.key == pygame.K_KP4:
            sc.shift(-1.0, 0.0)
        elif event.key == pygame.K_KP5:
            sc.screen.fill(COLORS['BLACK'])
        elif event.key == pygame.K_KP6:
            sc.shift(1.0, 0.0)
        elif event.key == pygame.K_KP_PLUS:
            timescale_i += max(0, timescale_i < 6)
            timescale = TIMES[timescale_i]
        elif event.key == pygame.K_KP1:
            OBJSIZE -= max(0, OBJSIZE > 2)
        elif event.key == pygame.K_KP2:
            sc.shift(0.0, -1.0)
        elif event.key == pygame.K_KP3:
            OBJSIZE += 1
        elif event.key == pygame.K_KP_ENTER:
            IS_RUNNING = not IS_RUNNING
        elif event.key == pygame.K_KP0:
            SINGLE_TICK = True
        elif event.key == pygame.K_KP_PERIOD:
            True
        elif event.key == pygame.K_ESCAPE:
            DONE = True
        elif event.key == pygame.K_LEFTBRACKET:
            follow_i -= max(0, follow_i > 0)
        elif event.key == pygame.K_RIGHTBRACKET:
            follow_i += max(0, follow_i < (len(objects) - 1))

    clock.tick(60)

    if IS_RUNNING or SINGLE_TICK:
        sc.follow(objects[follow_i], zoomlevel)
        sim_steps += 1
        updateSim(objects)
        SINGLE_TICK = False
