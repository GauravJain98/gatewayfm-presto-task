# GatewayFM Presto Task

## Setup and view dashboard

### Prerequisites

- kind
- kubectl
- helm

### Setup

1. Create Kind Cluster

```bash
# Create cluster
kind create cluster --name ethereum-devnet

# Verify cluster
kubectl cluster-info
kubectl get nodes
```

2. Setup Observability Stack

```bash
git clone https://github.com/GauravJain98/gatewayfm-presto-task
cd gatewayfm-presto-task

kubectl create ns monitoring

# Add Helm repositories
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Deploy Prometheus
helm install prometheus prometheus-community/prometheus \
  -n monitoring \
  --version 27.23.0 \
  -f manifests/observability/prometheus/values.yaml

# Deploy Grafana with dashboard
kubectl apply -f manifests/observability/grafana/ethereum-dashboard-configmap.yaml
helm install grafana grafana/grafana \
  -n monitoring \
  --version 10.1.5 \
  -f manifests/observability/grafana/values.yaml
```

3. Deploy Etherum Geth node

```bash
kubectl create ns geth

kubectl apply -f manifests/geth/
```

4. Deploy Load Generator

```bash
kubectl create ns load-generator

kubectl apply -f manifests/load-generator/
```

To increase the TPS you can update the `manifests/load-generator/deployment.yaml` `.spec.template.spec.containers[0].env[1].value` i.e the value of the `TARGET_TPS` value

5. View Grafana Dashboard

Run the following command

```bash
kubectl port-forward -n monitoring svc/grafana 3000:80
```

Go to [the dashboard](http://localhost:3000/d/eth-devnet-dashboard/ethereum-devnet-performance-dashboard)

username: `admin`
password: `password`

## Commands to verify 6-second block production and persistence

### 6-second block generation

You can verify the block generation in [this panel](http://localhost:3000/d/eth-devnet-dashboard/ethereum-devnet-performance-dashboard?orgId=1&from=now-30m&to=now&timezone=browser&viewPanel=panel-6) of the dashboard

You can also verify it by running the following script with the port forward in another terminal

Port Forward (The while is there do handle the persistence test)

```bash
while True; do kubectl port-forward -n geth svc/geth-devnet-service 8545:8545:;done
```

Verify

```bash
./blocktime.sh
```

### Persistence

In order to verify persistence you can restart the pod and see that the block number does not reset, also the same dashboard shows [panel](<http://localhost:3000/d/eth-devnet-dashboard/ethereum-devnet-performance-dashboard?orgId=1&from=now-30m&to=now&timezone=browser&viewPanel=panel-6>) shows the block numbers increasing

```bash
./persistance.sh
```

## Teardown

```bash
# Delete applications
helm uninstall grafana -n monitoring
helm uninstall prometheus -n monitoring
kubectl delete -f manifests/load-generator/
kubectl delete -f manifests/geth/

# Delete namespaces
kubectl delete namespace monitoring load-generator geth

# Delete Kind cluster
kind delete cluster --name ethereum-devnet
```

## Architecture and Design Choices

