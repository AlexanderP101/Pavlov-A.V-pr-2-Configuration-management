# Вариант 18: граф зависимостей Alpine APK

Python 3.11+, только стандартная библиотека. Запуск первого этапа:

```sh
./run.sh examples/acyclic.toml
```

Пять обязательных полей TOML: `package`, `repository`, `test_mode`,
`version`, `max_depth`. Относительный путь репозитория считается от TOML.
Ошибки конфигурации выводятся в stderr, код завершения — 2.
