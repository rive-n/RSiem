# Дипломная работа - SIEM.

## Что умеет?

1. Создавать подсистемы в реальном времени
2. Исполнять код в подсистемах в реальном времени
3. Собирать логи с существующих систем
4. Проксировать запросы согласно конфигурации
5. Рендерить темплейты в реальном времени

## Из чего состоит?

1. redis - Сбор информации с брокера RabbitMQ
2. RabbitMQ - Брокер, созданный для планировки и бэкграунд задач
3. fastapi rest - ядро системы
4. Grafana - собирает все необходимые логи с PostreSQL
5. PostreSQL - хранение логов

## Стек

- dramatiq - замена Celery. Работает как подпроцесс supervisord
- docker/python docker sdk - удобная библиотека для работы с docker socket HTTP API
- grafana client - подобие docker sdk, не очень удобная библиотека для работы с grafana HTTP API
- fastapi - асинхронный фреймворк для обработки запросов
- uvicorn - веб сервер для fastapi, ускоряем работу сервиса по максимуму

## Deploy

1. Необходимо создать .env файл для дальнейшего запуска в docker-compose, содержащий в себе значения:
    1. DEBUG - ключ, отвечающий за то, где будет запущена система: локально или в docker.
    2. ROOT_PATH - путь до корневой директории.
    3. GF_USERNAME - имя пользователя, указанного в docker-compose для входа в UI графаны
    4. GF_PASSWORD - паролья пользователя, указанного в docker-compose для входа в UI графаны
    5. PSQL_USERNAME - имя пользователя, указанного в docker-compose для создания datasource в графане
    6. PSQL_PASSWORD - пароль пользователя, указанного в docker-compose для создания datasource в графане
