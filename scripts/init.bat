@ECHO OFF
SETLOCAL

:: Load variables
CALL .\scripts\vars.bat

:: Login to Azure
ECHO Logging into Azure for tenant: 7a5561df-6599-4898-8a20-cce41db3b44f
CALL az account clear
CALL az login --tenant 7a5561df-6599-4898-8a20-cce41db3b44f
CALL az account set --subscription 32b0d332-7725-4b80-aec9-c7ec16ed0da5
IF ERRORLEVEL 1 (
  ECHO Failed to login to Azure.
  EXIT /B 1
)

:: Resource group
ECHO Creating resource group %RESOURCE_GROUP%...
CALL az group create --name %RESOURCE_GROUP% --location %LOCATION%
IF ERRORLEVEL 1 (
  ECHO Failed to create resource group '%RESOURCE_GROUP%' at '%LOCATION%'.
  EXIT /B 1
)

:: Sleep for 10 seconds
CALL timeout /t 10

:: Storage Account
ECHO Creating storage account %STORAGE_ACCOUNT%...
@REM ECHO az storage account create --name %STORAGE_ACCOUNT% --resource-group %RESOURCE_GROUP% --location %LOCATION%
CALL az storage account create --name %STORAGE_ACCOUNT% --resource-group %RESOURCE_GROUP% --location %LOCATION%
IF ERRORLEVEL 1 (
  ECHO Failed to create storage account.
  EXIT /B 1
)

:: Create container registry
ECHO Creating container registry %name%
CALL az acr create --resource-group %RESOURCE_GROUP% --name %name% --sku Basic --location %LOCATION% --admin-enabled true
IF ERRORLEVEL 1 (
  ECHO Failed to create container registry.
  EXIT /B 1
)

:: Sleep for 10 seconds
CALL timeout /t 10

:: Create kubernetes cluster
ECHO Creating kubernetes cluster
CALL az aks create -g %RESOURCE_GROUP% -n %name% --location %LOCATION% --attach-acr %name% --kubernetes-version 1.30 --ip-families IPv4,IPv6 --os-sku Ubuntu --tier Standard --node-count 1 --node-vm-size Standard_A2_v2
IF ERRORLEVEL 1 (
  ECHO Failed to give access of container registry to identity.
  EXIT /B 1
)

ECHO Initialization completed successfully.
ENDLOCAL
EXIT /B 0