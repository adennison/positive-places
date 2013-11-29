from django.conf.urls import patterns, include, url

url(r'^$', 'pos.views.welcome', name='welcome'),

urlpatterns = patterns('pos.views.welcome',
    url('^$', 'details'), # Set the root URL to point to the Home page
)

urlpatterns += patterns('pos.views.welcome',
    url(r'^welcome/', 'details', name='welcome'),
)

# urlpatterns = patterns('pos.views.home',
#     url('^$', 'details'), # Set the root URL to point to the Home page
# )

# urlpatterns += patterns('pos.views.home',
#     url(r'^home/$', 'details'),
# )

# urlpatterns += patterns('pos.views.disclaimer',
#     url(r'^disclaimer/$', 'details'),
# )

urlpatterns += patterns('pos.views.search',
    url(r'^search/', 'search'),
    url(r'^ajax_bbox_pos/', 'ajax_bbox_pos'),
    #url(r'^address_search/', 'address_search'),
)

urlpatterns += patterns('pos.views.address',
    url(r'^address/', 'index'),
)

urlpatterns += patterns('pos.views.about',
    url(r'^about/', 'details'),
)

urlpatterns += patterns('pos.views.contact_us',
    url(r'^contact_us/', 'details', name='contact_us'),
)

urlpatterns += patterns('pos.views.research_and_publications',
    url(r'^research_and_publications/', 'details'),
)

urlpatterns += patterns('pos.views.faq_framework_parks',
    url(r'^faq/faq_framework_parks/', 'details'),
)

urlpatterns += patterns('pos.views.faq_framework_natural',
    url(r'^faq/faq_framework_natural/', 'details'),
)

urlpatterns += patterns('pos.views.faq_framework_school',
    url(r'^faq/faq_framework_school/', 'details'),
)

urlpatterns += patterns('pos.views.faq_framework_residual',
    url(r'^faq/faq_framework_residual/', 'details'),
)

urlpatterns += patterns('pos.views.faq_database_audit',
    url(r'^faq/faq_database_audit/', 'details'),
)

urlpatterns += patterns('pos.views.faq_database_compilation',
    url(r'^faq/faq_database_compilation/', 'details'),
)

urlpatterns += patterns('pos.views.faq_database_computing',
    url(r'^faq/faq_database_computing/', 'details'),
)

urlpatterns += patterns('pos.views.faq_database_developing',
    url(r'^faq/faq_database_developing/', 'details'),
)

urlpatterns += patterns('pos.views.faq_database_verification',
    url(r'^faq/faq_database_verification/', 'details'),
)

urlpatterns += patterns('pos.views.faq_summary_general',
    url(r'^faq/faq_summary_general/', 'details'),
)

urlpatterns += patterns('pos.views.faq_summary_catchment',
    url(r'^faq/faq_summary_catchment/', 'details'),
)

urlpatterns += patterns('pos.views.faq_summary_quality',
    url(r'^faq/faq_summary_quality/', 'details'),
)

urlpatterns += patterns('pos.views.faq_summary_facility',
    url(r'^faq/faq_summary_facility/', 'details'),
)

# urlpatterns += patterns('pos.views.projects',
#     url(r'^projects/', 'details'),
# )

urlpatterns += patterns('pos.views.faq',
    url(r'^faq/', 'details', name='faq'),
)

urlpatterns += patterns('pos.views.pos_view',
    url(r'^pos/(?P<pk>\d+)/', 'details'),
)

urlpatterns += patterns('pos.views.region',
    url(r'^region/(?P<pk>\d+)/', 'details', name='load_region'),
    url(r'^download/', 'download_file'),
)

urlpatterns += patterns('pos.views.file_upload', # Python view file path
    url(r'^file_upload/$', 'upload_file'), # url, function name in Python file
    url(r'^load_data/$', 'load_data'),
    url(r'^load_data_currency/$', 'load_data_currency'),
    url(r'^upload_custom_region/$', 'upload_region', name='upload_region'),
)

urlpatterns += patterns('pos.views.login',
    url(r'^login/admin/$', 'login_admin_data_upload'),
    url(r'^login/user/$', 'login_user'),
    url(r'^logout/$', 'logout'),
)

urlpatterns += patterns('pos.views.project',
    url(r'^project/$', 'manage_projects'),
    url(r'^project/manage/$', 'manage_projects', name='manage_projects'),
    url(r'^project/add/$', 'add_project', name='add_project'),
    url(r'^project/delete/$', 'delete_project', name='delete_project'),
    url(r'^project/advanced/$', 'advanced', name='advanced_dashboard'),
)

urlpatterns += patterns('pos.views.user',
    url(r'^user/register/', 'register', name='register'),  # name= django reverse
)

urlpatterns += patterns('pos.views.user_region',
    #url(r'^user_region/user_region/', 'details', name='user_region'),
    # url(r'^user_region/user_region/$', 'validate_geometry'),
#    url(r'^user_region/(?P<pk>\d+)/', 'setup_user_region', name='setup_user_region'),
    url(r'^user_region/draw/(?P<pk>\d+)/', 'draw_user_region', name='draw_user_region'),
    url(r'^user_region/upload/(?P<pk>\d+)/', 'upload_user_region', name='upload_user_region'),
    url(r'^user_region/select_region/(?P<pk>\d+)/', 'select_lga_suburb_user_region', name='select_lga_suburb_user_region'),
    url(r'^user_region/save_user_region_polygon/$', 'save_user_region_polygon'),
)

urlpatterns += patterns('pos.views.user_stats',
    url(r'^user_stats/(?P<pk>\d+)/', 'details', name='scenario_modelling'),
    url(r'^user_stats/calculate_metrics/$', 'calculate_metrics'),
    url(r'^user_stats/save_modified_stats/$', 'save_modified_stats'),
    url(r'^user_stats/reset_areas/$', 'reset_areas'),
    url(r'^user_stats/reset_populations/$', 'reset_populations'),
    url(r'^user_stats/calculate_lga_stats/$', 'calculate_lga_stats'),
    url(r'^user_stats/calculate_suburb_stats/$', 'calculate_suburb_stats'),
    url(r'^user_stats/calculate_facility_stats/$', 'calculate_facility_stats'),
    url(r'^user_stats/download_scenario_stats/$', 'download_scenario_stats', name='download_scenario_stats'),
)

urlpatterns += patterns('',
    url(r'^captcha/', include('captcha.urls')),
)

# Password Reset
urlpatterns += patterns('',
    url(r'^accounts/password/reset/$', 'django.contrib.auth.views.password_reset',
        {'template_name': 'registration/password_reset.html'}, name="auth_password_reset"),
    url(r'^accounts/password/reset/done/$', 'django.contrib.auth.views.password_reset_done',
        {'template_name': 'registration/password_reset_done.html'}, name="auth_password_reset_done"),
    url(r'^accounts/password/reset/confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm',
        {'template_name': 'registration/password_reset_confirm.html'}, name='password_reset_confirm'),
    url(r'^accounts/password/reset/complete/$', 'django.contrib.auth.views.password_reset_complete',
        {'template_name': 'registration/password_reset_complete.html'}, name='password_reset_complete'),
)
