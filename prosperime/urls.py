from django.conf.urls.defaults import patterns, include, url
from django.conf import settings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'careers.views.home', name='home'),
    url(r'^home/$', 'careers.views.home'),
    url(r'^welcome/$','entities.views.welcome'),
    url(r'^personalize/$','careers.views.personalize_careers_jobs'),
    url(r'^personalize/careers/$','careers.views.personalize_careers'),
    url(r'^personalize/jobs/$','careers.views.personalize_jobs'),
    url(r'^add_personalization/$','careers.views.add_personalization'),
    url(r'^careers/jobs/$','careers.views.list_jobs'),
    url(r'^career/(\d+)/$','careers.views.career_profile'),
    url(r'^discover/$','careers.views.discover'),
    url(r'^discover/career/(\d+)/$','careers.views.discover_career'),
    url(r'^discover/career/(\d+)/orgs/$', 'careers.views.discover_career_orgs'),
    url(r'^discover/career/(\d+)/positions/$', 'careers.views.discover_career_positions'),
    url(r'^discover/position/(\d+)/$','careers.views.discover_position'),
    url(r'^search/','entities.views.search'),
    url(r'^companies/','entities.views.companies'),
    url(r'^filters/','entities.views.filters'),
    url(r'^pathfilters/','entities.views.path_filters'),
    url(r'^careerfilters/','entities.views.career_filters'),
    url(r'^paths/','entities.views.paths'),
    url(r'^path/(\d+)/$','entities.views.path'),
    url(r'^careers/$','entities.views.careers'),
    url(r'^careers/addDecision/$', 'careers.views.addDecision'),
    url(r'^careers/entityAutocomplete/$', 'careers.views.entityAutocomplete'),
    url(r'^careers/decisions/$', 'careers.views.viewCareerDecisions'),
    url(r'^decisions/', 'careers.views.getDecisions'),
    url(r'^login/','accounts.views.login'),
    url(r'^profile/(\d+)/$', 'accounts.views.profile'),
    url(r'^profile/org/(\d+)/$','accounts.views.profile_org'),
    url(r'^account/authorize','accounts.views.linkedin_authorize'),
    url(r'^account/authenticate','accounts.views.linkedin_authenticate'),
    url(r'^account/finish','accounts.views.finish_login'),
    url(r'^account/link','accounts.views.finish_link'),
    url(r'^account/success','accounts.views.success'),
    url(r'^account/logout','accounts.views.logout'),
    url(r'^account/login','accounts.views.login'),
    url(r'^tasks/', include('djcelery.urls')),
    url(r'^saved_paths/$','careers.views.show_paths'),
    url(r'^saved_paths/save/$', 'careers.views.save'),
    url(r'^saved/$','careers.views.get_paths'),
    url(r'^saved_paths/queue/$', 'careers.views.get_queue'),
    url(r'^saved_paths/rearrange/$', 'careers.views.rearrange'),
    url(r'^saved_paths/create/$', 'careers.views.create'),
    url(r'^saved_paths/remove/$', 'careers.views.remove'),
    url(r'^saved_paths/add_to_queue/$','careers.views.add_to_queue'),
    url(r'^next/','careers.views.next'),
    url(r'^contact/$', 'entities.views.contact'),
    url(r'^prototype/$', 'careers.views.prototype'),
    url(r'^rand/$', 'accounts.views.random_profile'),
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
