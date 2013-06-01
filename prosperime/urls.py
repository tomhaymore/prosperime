from django.conf.urls.defaults import patterns, include, url
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'careers.views.home', name='home'),
    url(r'^home/$', 'careers.views.home'),
    url(r'^welcome/$','entities.views.welcome'),

    # Accounts Views
    url(r'^privacy/$','accounts.views.privacy'),
    url(r'^terms/$','accounts.views.terms'),
    url(r'^copyright/$','accounts.views.copyright'),
    url(r'^use/$','accounts.views.use'),

    # Entities Views
    url(r'^contact/$', 'entities.views.contact'),
    url(r'^about/$', 'entities.views.about'),
    url(r'^meet/$', 'entities.views.meet'),

    # Careers Views
    url(r'^path/(\d+)/$', 'careers.views.viewPath'),
    url(r'^feed/$', 'careers.views.feed'),
    url(r'^build/$', 'careers.views.build'),
    url(r'^schools/$', 'careers.views.schools'),

    url(r'^progress/$', 'careers.views.progress'), # Am I on Track?
    
    url(r'^buildv2/$','careers.views.build_v2'),
    url(r'^build/(\d+)/$', 'careers.views.modify_saved_path'),

    url(r'^plan/$', 'careers.views.plan'),
    url(r'^plan/(\d+)/$', 'careers.views.plan'),

    # url(r'^personalize/$','careers.views.personalize_careers_jobs'),
    url(r'^personalize/careers/$','careers.views.personalize_careers'),
    url(r'^personalize/jobs/$','careers.views.personalize_jobs'),
    url(r'^add_personalization/$','careers.views.add_personalization'),
    url(r'^careers/jobs/$','careers.views.list_jobs'),
    url(r'^career/(\d+)/$','careers.views.career_profile'),
    url(r'^position/(\d+)/$','careers.views.position_profile'),
    url(r'^position_paths/(\d+)/$','careers.views.position_paths'),
    url(r'^position_paths_filters/(\d+)/$','careers.views.position_paths_filters'),
    url(r'^discover/$','careers.views.discover'),
    url(r'^discover/career/(\d+)/$','careers.views.discover_career'),
    url(r'^discover/career/(\d+)/orgs/$', 'careers.views.discover_career_orgs'),
    url(r'^discover/career/(\d+)/positions/$', 'careers.views.discover_career_positions'),
    # url(r'^discover/position/(\d+)/$','careers.views.discover_position'),
    url(r'^search/','entities.views.search'),
    url(r'^companies/','entities.views.companies'),
    url(r'^filters/','entities.views.filters'),
    url(r'^pathfilters/','entities.views.path_filters'),
    url(r'^careerfilters/','entities.views.career_filters'),
    url(r'^paths/','entities.views.paths'),
    url(r'^path/(\d+)/$','entities.views.path'),
    url(r'^careers/$','entities.views.careers'),

    ## Careers - AJAX calls
    url(r'^careers/addDecision/$', 'careers.views.addDecision'),
    url(r'^careers/addIndustry/$', 'careers.views.addIndustry'),
    url(r'^careers/addSavedCareer/$', 'careers.views.addSavedCareer'),
    url(r'^careers/addGoalPosition/$', 'careers.views.addGoalPosition'),
    url(r'^careers/entityAutocomplete/$', 'careers.views.entityAutocomplete'),
    url(r'^careers/decisions/$', 'careers.views.viewCareerDecisions'),
    url(r'^careers/careerAutocomplete/$', 'careers.views.careerAutocomplete'),
    url(r'^careers/idealPositionAutocomplete/$', 'careers.views.idealPositionAutocomplete'),
    url(r'^careers/industryAutocomplete/$', 'careers.views.industryAutocomplete'),
    url(r'^careers/positionAutocomplete/$', 'careers.views.positionAutocomplete'),
    url(r'^careers/getSavedCareers/$', 'careers.views.getSavedCareers'),
    url(r'^careers/getGoalPositions/$', 'careers.views.getGoalPositions'),
    url(r'^careers/getNextBuildStep/$', 'careers.views.get_next_build_step'),
    url(r'^careers/getNextBuildStepIdeal/$', 'careers.views.get_next_build_step_ideal'),
    url(r'^careers/saveBuildPath/$', 'careers.views.save_build_path'),
    url(r'^careers/deleteSavedPath/$', 'careers.views.delete_path'),
    url(r'^careers/getIdealPosPath/$', 'careers.views.get_ideal_pos_paths'),
    url(r'^careers/getIdealPaths/$', 'careers.views.get_ideal_paths'),
    url(r'^careers/getIdealMatches/$', 'careers.views.get_ideal_match_users'),
    url(r'^api/list_careers/$', 'careers.views.list_careers'),
    url(r'^careers/getProgress/$', 'careers.views.get_progress'),
    url(r'^careers/addProgressDetails/$', 'careers.views.add_progress_detail'),

    ## Accounts - AJAX calls
    url(r'^accounts/updateProfile/$', 'accounts.views.updateProfile'),
    url(r'^accounts/deleteItem/$', 'accounts.views.deleteItem'),
    url(r'^accounts/connect/$', 'accounts.views.connect'),

    ## Social
    url(r'^social/saveComment/$', 'social.views.saveComment'),

    url(r'^decisions/', 'careers.views.getDecisions'),
    url(r'^login/','accounts.views.login'),
    url(r'^account/register','accounts.views.register'),
    url(r'^profile/(\d+)/$', 'accounts.views.profile'),
    url(r'^profile/org/(\d+)/$','entities.views.profile_org'),
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
    url(r'^rand/$', 'accounts.views.random_profile'),
    url(r'^home2/$', 'careers.views.home_proto'),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    # url(r'^prosperime/', include('prosperime.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)

if not settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
    )
else:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
    )
