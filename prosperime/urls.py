from django.conf.urls.defaults import patterns, include, url
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'social.views.welcome'),
    # url(r'^$','careers.views.proto'),
    url(r'^home/$', 'social.views.home'),
    url(r'^welcome/$','social.views.welcome'),
    url(r'^unsubscribe/$','accounts.views.unsubscribe'),

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
    url(r'^majors/$', 'careers.views.majors_v4'),
    url(r'^majors_v3/$', 'careers.views.majors_v3'),
    url(r'^majors_v4/$', 'careers.views.majors_v4'),
    url(r'^majors_test/$', 'careers.views.test_majors_v3'),
    url(r'^majors/(\d+)/$','careers.views.major'),
    # url(r'^majors/v/(\d+)/$', 'careers.views.single_major'),

    # Recruiter Views
    url(r'^recruiters/$', 'social.views.recruiters'),
    url(r'^recruiters/thanks/$', 'social.views.recruiters_thanks'),

    url(r'^progress/$', 'careers.views.progress'), # Am I on Track?
    
    url(r'^buildv2/$','careers.views.build_v2'),
    url(r'^build/(\d+)/$', 'careers.views.modify_saved_path'),

    url(r'^plan/$', 'careers.views.plan'),
    url(r'^plan/(\d+)/$', 'careers.views.plan'),

    url(r'^internships/$', 'careers.views.internships'),
    url(r'^internships_v2/$', 'careers.views.internships_simple'),

    url(r'^chrome_api/$', 'careers.views.chrome_api'),

    url(r'^personalize/$','accounts.views.personalize'),

    # Social Views
    url(r'^thread/(\d+)/$', 'social.views.thread'),
    url(r'^thread/$', 'social.views.create_thread'),
    url(r'^question/(\d+)/$', 'social.views.question'),
    url(r'^ask/$', 'social.views.ask'),

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

    ## Entities - API

    url(r'^entities/suggest/(\w+)/$','entities.views.suggest'),

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
    url(r'^careers/testIdealPaths/$', 'careers.views.test_ideal_paths'),
    url(r'^careers/testBuildPaths/$', 'careers.views.test_build_paths'),
    url(r'^api/list_careers/$', 'careers.views.list_careers'),
    url(r'^careers/addProgressDetails/$', 'careers.views.add_progress_detail'),
    url(r'^careers/getSchoolFragment/(?:/(?P<school_id>\d+))?/$', 'careers.views.get_school_fragment'),
    url(r'^careers/getSchoolFragment/$', 'careers.views.get_school_fragment'),
    url(r'^careers/getFeedFragment/$', 'careers.views.get_feed_fragment'),
    url(r'^careers/getMajorsData/$', 'careers.views.get_majors_data'),
    url(r'^careers/getMajorsData/v3/$', 'careers.views.get_majors_data_v3'),
    url(r'^careers/getMajorsFilters/$','careers.views.get_majors_filters'),
    url(r'^careers/getSingleMajorData/(\d+)/$','careers.views.get_major_data'),
    url(r'^careers/getInternshipData/$', 'careers.views.get_internship_data'),
    url(r'^careers/getInternshipFilters/$', 'careers.views.get_internship_filters'),

    ## Accounts - AJAX calls
    url(r'^accounts/updateProfile/$', 'accounts.views.updateProfile'),
    url(r'^accounts/addToProfile/$','accounts.views.add_to_profile'),
    url(r'^accounts/deleteItem/$', 'accounts.views.deleteItem'),
    url(r'^accounts/connect/$', 'accounts.views.connect'),

    ## Social -- AJAX calls
    url(r'^social/saveComment/$', 'social.views.saveComment'),
    url(r'^social/followThread/$', 'social.views.followThread'),
    url(r'^social/unfollowThread/$', 'social.views.unfollowThread'),   
    url(r'^social/updateVotes/$', 'social.views.updateVotes'),
    url(r'^social/postComment/$', 'social.views.postComment'),
    url(r'^social/createThread/$', 'social.views.createThread'),





    url(r'^decisions/', 'careers.views.getDecisions'),
    url(r'^login/','accounts.views.login'),
    
    url(r'^profile/(\d+)/$', 'accounts.views.profile'),
    url(r'^profile/org/(\d+)/$','entities.views.profile_org'),
    url(r'^account/register','accounts.views.register'),
    url(r'^account/authorize','accounts.views.linkedin_authorize'),
    url(r'^account/authenticate','accounts.views.linkedin_authenticate'),
    # url(r'^account/finish','accounts.views.finish_login'),
    url(r'^account/finish','accounts.views.finish_registration'),
    url(r'^account/link','accounts.views.finish_link'),
    url(r'^account/success','accounts.views.success'),
    url(r'^account/logout','accounts.views.logout'),
    url(r'^account/login','accounts.views.login'),
    url(r'^account/refused','accounts.views.linkedin_refused'),
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

    # url(r'^proto/$', 'careers.views.proto'),
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
