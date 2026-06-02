import os
from pathlib import Path
import logging

#logging string
# logging.basicConfig(level=logging.INFO, format='[%(asctime)s]: %(message)s:')

project_name = 'landlink'

list_of_files = [
    ".github/workflows/main.yaml",
    f"src/{project_name}/__init__.py",
    f"src/{project_name}/components/__init__.py",
    f"src/{project_name}/utils/__init__.py",
    f"src/{project_name}/config/__init__.py",
    f"src/{project_name}/config/configuration.py",
    f"src/{project_name}/pipeline/__init__.py",
    f"src/{project_name}/entity/__init__.py",
    f"src/{project_name}/constants/__init__.py",
    "config/config.yaml",
    "dvc.yaml",
    "params.yaml",
    "requirements.txt",
    "setup.py",
    "research/trials.ipynb",
    "templates/index.html"


]

for fliepath in list_of_files:
    fliepath = Path(fliepath)

    filedir , filename = os.path.split(fliepath)

    if filedir != "":
        os.makedirs(filedir, exist_ok = True)

    if (not os.path.exists(filename)) or (os.path.getsize(fliepath) == 0):
        with open(fliepath , 'w') as f:
            pass
    
    else:
        print("file already exists")