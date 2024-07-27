# Configure the Azure provider
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 3.93.0"
    }
  }

  required_version = ">= 1.9.0"
}

provider "azurerm" {
  features {}
}

###############################################
#                 Variables                   #
###############################################
variable "location" {
  default = "westeurope"
  type    = string
}

###############################################
#              Infrastructure                 #
###############################################
# Create resource group
resource "azurerm_resource_group" "rg" {
  name     = "coursecatalogue2"
  location = var.location

  timeouts {
    create = "1m"
    delete = "30m"
  }
}

# Create a container registry
resource "azurerm_container_registry" "acr" {
  name                = "coursecatalogue2"
  resource_group_name = azurerm_resource_group.rg.name
  location            = var.location
  sku                 = "Basic"
  admin_enabled       = true

  timeouts {
    create = "3m"
    delete = "10m"
  }
}

# Create kubernetes cluster
resource "azurerm_kubernetes_cluster" "cluster" {
  name                = "coursecatalogue2"
  resource_group_name = azurerm_resource_group.rg.name
  location            = var.location
  kubernetes_version  = "1.30"
  sku_tier            = "Standard"

  dns_prefix = "default"

  default_node_pool {
    name       = "default"
    node_count = 1
    vm_size    = "Standard_A2_v2"
    os_sku     = "Ubuntu"
  }

  network_profile {
    network_plugin = "kubenet"
    ip_versions = ["IPv4", "IPv6"]
  }

  identity {
    type = "SystemAssigned"
  }

  timeouts {
    create = "5m"
    delete = "30m"
  }

}

# Attach container registry to cluster
resource "azurerm_role_assignment" "acr-cluster" {
  principal_id                     = azurerm_kubernetes_cluster.cluster.kubelet_identity[0].object_id
  role_definition_name             = "AcrPull"
  scope                            = azurerm_container_registry.acr.id
  skip_service_principal_aad_check = true

  timeouts {
    create = "3m"
    delete = "5m"
  }
}

###############################################
#                   Outputs                   #
###############################################
# Set Kube Config as output
output "kube_config" {
  value     = azurerm_kubernetes_cluster.cluster.kube_config_raw
  sensitive = true
}

output "resource_group_name" {
  value = azurerm_resource_group.rg.name
}

output "cluster_name" {
  value = azurerm_kubernetes_cluster.cluster.name
}

output "acr_name" {
  value = azurerm_container_registry.acr.name
}