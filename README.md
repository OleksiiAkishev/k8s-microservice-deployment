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
12. Build image with
    docker build -t k8s-python-app:1 .
        Reminder the . is a build context here, the path the dockerfile is
13. Check images, run built image:
    docker images 
    docker run -p 8000:8080 k8s-python-app:1
- Tried to run with the detached from terminal:
    docker run -p 7000:8080 -d k8s-python-app:1
14. Check the running docker container:
    docker exec -it <container_id> /bin/sh
        exec: run a command inside running container
        -it: interactive terminal (keeps open)
        /bin/sh : lightweight terminal, also /bin/bash can try
    Example without -it:
        docker exec 1fac9c0e1256 cat main.py
        --> no terminal kept open
        --> provided command will be output to the terminal
15. Install helm charts locally and create a boilerplate 
    sudo snap install helm
    helm create k8s-python-api-helm
16. Learn what is the Service of type ClusterIP:
    - allows internal communication between pods.
    - pods communicates only via service.
    - provides static ip, no changes:
        means even if pod A destroyed, a new pod B will have the same IP and other pods still can communicate to it. 
    - pods scalling: if more than one pod replicate deployed, a cluster ip works in this case a load balancer and distributes the requests beetwen pods.
17. Render or simulate real helm install:
    - helm template test ./k8s-python-api-helm
    - helm install --dry-run --debug my-release ./k8s-python-api-helm  --> simulation of full Helm install without deploying it
18. Troubleshoot
    FYI:
     - helm list : list all releases

19. Install 'kind (Kubernetes in Docker)' to be able to have own local kubernetes cluster
    - curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64
    - chmod +x ./kind
    - sudo mv ./kind /usr/local/bin/kind
19.1 Create a cluster
    - kind create cluster
    Note: to release resources after your work completed, you can delete cluster with:
        kind delete cluster
19.2 After installion is done, check your cluster:
    kubectl get nodes
    Result:
        NAME                 STATUS   ROLES           AGE    VERSION
        kind-control-plane   Ready    control-plane   119s   v1.35.1
19.3 Cluster status check:
    kubectl cluster-info
        Kubernetes control plane is running at https://127.0.0.1:46673
        CoreDNS is running at https://127.0.0.1:46673/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

20. Return back to the values.yaml, where the helm template gives parsing error, the line which is pointed by helm cannot be really that line which you need to fix. Try to install and user yaml lints instead.
    - sudo snap install yq
    - yq eval '.' ./k8s-python-api-helm/values.yaml
    Result: Error: bad file './k8s-python-api-helm/values.yaml': yaml: line 6: found unexpected end of stream