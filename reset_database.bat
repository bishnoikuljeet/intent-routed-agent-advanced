@echo off
echo Resetting Database Containers
echo.

echo Stopping database containers...
docker stop analytics_db logs_db 2>nul

echo Removing database containers...
docker rm analytics_db logs_db 2>nul

echo.
echo Starting database containers with updated data...
docker run -d --name analytics_db -p 3306:3306 -e MYSQL_ROOT_PASSWORD=analytics_root_password -e MYSQL_DATABASE=sales -v "%cd%\databases\init-scripts\mysql-sales:/docker-entrypoint-initdb.d" mysql:8.0

docker run -d --name logs_db -p 3307:3306 -e MYSQL_ROOT_PASSWORD=logs_root_password -e MYSQL_DATABASE=inventory -v "%cd%\databases\init-scripts\mysql-inventory:/docker-entrypoint-initdb.d" mysql:8.0

echo.
echo Waiting for databases to initialize...
timeout /t 30 /nobreak >nul

echo.
echo Database reset complete!
echo.
echo Database Status:
echo - Sales Database: localhost:3306 (analytics_db container)
echo - Inventory Database: localhost:3307 (logs_db container)
echo.
echo The new Arduino Starter Kit (SKU-011) has been added with low stock (8 units, reorder point: 25)
echo.
echo You can now test: "Which products are low on stock?"
echo.
pause
