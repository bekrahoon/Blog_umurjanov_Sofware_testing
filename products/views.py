from django.shortcuts import render, redirect, get_object_or_404
from .models import Product
from .forms import ProductForm


# READ — список
def product_list_view(request):
    products = Product.objects.all().order_by('-id')
    return render(request, 'products/product_list.html', {'products': products})


# READ — один объект
def product_detail_view(request, id):
    product = get_object_or_404(Product, id=id)
    return render(request, 'products/product_detail.html', {'product': product})


# CREATE
def product_create_view(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            return redirect('product_detail', id=product.id)
    else:
        form = ProductForm()
    return render(request, 'products/product_form.html', {'form': form, 'title': 'Новый товар'})


# UPDATE
def product_update_view(request, id):
    product = get_object_or_404(Product, id=id)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_detail', id=product.id)
    else:
        form = ProductForm(instance=product)
    return render(request, 'products/product_form.html', {'form': form, 'title': 'Редактировать товар'})


# DELETE (GET — страница подтверждения, POST — удаление)
def product_delete_view(request, id):
    product = get_object_or_404(Product, id=id)
    if request.method == 'POST':
        product.delete()
        return redirect('product_list')
    return render(request, 'products/product_confirm_delete.html', {'product': product})
