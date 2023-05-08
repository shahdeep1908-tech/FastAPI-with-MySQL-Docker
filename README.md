# FastAPI-with-MySQL-Docker

## Create a Docker container with MySQL  
```
docker pull mysql:latest
docker run --name mysql -e MYSQL_ROOT_PASSWORD=<your_password> -p 3306:3306 -d mysql:latest
docker ps
docker exec -it mysql mysql -p
```

## Create Database and Table to connect to Code
```
USE mydatabase;
CREATE TABLE leads (
    id INT AUTO_INCREMENT PRIMARY KEY,
    phone_work VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
);
select * from leads;
```

## How to run this project
```
pip install -r requirements.txt
python main.py
```

## How to get Bitcoin chart (API Endpoint)
```
http://0.0.0.0:8080/bitcoin_price?days=30&interval=monthly
```