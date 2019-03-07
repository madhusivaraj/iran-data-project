import os.path
from setuptools import setup, find_packages
 
with open(os.path.join(os.path.dirname(__file__), 'requirements.txt')) as f:
    reqs = []
    for line in f:
        reqs.append(line.strip().split('=')[0])

setup(
    name = 'scraper',
    version = '0.0.1',
    zip_safe = False,
    packages = find_packages(),
    install_requires = reqs,
)
