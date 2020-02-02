import io

from setuptools import find_packages
from setuptools import setup

with io.open("README.md", "rt", encoding="utf8") as f:
    readme = f.read()

setup(
    name="creepo",
    version="1.0.0",
    url="git@github.com:dooleydiligent/creepo.git",
    license="BSD",
    maintainer="lane",
    maintainer_email="lane@joeandlane.com",
    description="A rough sketch of a multi-format caching repository.",
    long_description=readme,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=["bottle", "requests", "lxml", "urllib3", "paste"],
    extras_require={"test": ["pytest", "coverage"]},
)
