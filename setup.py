try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

config = {
	'name': 'Orbital Mechanics Learning Tool',
	'version': '0.1',
	'url': 'https://github.com/parnellj/orbits',
	'download_url': 'https://github.com/parnellj/orbits',
	'author': 'Justin Parnell',
	'author_email': 'parnell.justin@gmail.com',
	'maintainer': 'Justin Parnell',
	'maintainer_email': 'parnell.justin@gmail.com',
	'classifiers': [],
	'license': 'GNU GPL v3.0',
	'description': 'Experiments with principles of orbital mechanics.',
	'long_description': 'Experiments with principles of orbital mechanics.',
	'keywords': '',
	'install_requires': ['nose'],
	'packages': ['orbits'],
	'scripts': []
}
	
setup(**config)
