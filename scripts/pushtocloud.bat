@ECHO OFF
SETLOCAL

:: Load variables
CALL .\scripts\vars.bat

SET IMAGE=tai-coursecatalogue
SET VERSION=0.0.1
SET CERT_FILE_PATH=/app/cert.pem

@REM :: Build and push image to the cloud 
@REM ECHO Building docker image and pushing to the cloud
@REM CALL docker build -t %IMAGE%:%VERSION% .
@REM CALL docker image tag %IMAGE%:%VERSION% coursecatalogue.azurecr.io/%IMAGE%:%VERSION%
@REM CALL az acr login --name %name%
@REM CALL docker push coursecatalogue.azurecr.io/%IMAGE%:%VERSION%
@REM IF ERRORLEVEL 1 (
@REM   ECHO Failed to push docker image to the cloud.
@REM   EXIT /B 1
@REM )

:: Connect to correct kubernetes cluster
ECHO Connecting to kubernetes cluster %name%
CALL az aks get-credentials --resource-group %RESOURCE_GROUP% --name %name%

:: Create and apply config map with environment variables
ECHO Creating and applying config map
CALL kubectl create configmap envs --from-env-file=secrets\prod.env --dry-run=client -o yaml > deployment\envs.yaml
CALL kubectl apply -f deployment\envs.yaml
IF ERRORLEVEL 1 (
  ECHO Failed to apply config map.
  EXIT /B 1
)

:: Push pod to cluster or apply changed to pod if exists
ECHO Configuring kubernetes
CALL kubectl apply -f .\deployment\pod.yaml
IF ERRORLEVEL 1 (
  ECHO Failed to push pod.
  EXIT /B 1
)

:: Deploy Kubernetes Dashboard
ECHO Deploying Kubernetes Dashboard
CALL kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml
IF ERRORLEVEL 1 (
  ECHO Failed to deploy Kubernetes Dashboard.
  EXIT /B 1
)

:: Create Service Account and Cluster Role Binding for dashboard
ECHO Creating Service Account and Cluster Role Binding
CALL kubectl create serviceaccount dashboard-admin-sa
CALL kubectl create clusterrolebinding dashboard-admin-sa --clusterrole=cluster-admin --serviceaccount=default:dashboard-admin-sa
IF ERRORLEVEL 1 (
  ECHO Failed to create Service Account and Cluster Role Binding.
  EXIT /B 1
)

ECHO Initialization completed successfully.
ENDLOCAL
EXIT /B 0