## Setup Observbility Stack

```bash
kubectl create ns monitoring
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts

helm install prometheus prometheus-community/prometheus -n monitoring -f manifests/observability/prometheus/values.yaml
helm install grafana grafana/grafana -n monitoring -f manifests/observability/grafana/values.yaml
```


## Setup load generator
```
kubectl create ns load-generator
kubectl apply -f load-generator
```