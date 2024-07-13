SET IMAGE=tai-coursecatalogue
SET VERSION=0.0.1
SET CERT_FILE_PATH=/app/cert.pem

CALL docker build -t %IMAGE%:%VERSION% .
CALL CALL docker run -d -p 80:80 --env-file secrets\prod.env %IMAGE%:%VERSION%