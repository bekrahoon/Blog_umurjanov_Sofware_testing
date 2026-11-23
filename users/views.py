from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from users.forms import CaptchaLoginForm, CustomRegisterForm
from users.models import CustomUser


# регистрация
def register_view(request):
    if request.method == 'POST':
        form = CustomRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('/login/')
    else:
        form = CustomRegisterForm()
    return render(request, 'users/register.html', {'form': form})


# авторизация с капчей
def auth_login_view(request):
    if request.method == 'POST':
        form = CaptchaLoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('/profile/')
    else:
        form = CaptchaLoginForm(request)
    return render(request, 'users/login.html', {'form': form})


# выход
def auth_logout_view(request):
    logout(request)
    return redirect('/login/')


# личный кабинет
@login_required(login_url='/login/')
def profile_view(request):
    user = CustomUser.objects.get(id=request.user.id)
    return render(request, 'users/profile.html', {'user': user})
