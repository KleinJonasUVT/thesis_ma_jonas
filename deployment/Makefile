# Make sure these variables correspond with the .yaml configuration files!
image_path := ..
image_name := "tai-coursecatalogue"
image_version := "0.1.0"
envs_path := ..\secrets\prod.env

fetch_terraform_output:
	@echo "Fetching resource outputs using terraform"

	$(eval RG := $(shell terraform output resource_group_name))
	@echo "\nResource group '$(RG)'"

	$(eval CN := $(shell terraform output cluster_name))
	@echo "\nCluster '$(CN)'"
 
	$(eval ACR := $(shell terraform output acr_name))
	@echo "\nContainer registry '$(ACR)'"

connect_to_cluster:
	@echo "Connecting to cluster $(CN) in resource group $(RG)"
	az aks get-credentials --resource-group $(RG) --name $(CN)

setup_dashboard:
	@echo "Creating Service Account and Cluster Role Binding"
	kubectl create serviceaccount dashboard-admin-sa
	kubectl create clusterrolebinding dashboard-admin-sa --clusterrole=cluster-admin --serviceaccount=default:dashboard-admin-sa
	@echo "Installing dashboard"
	kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml

setup_nginx:
	@echo "Setting up nginx..."
	kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.11.1/deploy/static/provider/cloud/deploy.yaml 

setup_cert_manager:
	@echo "Setting up cert manager..."
	kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.11.1/cert-manager.yaml

push_new_docker:
	@echo "\nPushing new docker image to the cloud"
	docker build -t $(image_name):$(image_version) $(image_path)
	docker image tag $(image_name):$(image_version) $(ACR).azurecr.io/$(image_name):$(image_version)
	az acr login --name $(ACR)
	CALL docker push $(ACR).azurecr.io/$(image_name):$(image_version)

apply_kubeconfigs: 
	@echo "Creating secrets"
	kubectl create secret generic envs --from-env-file=$(envs_path)

	@echo "Applying deployment"
	kubectl apply -f deployment.yaml

	@echo "Applying networking"
	kubectl apply -f ingress.yaml

	@echo "Applying TLS"
	kubectl apply -f tls.yaml

load_dashboard:
	kubectl create token dashboard-admin-sa > .\bearer-token.txt
	@echo "http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/"
	kubectl proxy

setup: fetch_terraform_output connect_to_cluster setup_dashboard setup_nginx setup_cert_manager
upload: fetch_terraform_output connect_to_cluster push_new_docker apply_kubeconfigs