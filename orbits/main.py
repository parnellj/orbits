from __future__ import print_function, division
from vpython import *

scene.userzoom = True
scene.userspin = True
scene.width = 1600
scene.height = 900

VISIBLE_RADIUS_MULTIPLIER = 10
G = 6.674e-11

class Orbit:
    def __init__(self, a, e, i, O, o, mu):
        """
        a. Semi Major Axis. Size. Half of the length (in meters) of the major axis.
        e. Eccentricity. Shape. Depends on r of the periapsis, r of apoapsis, and length of (a)
        i. Inclination. Tilt. Inclination in degrees from the equatorial plane to the orbital plane.
        O. Longitude of the Ascending Node. Swivel. Angle between vernal equinox and the AN.
        o. Argument of Periapsis. Location of periapsis.  Angle from AN to periapsis, CCW from North
        mu. True Anomaly. Position. The angle in degrees from orbit’s periapsis to orbiting body.

        :param a:
        :param e:
        :param i:
        :param O:
        :param o:
        :param mu:
        """
        a, e, i, O, o, mu = a, e, i, O, o, mu


class Body:
    def __init__(self, position, velocity, mass, radius, shape=sphere, color=color.red):
        self.position = vector(*position)
        self.velocity = vector(*velocity)
        self.force = vector(0, 0, 0)
        self.mass = mass
        self.radius = radius
        self.color = color

        self.model = shape(pos=self.position, radius=self.radius * VISIBLE_RADIUS_MULTIPLIER,
                           color=self.color)

    def queue_force(self, force_vector):
        raise NotImplementedError('Body.apply_force not implemented yet')

    def update_position(self):
        self.model.pos = self.position


def r_to_xyz(azimuth, polar, radius):
    x = radius * cos(azimuth) * sin(polar)
    y = radius * sin(azimuth) * sin(polar)
    z = radius * cos(polar)
    return (x, y, z)


def calc_grav(body_1, body_2):
    """
    Calculate the vector force exerted on body 2 by body 1
    :param body_1:
    :param body_2:
    :return:
    """
    relative_position = body_2.position - body_1.position
    unit_vector = relative_position / relative_position.mag
    force = (-G * body_1.mass * body_2.mass / relative_position.mag ** 2) * unit_vector
    return force

sun = Body((0, 0, 0), (0, 0, 0), 1.988e30, 6.957e8, sphere, color.red)

earth_pos = r_to_xyz(0, radians(90 - 7.155), 1.521e11)

earth = Body(earth_pos, (0, 2.93e4, 0), 5.972e24, 6.371e8, sphere, color.blue)

dt = 1

for i in range(0, 367 * 24 * 60 * 60, dt):
    grav_force = calc_grav(sun, earth)
    grav_accel = grav_force / earth.mass
    earth.velocity += (grav_accel * dt)
    earth.position += (earth.velocity * dt)
    earth.update_position()
    if i % (24 * 60 * 60) == 0:
        print("day {0}".format(i / (24 * 60 * 60)))
        print(earth.velocity, earth.position)
