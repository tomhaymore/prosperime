from django.conf.urls.defaults import patterns, include, url
from django.conf import settings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'entities.views.home', name='home'),
    url(r'^home/$', 'entities.views.home'),
    url(r'^welcome/$','entities.views.welcome'),
    url(r'^discover/$','entities.views.discover'),
    url(r'^discover/career/(\d+)/$','entities.views.discover_career'),
    url(r'^search/','entities.views.search'),
    url(r'^companies/','entities.views.companies'),
    url(r'^filters/','entities.views.filters'),
    url(r'^pathfilters/','entities.views.path_filters'),
    url(r'^careerfilters/','entities.views.career_filters'),
    url(r'^paths/','entities.views.paths'),
    url(r'^path/(\d+)/$','entities.views.path'),
    url(r'^careers/','entities.views.careers'),
    url(r'^login/','accounts.views.login'),
    url(r'^profile/(\d+)/$', 'entities.views.profile'),
    url(r'^profile/org/(/d+)/$','entities.views.org_profile'),
    url(r'^account/authorize','accounts.views.linkedin_authorize'),
    url(r'^account/authenticate','accounts.views.linkedin_authenticate'),
    url(r'^account/finish','accounts.views.finish_login'),
    url(r'^account/link','accounts.views.finish_link'),
    url(r'^account/success','accounts.views.success'),
    url(r'^account/logout','accounts.views.logout'),
    url(r'^account/login','accounts.views.login'),
    url(r'^tasks/', include('djcelery.urls')),
    url(r'^saved_paths/$','saved_paths.views.show_paths'),
    url(r'^saved_paths/save/$', 'saved_paths.views.save'),
    url(r'^saved/$','saved_paths.views.get_paths'),
    url(r'^saved_paths/rearrange/$', 'saved_paths.views.rearrange'),
    url(r'^saved_paths/create/$', 'saved_paths.views.create'),
    url(r'^saved_paths/remove/$', 'saved_paths.views.remove'),
    url(r'^saved_paths/(.+)', 'saved_paths.views.all_paths'),
    url(r'^contact/$', 'entities.views.contact'),
    url(r'^prototype/$', 'saved_paths.views.prototype'),
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