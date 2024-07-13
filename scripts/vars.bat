:: Define variables (in lowercase)
SET name=coursecatalogue
SET version=0.0.1

:: Path where cert.pem file in Docker is copied to
SET CERT_FILE_PATH=/app/cert.pem
SET PORT=80

:: Do not change variables
SET LOCATION=westeurope
SET REGISTRY=%name%
SET STORAGE_ACCOUNT=%name%tai
SET RESOURCE_GROUP=%name%