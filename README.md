# InternshipAnswerSber
## Запуск

```bash
docker compose up
```

Приложение будет доступно по адресу: `http://localhost:8000`

## Использование

Параметры передаются через URL, например:
```
http://localhost:8000/?hostname=PC1
```

## Запуск тестов

```bash
docker-compose exec fastapi-app pytest app/test.py -v
```
