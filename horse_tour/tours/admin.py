from django.contrib import admin

from . import models


class TourRouteInline(admin.StackedInline):
    model = models.TourRoute


@admin.register(models.Tour)
class TourAdmin(admin.ModelAdmin):
    list_display = ['title', 'price', 'duration_hours']
    filter_horizontal = ['categories']
    inlines = [TourRouteInline]


@admin.register(models.Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['customer', 'tour', 'date', 'time']
    list_filter = ['date', 'tour']


@admin.register(models.Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['customer', 'tour', 'mark', 'created_at']


admin.site.register(models.Category)
admin.site.register(models.TourRoute)
admin.site.register(models.Customer)
