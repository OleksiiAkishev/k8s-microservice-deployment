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

21. Install Linkerd for the mTLS between pods. 
    Linkerd of doc: https://linkerd.io/2-edge/tasks/install/
    curl -sL https://run.linkerd.io/install | sh
    export PATH=$PATH:$HOME/.linkerd2/bin
    linkerd check --pre - check cluster compatibility
    linkerd install | kubectl apply -f -  - install Linkerd control plane
    Mostly will have error to install linkerd install --crds
    Then to install Gateaway API:
    kubectl apply --server-side -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.5.0/standard-install.yaml
    official doc: https://gateway-api.sigs.k8s.io/guides/getting-started/
    Now can run: 
        linkerd install | kubectl apply -f -
    Final check:
        linkerd check

22. Follow official sprig docs to build templates:
    https://masterminds.github.io/sprig/string_slice.html
    https://github.com/Masterminds/sprig?tab=readme-ov-file

23. Added namespace and configmap templates
    23.1 Learned how to use the templates helpers if need common logic to be executed.
24. Separate debug flag for the helm:
    helm template . --debug
25. Learn how to debug the context, add debug for render, e.g.
    apiVersion: v1
    kind: Namespace
    metadata:
        debug-context: |
    {{ toYaml . | indent 4 }}
Note: chart debug it is not like a code debug, the output will be available only if there are no errors during rendering and the final render output will have the debug context.

26. Use an official Sprig library to Debug helm charts.
    https://masterminds.github.io/sprig/string_slice.html
    Online yaml validator: https://www.yamllint.com/
    Example of error:
        Error: template: k8s-python-api-helm/templates/namespace.yaml:4:11: executing "k8s-python-api-helm/templates/namespace.yaml" at <include "k8s-python-api-helm.namespace" .>: error calling include: template: k8s-python-api-helm/templates/_helpers.tpl:70:14: executing "k8s-python-api-helm.namespace" at <slice $parts 0 3>: error calling slice: list should be type of slice or array but map
    The key was to check what produced by list function, apparently based on the doc it gives the map and not array which was expected by slice function.
27. Try to deploy on cluster now:
        helm install --generate-name ./ or helm install aks-pn-release ./
    Delete release:
        helm uninstall <release-name>
28. Learn on the Deployment and pods labels, how and where to define them and why it is matter.
    Deployment is asking  - which pod belongs to me?
        spec.selector.matchLabels --> the filter
            The exact identifier which help to Deployment to find its pods
        spec.template.metadata.labels --> the labels assigned to pod

    Rule: what is defined in the matchLabels must exist in the labels and vice versa
28.1 To understand where the pod template definition is started, example:
    apiVersion: apps/v1
kind: Deployment
metadata:
  namespace: {{ include "k8s-python-api-helm.namespace" . }}
  name: {{ include "k8s-python-api-helm.fullname" . }}
  labels:
    {{- include "k8s-python-api-helm.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "k8s-python-api-helm.selectorLabels" . | nindent 6 }}
  template:  # <---- This is starting place of the POD template
    spec:    # <---- POD spec starts here
      containers:
28.2 Helm upgrade after deployment fix.
    helm upgrade <release-name> ./
28.3 Check the deployment after install:
    Release "aks-pn-release" has been upgraded. Happy Helming!
    NAME: aks-pn-release
    LAST DEPLOYED: Mon Mar 23 11:10:14 2026
    NAMESPACE: default
    STATUS: deployed
    REVISION: 2
    DESCRIPTION: Upgrade complet

- helm list
- kubectl get namespaces
- kubectl get deployment -n 
- kubectl get events <deployment> -n

29. Troubleshoot on failed deployment
    kubectl get deployment <deployment> -n <namespace> -o yaml
    kubectl get pods -n
    kubectl get events -n
    kubectl get events -n <namespace> \
      --field-selector involvedObject.name=<pod-name>
    kubectl get pod <pod-name> -n <namespace> -o wide
    kubectl describe pod <pod> -n