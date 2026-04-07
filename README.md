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
6.1 Install pytest inside .venv
    pip install pytest
6.2 Python tests run:
    python3 -m pytest
7. Github master branch rules added 
8. Create main.py
9. Create simple run python API application run on 8000
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
10. Create Dockerfile and create 2 layers (build, runtime)
11. Use auto command to create py requirements file:
    pip freeze > requirements.txt
11.1 Install all from the requirements
    pip install -r requirements.txt
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
    - kind create cluster --name <cluster_name>
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
How does the helm knows where to deploy, it check if there is a cluster install via context:
    kubectl config current-context

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

30. Create ci/cd process to validate and deliver python app.
    - __init__.py added and main.py moved to app folder to make the main.py explicitly as module not just folder.
    - pytest added to requirements.txt
    - compilation added: python -m compileall .
    - linting added: ruff check .
    - pytest added context path: env:
                                    PYTHONPATH: .

31. Docker packages are pushed to the Github packages via CI workflow process.
32. Add secret link to the repo secrets
33. Initial cluster creation on Github - kind:
    - cluster create
    - cluster check
34. Create CD process for secret cluster creation and bind it to the pull secrets process from registry.

35. Before rollout ephermal kind cluster on Github add more functionality and test on local.
    35.1 Add the secret with the token on local cluster
    kubectl create secret docker-registry ghcr-secret \
            --docker-server=https://ghcr.io \
            --docker-username=${{ github.actor }} \
            --docker-password=${{ secrets.GHCR_TOKEN }} \
            --docker-email=${{ github.actor }}@users.noreply.github.com

36. Learn on Helm + GO interpreting processes:
        how GO parses the objects

        Object/dictionary (key: val) --> map[string]inteface{}
        Array/list (- item) --> []inteface{}
        String/scalar ("test") --> string
        Number/bool --> int, float64, bool

        Example1: in yaml

        imagePullSecrets:
        - name: my-secret

        How GO sees that
        []interface{}{                  // outer list → []interface{}
            map[string]interface{}{     // inner object → map[string]interface{}
                "name": "my-secret"     // string value inside the map
            }
        }

        Example2:
        imagePullSecrets:
        - "1"
        - "2"
        
        How GO sees that

        []interface{}{"1", "2"}

        When error happens like:
        wrong type for value; expected string; got []interface {}
        Need to use toYaml function
        Why use | toYaml:
        Without it helm parses and evaluates the expression inside {{ }} as Go:
        []interface{}{} --> invalid syntax, then the  pipe (|) toYaml transorms a GO object to the yaml format, even it seems redundant as the object already stored in the values.yaml in the correct format, as
        imagePullSecrets:
        - name: my-secret

37. TO avoid discrepency between helm release and the cluster release specify the release name when deploying on cluster, example:
helm upgrade --install k8s-python-api ./k8s-python-api-helm \
  --namespace <namespace_name> --create-namespace
  Note: even if namespace will exist during helm templates apply the only discrepency will be taken into consideration.
--install: if release not exist, create if yes - update
38. Learned index, access an element by specified position:
    name: {{ (index .Values.imagePullSecrets 0).name }}
39. If local helm context has more than one values yaml file, then command must have the explicit name of them:
    helm template my-app ./chart \
        -f values.yaml \
        -f secrets-values.yaml \
        -f prod-values.yaml
Note:
    if values.yaml inside chart, need to specify the exact:
    -f ./chart/values.yaml
40. Deploy on local with secret creation
41. describe and get difference learned:
    get - quick overview in the desire format, e.g., 
        kubectl get pods -n my-namespace
        kubectl get deployment <name> -n <namespace> -o yaml
    describe - detailed human-readable information + events.
        kubectl describe pod app-123 -n my-namespace
42. Troubleshoot on the error:
 failed to pull and unpack image "ghcr.io/oleksiiakishev/k8s-microservice-deployment/k8s-python-api:latest": failed to resolve reference "ghcr.io/oleksiiakishev/k8s-microservice-deployment/k8s-python-api:latest": failed to authorize: failed to fetch anonymous token: unexpected status from GET request to https://ghcr.io/token?scope=repository%3Aoleksiiakishev%2Fk8s-microservice-deployment%2Fk8s-python-api%3Apull&service=ghcr.io: 401 Unauthorized

 - check with local cli: 
    - docker login ghcr.io -u <username> -p <token>
    - try pull now: docker pull ghcr.io/<owner>/<repo>/<image>:<tag>, e.g., hcr.io/oleksiiakishev/k8s-microservice-deployment/k8s-python-api:latest
- check (describe) the secret if the name is correct
- check the imagePullSecrets if correct in deployment with describe as well.
- learned that for the pull secret the secret type must be of the type:
    kubernetes.io/dockerconfigjson and not opaque
