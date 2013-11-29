from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'cbeh.views.home', name='home'),
    # url(r'^cbeh/', include('cbeh.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^djangoadmin/doc/', include('django.contrib.admindocs.urls')),

    url(r'^cbeh/pos/', include('pos.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^djangoadmin/', include(admin.site.urls)),
)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += staticfiles_urlpatterns()
