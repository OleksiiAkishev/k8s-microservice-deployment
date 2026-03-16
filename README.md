# k8s-microservice-deployment

1. Created Github repo.
2. SSH connection from wsl ubuntu to repo.
3. Install python on Ubuntu:
    sudo apt update && sudo apt install -y python3-venv python3-pip
4. Create a python env:
    python3 -m venv .venv
5. Activate env
    source .venv/bin/activate
    Now you are inside it: (.venv)
Note: exit from env:
    deactivate
6. Install dependecies if any, e.g (Prometheus):
    pip install fastapi uvicorn prometheus-client

7. Github master branch rules added 
8. Create main.py
9. Create simple run python API application run on 8000
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
10. Create Dockerfile and create 2 layers (build, runtime)
11. Use auto command to create py requirements file:
    pip freeze > requirements.txt
12.