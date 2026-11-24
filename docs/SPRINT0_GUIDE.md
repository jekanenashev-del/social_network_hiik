# Павлов — Sprint 0: пошаговый гайд

1. Получи свежий код и создай ветку:
```bash
git checkout develop
git pull
git checkout -b feature/pavlov-sprint0-foundation
```
2. Перед копированием сравни файлы с репозиторием. В стартовом скелете `main.py` уже содержит главную страницу, `/health/deep`, шаблоны и логирование — не затирай их упрощённой версией из пакета, перенеси нужные части вручную.
3. Убедись, что `pydantic-settings` есть в `requirements.txt`; если нет — добавь. Настоящий `.env` не коммить.
4. Перенеси/сверь `config.py`, `db/base.py`, `db/session.py`, `main.py`. `settings` — общие настройки; `get_db()` открывает и закрывает сессию; `Base` — родитель ORM-моделей.
5. В `dependencies.py` оставь заглушку `get_current_user`: JWT-реализацию делает Сивачев в Sprint 1.
6. `UserRead`, `PostRead`, `NotificationRead` взяты из полного плана. Поля `PostCreate`, `ReactionCreate`, `FriendshipRead` там не определены — черновики из пакета согласуй с владельцами модулей до merge.
7. Добавь `docs/ARCHITECTURE.md`, `docs/MODULE_TEMPLATE.md`. Владельцы модулей заполняют `docs/modules/<N>.md`; ты проверяешь полноту карточек.
8. Проверки из корня проекта:
```bash
python -c "from app.core.config import settings; print(settings.app_env)"
python -c "from app.db.session import engine, get_db; print(engine)"
python -c "from app.main import app; print(app.title)"
```
Затем, когда готовы модели и Docker: `docker compose up --build`; проверь `/health` и `/docs`. Не заявляй, что тесты прошли, если их не запускал.
9. PR:
```bash
git add app docs
git commit -m "Add Sprint 0 application foundation and architecture docs"
git push -u origin feature/pavlov-sprint0-foundation
```
Открой PR в `develop`, укажи проверки и ограничения.
10. На ревью проверяй: слои; R/W-границы модулей; контракты; N+1; минимум 2 теста; отсутствие секретов; logging вместо `print()`.
11. Для интеграции обнови `develop`, запусти `docker compose up --build`, проверь запуск, `/health` и smoke-тесты. Запиши проблемы и решения в `docs/INTEGRATION_LOG.md`. Не чини весь чужой модуль вместо владельца.

## Что требует команды
- Назначить Scrum Master и интегратора на ротацию (список людей/решение в документах не указаны).
- Карточки модулей заполняют их владельцы.
- Три схемы с неуказанными в плане полями остаются черновиками до согласования.
- Docker/CI/тесты нельзя считать проверенными без запуска в настоящем репозитории.
