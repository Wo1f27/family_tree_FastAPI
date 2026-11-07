# Family Tree - Сборка и установка

## Структура после установки

```
C:\Program Files\FamilyTree\
├── family_tree.exe          ← Desktop приложение
├── family_tree_web.exe      ← Web сервер (FastAPI)
├── Открыть веб-интерфейс.lnk ← Ярлык (открывает браузер)
├── data\
│   └── genealogy.db         ← Общая БД
└── ...
```

## Как работает общая БД

Оба приложения (desktop и web) используют **одну и ту же БД**:

### В режиме разработки
- Путь: `data/genealogy.db` (в корне проекта)
- Оба приложения используют один файл

### В режиме PyInstaller (frozen)
- Путь: `~/.local/share/FamilyTree/data/genealogy.db` (Linux/Mac)
- Путь: `%LOCALAPPDATA%\FamilyTree\data\genealogy.db` (Windows)
- Оба приложения используют один файл

## Сборка

### Локальная сборка (Windows)
1. Установите Python 3.13
2. Установите зависимости: `pip install -r requirements.txt`
3. Установите PyInstaller: `pip install pyinstaller`
4. Соберите desktop: `pyinstaller desktop.spec`
5. Соберите web: `pyinstaller web.spec`
6. Установите Inno Setup
7. Соберите установочник: `iscc installer/setup.iss`

### GitHub Actions
1. Создайте тег: `git tag v1.0.0 && git push origin v1.0.0`
2. GitHub Actions автоматически соберёт установочники
3. Загрузите артефакты из действий

## Запуск веб-сервера

### Вручную
```bash
cd C:\Program Files\FamilyTree
.\family_tree_web.exe
```

### Через ярлык
- Двойной клик на "Открыть веб-интерфейс" на рабочем столе
- Браузер откроется автоматически на `http://127.0.0.1:8000/`

## Проверка общей БД

1. Запустите desktop приложение
2. Добавьте персону
3. Запустите web сервер
4. Откройте `http://127.0.0.1:8000/api/v1/persons/`
5. Вы увидите добавленную персону
