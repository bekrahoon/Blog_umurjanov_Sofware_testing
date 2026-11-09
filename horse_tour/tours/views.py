"""
Представления (views) стартапа «Конный тур».

Каждая форма создания отправляет данные методом POST; при успехе
выполняется редирект на список туров, при ошибке форма показывается снова
с сообщениями об ошибках (статус 200).
"""
from django.shortcuts import get_object_or_404, redirect, render

from . import forms, models


def _create_view(request, form_class, title):
    """Общая логика для всех форм создания."""
    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            form.save()
            return redirect('tour_list')
    else:
        form = form_class()
    return render(request, 'tours/form.html', {'form': form, 'title': title})


def tour_list_view(request):
    """
    Список всех туров :model:`tours.Tour` с их категориями.

    **Шаблон:** :template:`tours/tour_list.html`
    """
    tours = models.Tour.objects.prefetch_related('categories').all()
    return render(request, 'tours/tour_list.html', {'tours': tours})


def tour_detail_view(request, id):
    """
    Страница одного тура: маршрут (1 к 1), покупки и комментарии (1 ко многим),
    категории (многие ко многим). Если тура нет — 404.

    **Шаблон:** :template:`tours/tour_detail.html`
    """
    tour = get_object_or_404(models.Tour, id=id)
    return render(request, 'tours/tour_detail.html', {'tour': tour})


def create_category_view(request):
    """Создание :model:`tours.Category` (POST)."""
    return _create_view(request, forms.CategoryForm, 'Новая категория')


def create_tour_view(request):
    """Создание :model:`tours.Tour` с выбором категорий (POST)."""
    return _create_view(request, forms.TourForm, 'Новый тур')


def create_route_view(request):
    """Создание :model:`tours.TourRoute` — маршрута тура, связь 1 к 1 (POST)."""
    return _create_view(request, forms.TourRouteForm, 'Новый маршрут')


def create_customer_view(request):
    """Регистрация :model:`tours.Customer` (POST)."""
    return _create_view(request, forms.CustomerForm, 'Новый клиент')


def create_booking_view(request):
    """
    Покупка тура :model:`tours.Booking` (POST).

    Нельзя купить второй тур на тот же день и время одному человеку.
    """
    return _create_view(request, forms.BookingForm, 'Купить тур')


def create_comment_view(request):
    """
    Комментарий :model:`tours.Comment` (POST).

    Разрешён только к турам, в которых клиент был.
    """
    return _create_view(request, forms.CommentForm, 'Оставить комментарий')
