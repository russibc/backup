rm -rf ~/.m2/repository/br/ufsc/epibuilder-core

cd ~/github/EpiBuilder/src/core
mvn clean install -DskipTests

cd ~/github/EpiBuilder/src/web/backend
mvn clean package -DskipTests