For that the manual command can be used:
 kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=my \
  --docker-password=token \
  --docker-email=email

then in the describe can see:
t
Name:         ghcr-secret
Namespace:    default
Labels:       <none>
Annotations:  <none>

Type:  kubernetes.io/dockerconfigjson

Data
====
.dockerconfigjson:  96 bytes

the correct type, thus the same pattern to be followed

43. Learned on the flow for the helm upgrade
helm upgrade --install
      │
      ▼
Templates rendered using values.yaml
      │
      ▼
Resources applied to cluster
  ├─ Namespace
  ├─ Secrets / ConfigMaps
  ├─ Services
  └─ Deployments
        │
        ▼
Deployment creates ReplicaSet
        │
        ▼
ReplicaSet creates Pods
        │
        ▼
Pods check imagePullSecrets → pull images
        │
        ▼
Containers start

where applied to the cluster, means with real apply command.

44. Learned on the correct deployment restart command:
    kubectl rollout restart deployment k8s-python-api-deployment -n k8s-python-api

    - restart all pods in the deployment
    - triggers a rolling restart

45. Filter on the container name when describe pod
    kubectl describe pod k8s-python-api-7d9f4c5f9 -n <namespace> | grep -A 5 "Containers:"
    OR
    kubectl get pod k8s-python-api-7d9f4c5f9 -n <namespace> -o jsonpath='{.spec.containers[*].name}'
    OR for all properties:
    kubectl get pod k8s-python-api-deployment-66d477bc57-gf8c7 -n k8s-python-api -o jsonpath='{.spec.containers[*]}'

46. Check container logs:
    kubectl logs k8s-python-api-deployment-66d477bc57-gf8c7 -c k8s-python-api-helm -n k8s-python-api

47. Check how to hit the container on the cluster

48. Refacor:
    - added infra (ingress, sa, namespace)
    - segregated infra and app

49. kubectl cluster-info dump
    The complete state of the cluster;
    To avoid huge output - use grep.
        Example: kubectl cluster-info dump | grep authorization-mode
50. Learn on services:
        ```
        Client (browser)
            │
            ▼
        NodePort Service (Traefik)  ── external entry point, port e.g. 30443
            │
            ▼
        Traefik Pod (Ingress Controller) ── routes traffic to backend services
            │
            ▼
        ClusterIP Service (App) ── internal routing
            │
            ▼
        Application Pod ── container listening on target port (e.g., 443)
        ```

        ### Short Explanation

        * **NodePort Service** → exposes Traefik externally
        * **Traefik Pod** → ingress controller, handles routing, TLS, rules
        * **ClusterIP Service** → internal access to application pod/ exposes Application (e.g., web api internally)
        * **App Pod** → the actual container serving the application

        > TL;DR: External → NodePort → Traefik → ClusterIP → Pod

        This captures the core flow for external-to-internal traffic via Traefik.

51. Traefik deployed and running, as expected error regarding SA
    "Failed to watch" err="failed to list *v1alpha1.IngressRouteUDP: ingressrouteudps.traefik.io is forbidden: User \"system:serviceaccount:ingress:traefik-ingress-controller\" cannot list resource \"ingressrouteudps\" in API group \"traefik.io\" at the cluster scope" logger="UnhandledError" reflector="k8s.io/client-go@v0.34.3/tools/cache/reflector.go:290" type="*v1alpha1.IngressRouteUDP"

52. How to check if particular service account is allowed to do the action:
        kubectl auth can-i list services \
  --as=system:serviceaccount:ingress:traefik-ingress-controller
  Flow:
    kubectl auth can-i -> API server -> RBAC engine -> returns yes/no
    etcd = the filing cabinet where all rules are stored
52.1 Check all roles:
    kubectl get roles -A
    kubectl get clusterroles
Note: 
    - the role has only rights where it exists, it doesn't have the ability to access outside specified namespace.
    - the cluster role is cluster-wide, can go everywhere.
52.2 Check the role bindings:
    kubectl get rolebindings -A
    kubectl get clusterrolebindings
Note:
    - role binding binds a Role to the SA in the namespace.
    - cluster role binding the same concept, role(cluster) to SA.
52.3 Check what the SA can do in the CLuster:
    kubectl auth can-i --list \
  --as=system:serviceaccount:ingress:traefik-ingress-controller

53. To eliminate the upper errors:
    - Cluster Role template
    - Cluster Role Binding template
    - CRDs to be installed:
        kubectl apply -f https://raw.githubusercontent.com/traefik/traefik/v3.6/docs/content/reference/dynamic-configuration/kubernetes-crd-definition-v1.yml