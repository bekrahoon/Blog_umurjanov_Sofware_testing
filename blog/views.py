from django.db.models import F
from django.shortcuts import render, get_object_or_404
from . import models

def blog_list_view(request):
    if request.method == 'GET':
        blog = models.Blog.objects.all().order_by('-id')
    return render(request, template_name='blog_list.html', context={'blog': blog})


def blog_detail_view(request, id):
    if request.method == "GET":
        blog_id = get_object_or_404(models.Blog, id=id)
        # +1 к лайкам при каждом заходе на детальную страницу
        models.Blog.objects.filter(id=blog_id.id).update(likes=F('likes') + 1)
        blog_id.refresh_from_db()
    return render(request, template_name='blog_detail.html', context={'blog_id': blog_id})
