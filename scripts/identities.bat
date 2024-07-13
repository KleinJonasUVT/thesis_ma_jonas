@REM :: Create identity
@REM ECHO Creating identity
@REM CALL az identity create --name %name% --resource-group %RESOURCE_GROUP%
@REM IF ERRORLEVEL 1 (
@REM   ECHO Failed to create identity.
@REM   EXIT /B 1
@REM )

@REM SET keyvaultname=%name%-2

@REM :: Create key-vault
@REM ECHO Creating key vault
@REM CALL az keyvault create --name %keyvaultname% --resource-group %RESOURCE_GROUP% --enable-rbac-authorization false --enable-purge-protection
@REM IF ERRORLEVEL 1 (
@REM   ECHO Failed to create key vault.
@REM   EXIT /B 1
@REM )

@REM :: Capture identity id
@REM FOR /F "tokens=*" %%i IN ('az identity show --resource-group %RESOURCE_GROUP% --name %name% --query id --output tsv') DO SET identityId=%%i

@REM :: Capture identity principal id
@REM FOR /F "tokens=*" %%i IN ('az identity show --resource-group %RESOURCE_GROUP% --name %name% --query principalId --output tsv') DO SET identityPrincipalId=%%i

@REM :: Capture keyvault id
@REM FOR /F "tokens=*" %%i IN ('az keyvault show --resource-group %RESOURCE_GROUP% --name %keyvaultname% --query id --output tsv') DO SET keyvaultId=%%i

@REM :: Give identity access to key vault
@REM ECHO Giving identity %identityId% access to keyvault
@REM CALL az keyvault set-policy --resource-group %RESOURCE_GROUP% --name %keyvaultname% --object-id %identityPrincipalId% --key-permissions get unwrapKey wrapKey
@REM IF ERRORLEVEL 1 (
@REM   ECHO Failed to give identity access to keyvault.
@REM   EXIT /B 1
@REM )

@REM :: Create key
@REM ECHO Creating the keys
@REM CALL az keyvault key create --name %name% --vault-name %keyvaultname%
@REM IF ERRORLEVEL 1 (
@REM   ECHO Failed to create a key.
@REM   EXIT /B 1
@REM )

@REM FOR /F "tokens=*" %%i IN ('az keyvault key show --name %name% --vault-name %keyvaultname% --query key.kid --output tsv') DO SET keyId=%%i

@REM :: Capture resource ID of container registry
@REM FOR /F "tokens=*" %%i IN ('az acr show --resource-group %RESOURCE_GROUP% --name %REGISTRY% --query id --output tsv') DO SET resourceId=%%i

@REM :: Give identiy access to the container registry
@REM ECHO Giving identity '%identityPrincipalId%' access to the container registry '%resourceId%'
@REM CALL az role assignment create --assignee %identityPrincipalId% --scope %resourceId% --role "AcrPull"
@REM IF ERRORLEVEL 1 (
@REM   ECHO Failed to give access of container registry to identity.
@REM   EXIT /B 1
@REM )