
Веб-приложение для публикации рецептов с элементами социальной сети. Пользователи могут делиться рецептами, добавлять их в избранное, подписываться на других авторов и составлять списки покупок.

## Быстрый старт

1. Клонируйте репозиторий

2. Создайте файл `.env` в директории `infra` на основе `.env.example`:
```bash
cp infra/.env.example infra/.env
```

3. Запустите проект:
```bash
cd infra
docker-compose up -d
```

4. Создайте суперпользователя:
```bash
docker-compose run backend python manage.py createsuperuser
```

## Данные

В файле `.env` параметр `LOAD_TEST_DATA=1` позволяет загрузить тестовые данные при запуске. (Сами тестовые данные находятся в backend/test_data.json)

Также вы можете зайти в админ панель и загрузить ингридиенты нажав на "Импорт" и выбрав по пути data/ingredients.csv

## Доступ к приложению

- Веб-интерфейс: [Localhost](http://localhost/)
- API документация: [Localhost docs](http://localhost/api/docs/)
- Админ-панель: [Localhost admin](http://localhost/admin/)
