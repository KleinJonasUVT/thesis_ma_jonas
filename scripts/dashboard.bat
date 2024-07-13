@ECHO OFF
SETLOCAL

:: Get the Token
ECHO Retrieving Token for Service Account
CALL kubectl create token dashboard-admin-sa > .\deployment\bearer-token.txt

ECHO Access the Kubernetes Dashboard at:
ECHO http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/

:: Start Kubernetes Proxy
ECHO Starting Kubernetes Proxy
CALL kubectl proxy
IF ERRORLEVEL 1 (
  ECHO Failed to start Kubernetes Proxy.
  EXIT /B 1
)

ENDLOCAL
EXIT /B 0