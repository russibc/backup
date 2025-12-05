sudo systemctl stop postgresql
docker stop epibuilder-postgres
docker rm epibuilder-postgres

docker run -d --name epibuilder-postgres -e POSTGRES_USER=epiuser -e POSTGRES_PASSWORD=epiuser -e POSTGRES_DB=epibuilder -p 5432:5432 -v epibuilder-data:/var/lib/postgresql/data postgres:15.14-alpine3.21
