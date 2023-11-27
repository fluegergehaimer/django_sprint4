from django.contrib import admin
from django.urls import include, path, reverse_lazy
from django.conf.urls.static import static
from django.views.generic.edit import CreateView
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings


urlpatterns = [
    path('pages/', include('pages.urls')),
    path('admin/', admin.site.urls),
    path('auth/', include('django.contrib.auth.urls')),
    path(
        'auth/registration/',
        CreateView.as_view(
            template_name='registration/registration_form.html',
            form_class=UserCreationForm,
            success_url=reverse_lazy('blog:index'),
        ), name='registration'
    ),
    path('', include('blog.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'pages.views.page_not_found'
handler403 = 'pages.views.csrf_failure'
handler500 = 'pages.views.internal_server_error'
