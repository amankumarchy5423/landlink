import setuptools
from src.landlink import *

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()
    logger.info("README.md loaded successfully.")


__version__ = "0.0.0"

REPO_NAME = "landlink"
AUTHOR_USER_NAME = "Aman"
SRC_REPO = "landlink"



setuptools.setup(
    name=SRC_REPO,
    version=__version__,
    author=AUTHOR_USER_NAME,
    
    description="A land deal marketplace platform built with Flask ",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=f"https://github.com/{AUTHOR_USER_NAME}/{REPO_NAME}",
    project_urls={
        "Bug Tracker": f"https://github.com/amankumarchy5423/landlink.git",
    },
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src")
)
logger.info("setup.py executed successfully.")