CREATE DATABASE IF NOT EXISTS Bentley_Bot;
CREATE USER IF NOT EXISTS 'bentley_user'@'%' IDENTIFIED BY 'Domingo313';
GRANT ALL PRIVILEGES ON Bentley_Bot.* TO 'bentley_user'@'%';