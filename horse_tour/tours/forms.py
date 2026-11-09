from django import forms

from . import models


class CategoryForm(forms.ModelForm):
    class Meta:
        model = models.Category
        fields = '__all__'


class TourForm(forms.ModelForm):
    class Meta:
        model = models.Tour
        fields = ['title', 'description', 'price', 'duration_hours', 'categories']
        widgets = {'categories': forms.CheckboxSelectMultiple}


class TourRouteForm(forms.ModelForm):
    class Meta:
        model = models.TourRoute
        fields = '__all__'


class CustomerForm(forms.ModelForm):
    class Meta:
        model = models.Customer
        fields = '__all__'


class BookingForm(forms.ModelForm):
    class Meta:
        model = models.Booking
        fields = ['customer', 'tour', 'date', 'time']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = models.Comment
        fields = ['customer', 'tour', 'text', 'mark']
