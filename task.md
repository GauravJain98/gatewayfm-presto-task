Presto Blockchain DevOps Engineer — Test Assignment 
Objective 
Deploy and operate a single-node Ethereum devnet using Geth in developer mode on Kubernetes, perform load testing with Python, and visualize key performance metrics in Grafana. 
Requirements & Deliverables 
Use Geth in -dev mode as the blockchain client. The network must: 
• Run as a single node. 
• Produce blocks every 6 seconds. 
• Persist state between restarts (e.g., via a PVC or equivalent). 
• Include prefunded accounts, specifically 0x62358b29b9e3e70ff51D88766e41a339D3e8FFff funded with 100 ETH, and any other accounts you need to complete the assignment. 
Implement a Python workload that: 
• Connects to the node’s JSON-RPC interface. 
• Generates configurable transaction load with adjustable TPS and concurrency. 
• Measures and records TPS, RPS, and MGas/s, latency and failure rates. 
• Stores or exposes collected data for Grafana visualization using any data pipeline or observability approach you prefer. 
Provide a Grafana dashboard showing at least: 
• Achieved TPS over time 
• RPC RPS over time 
• MGas/s over time 
• Latency 
• Failure rates 
• Any additional useful network metrics of your choice 
Deliver clean Kubernetes manifests (or a Helm chart) for all components: 
• Blockchain node 
• Observability stack 
• Load generator 
Include a CI/CD pipeline (GitHub Actions) that: 
• Lints YAML and Python files 
• Builds the workload Docker image and pushes it to the GitHub repo.
Provide a clear README with: 
• Setup and teardown instructions, should include scripts to deploy everything to local Kubernetes cluster (Kind). 
• Commands to verify 6-second block production and persistence. 
• Steps to run the Python workload and open the Grafana dashboard. 
• Short explanation of your architecture and design choices. 
Notes 
• Feel free to contact us if you have any questions during the test assignment. 
• Using AI tools (like ChatGPT or Copilot) is allowed and encouraged, as long as you fully understand and can explain the code and design choices you submit.
