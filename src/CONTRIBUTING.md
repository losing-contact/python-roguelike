# Как мы работаем вдвоём

## Ветки

- `develop` - общая ветка, всегда запускается и проходит тесты. Напрямую не коммитим.
- Каждая задача - своя ветка от свежей `develop`, живёт 1-3 дня:

| Префикс | Для чего | Пример |
|---|---|---|
| `feat/` | новая возможность | `feat/ogre-enemy` |
| `fix/` | исправление бага | `fix/exit-blocked-by-enemy` |
| `refactor/` | перестройка без смены поведения | `refactor/split-renderer` |
| `test/` | только тесты | `test/combat-edge-cases` |
| `docs/` | документация | `docs/architecture` |
| `chore/` | настройки, мусор | `chore/ruff-config` |

```bash
git switch develop && git pull
git switch -c feat/ogre-enemy
```

## Коммиты

Формат `тип: что сделано`, до ~72 символов, повелительное наклонение. Один коммит - одна мысль.

```
feat: add ogre with rest turn and guaranteed counterattack
fix: stop enemies from stepping onto the exit tile
refactor: move item descriptions to presentation/messages
test: cover vampire first-hit miss
docs: describe how to add an enemy type
```

Почему так, объясняйте в теле коммита (после пустой строки). Не коммитим: `__pycache__`,
`.idea`, `.venv`, сохранения игры. Всё это уже в `.gitignore`.

## Merge request

1. Перед созданием: `git fetch && git rebase origin/develop`, затем `make test lint`.
2. Маленький MR (до ~300-400 строк). Больше - режьте на части.
3. Заполните шаблон (подставляется автоматически).
4. Второй человек делает ревью и нажимает Approve. **Свой MR не мерджим.**
5. Merge: `Squash` для веток с неряшливыми коммитами, обычный merge, если коммиты аккуратные.
   После merge ветка удаляется.
6. В `develop` не делаем `push --force`. В своей ветке можно `--force-with-lease`.

## Чек-лист ревьюера

- [ ] `domain` не импортирует `curses`/`json`; тесты `test_architecture.py` зелёные
- [ ] В домене нет текстов для игрока и нет глобального `random`
- [ ] На новое поведение есть тест
- [ ] Числа баланса лежат в `balance.py`
- [ ] Нет лишних файлов в диффе
- [ ] Автор может объяснить каждую строку (на P2P-проверке спросят про любую часть)

## Задачи

Одна задача = один Issue на доске (`To do` -> `In progress` -> `Review` -> `Done`), метки
`domain`, `presentation`, `datalayer`, `bonus`. Название ветки начинайте с номера Issue, если он есть.
Общие контракты (`Level`, команды, события, `SaveRepository`) меняем только после обсуждения.
