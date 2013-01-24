from django.conf.urls.defaults import patterns, include, url
from django.conf import settings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'entities.views.home', name='home'),
    url(r'^search/','entities.views.search'),
    url(r'^companies/','entities.views.companies'),
    url(r'^filters/','entities.views.filters'),
    url(r'^pathfilters/','entities.views.path_filters'),
    url(r'^paths/','entities.views.paths'),
    url(r'^path/(\d+)/$','entities.views.path'),
    url(r'^careers/','entities.views.careers'),
    url(r'^login/','accounts.views.login'),
    url(r'^account/authorize','accounts.views.linkedin_authorize'),
    url(r'^account/authenticate','accounts.views.linkedin_authenticate'),
    url(r'^account/finish','accounts.views.finish_login'),
    url(r'^account/link','accounts.views.finish_link'),
    url(r'^account/success','accounts.views.success'),
    url(r'^account/logout','accounts.views.logout'),
    url(r'^account/login','accounts.views.login'),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    # url(r'^prosperime/', include('prosperime.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)

if not settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
    )
else:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
    )