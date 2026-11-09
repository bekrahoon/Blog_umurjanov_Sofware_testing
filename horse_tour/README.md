# Horse Tour — стартап «Конный тур» (Django)

Практика по отношениям в БД + тестирование.

## Модели и связи

| Связь | Модели |
|---|---|
| **1 к 1** | `Tour` ↔ `TourRoute` (у тура один маршрут) |
| **1 ко многим** | `Customer` → `Booking`, `Tour` → `Booking`, `Customer` → `Comment`, `Tour` → `Comment` |
| **Многие ко многим** | `Tour` ↔ `Category` («конный», «пеший», «мото») |

## Бизнес-правила (и тесты на них)

1. **1 человек может купить только 1 тур на определённый день и время** — `UniqueConstraint(customer, date, time)` в `Booking`.
2. **1 человек может оставить несколько комментариев к турам, в которых был** — `Comment.clean()` проверяет, что есть покупка этого тура с датой не позже сегодняшней.
3. **У тура есть категории** — `Tour.categories` (ManyToMany с `Category`).

## Тесты

`tours/tests.py` — 46 тестов:
- связи 1:1, 1:N, M:N (создание, запрет второго маршрута, каскадное удаление);
- правило «один тур на день и время»;
- правило «комментарии только к посещённым турам»;
- категории;
- **отправка данных через все формы (POST)** — валидные и невалидные данные;
- страницы списка/детали, 404;
- документация admindocs.

После прогона автоматически создаётся отчёт `Test_Report.docx`.

```bash
pip install -r requirements.txt
python manage.py test tours
```

## Документация (Django admindocs)

Подключён `django.contrib.admindocs`, документация берётся из docstring'ов моделей и views.

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Открыть: http://127.0.0.1:8000/admin/doc/ (модели: `/admin/doc/models/`, views: `/admin/doc/views/`).

## Страницы

- `/` — список туров
- `/tours/<id>/` — тур (маршрут, покупки, комментарии)
- `/categories/create/`, `/tours/create/`, `/routes/create/`, `/customers/create/`, `/bookings/create/`, `/comments/create/` — формы
