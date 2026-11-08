# API v0.1

## Регистрация
`POST /auth/register`
```json
{"email":"user@example.com","password":"at-least-12-characters"}
```

## Вход
`POST /auth/token` — OAuth2 form: username=email, password=password.

## Сигнал
`POST /reports` с Bearer token:
```json
{
  "profile_url":"https://www.facebook.com/example",
  "profile_name":"Example",
  "reason_category":"coordinated_activity",
  "description":"Описание с конкретен контекст и проверими факти.",
  "evidence_urls":["https://example.org/investigation"]
}
```

## Публични маркировки
`GET /profiles/flagged`

## История на профил
`GET /profiles/{profile_id}/history`

## Модерация
`GET /admin/reports` и `POST /admin/reports/{report_id}/decision` — само reviewer/admin.
