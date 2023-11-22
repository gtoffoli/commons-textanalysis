from django.contrib import admin
from django.urls import path
# from django.conf.urls import url
from django.urls import re_path as url
from django.views.generic import TemplateView
from django.conf import settings

from textanalysis import views

urlpatterns = [
    path('admin/', admin.site.urls),
    url(r"^$", views.ta_input, name="home"),
    url(r"^ta_input/$", views.ta_input, name="ta_input"),
    # wordlists and cohesion must be before parametric urls
    url(r"^wordlists/$", views.text_wordlists, name="text_wordlists_0"),
    url(r"^wordlists/(?P<file_key>[\w\d-]+)/$", views.text_wordlists, name="dependencywordlists_1"),
    url(r"^wordlists/(?P<file_key>[\w\d-]+)/(?P<obj_type>[\w\.-]+)/(?P<obj_id>[\w\d-]+)/$", views.text_wordlists, name="text_wordlists_3"),
    url(r"^wordlists/(?P<obj_type>[\w\.-]+)/(?P<obj_id>[\w\d-]+)/$", views.text_wordlists, name="text_wordlists_2"),
    url(r"^nounchunks/$", views.text_nounchunks, name="text_nounchunks_0"),
    url(r"^nounchunks/(?P<obj_type>[\w]{2,8})/(?P<obj_id>[\w\d-]+)/(?P<glossary_id>[\d-]+)/$", views.text_nounchunks, name="text_nounchunks_glossary"),
    url(r"^nounchunks/(?P<file_key>[\w\d-]+)/(?P<obj_type>[\w\.-]+)/(?P<obj_id>[\w\d-]+)/$", views.text_nounchunks, name="text_nounchunks_3"),
    url(r"^nounchunks/(?P<obj_type>[\w]{2,8})/(?P<obj_id>[\w\d-]+)/$", views.text_nounchunks, name="text_nounchunks_2"),
    url(r"^nounchunks/(?P<file_key>[\w\d-]+)/$", views.text_nounchunks, name="text_nounchunks_1"),
    url(r"^cohesion/$", views.text_cohesion, name="text_cohesion_0"),
    url(r"^cohesion/(?P<file_key>[\w\d-]+)/$", views.text_cohesion, name="text_cohesion_1"),
    url(r"^cohesion/(?P<file_key>[\w\d-]+)/(?P<obj_type>[\w\.-]+)/(?P<obj_id>[\w\d]+)/$", views.text_cohesion, name="text_cohesion_3"),
    url(r"^cohesion/(?P<obj_type>[\w\.-]+)/(?P<obj_id>[\w\d-]+)/$", views.text_cohesion, name="text_cohesion_2"),
    url(r"^dependency/$", views.text_dependency, name="text_dependency_0"),
    url(r"^dependency/(?P<file_key>[\w\d-]+)/$", views.text_dependency, name="text_dependency_1"),
    url(r"^dependency/(?P<file_key>[\w\d-]+)/(?P<obj_type>[\w\.-]+)/(?P<obj_id>[\w\d-]+)/$", views.text_dependency, name="text_dependency_3"),
    url(r"^dependency/(?P<obj_type>[\w]{2,8})/(?P<obj_id>[\w\d-]+)/$", views.text_dependency, name="text_dependency_2"),

    url(r"^annotations/(?P<file_key>[\w\d-]+)/(?P<obj_type>[\w\.-]+)/(?P<obj_id>[\w\d-]+)/$", views.text_annotation, name="text_annotation_3"),
    url(r"^annotations/(?P<obj_type>[\w]{2,8})/(?P<obj_id>[\w\d-]+)/$", views.text_annotation, name="text_annotation_2"),

    url(r"^context_dashboard/$", views.context_dashboard, name="context_dashboard_0"),
    url(r"^context_dashboard/(?P<file_key>[\w\d-]+)/$", views.context_dashboard, name="context_dashboard_1"),
    url(r"^context_dashboard/(?P<file_key>[\w\d-]+)/(?P<obj_type>[\w\.-]+)/(?P<obj_id>[\w\d-]+)/$", views.context_dashboard, name="context_dashboard_3"),
    url(r"^context_dashboard/(?P<obj_type>[\w\.-]+)/(?P<obj_id>[\w\d-]+)/$", views.context_dashboard, name="context_dashboard_2"),

    url(r"^text_dashboard/$", views.text_dashboard, name="text_dashboard_0"),
    url(r"^text_dashboard/(?P<file_key>[\w\d-]+)/$", views.text_dashboard, name="text_dashboard_1"),
    url(r"^text_dashboard/(?P<file_key>[\w\d-]+)/(?P<obj_type>[\w\.-]+)/(?P<obj_id>[\w\d-]+)/$", views.text_dashboard, name="text_dashboard_3"),
    url(r"^text_dashboard/(?P<obj_type>[\w]{2,8})/(?P<obj_id>[\w\d-]+)/$", views.text_dashboard, name="text_dashboard"),
    url(r"^text_dashboard/(?P<obj_type>[\w]{2,8})/(?P<obj_id>[\w\d]+)$", views.text_dashboard, name="text_dashboard_unterminated"),
    url(r"^text_dashboard/(?P<obj_type>[\w]{2,8})/(?P<obj_id>.+)$", views.text_dashboard, name="text_dashboard_by_url"),
    url(r"^text_dashboard/(?P<obj_type>[\w]{2,8})/(?P<obj_id>[\w\d-]+)/$", views.text_dashboard, name="text_dashboard_by_url"),

    url(r"^corpus_dashboard/(?P<file_key>[\w\.-]+)/$", views.corpus_dashboard, name="corpus_dashboard"),

    url(r"^contents/$", views.ajax_contents, name="ajax_contents"),
    url(r"^new_corpus/$", views.ajax_new_corpus, name="ajax_new_corpus"),
    url(r"^make_corpus/$", views.ajax_make_corpus, name="ajax_make_corpus"),
    # url(r"^get_corpora/$", views.ajax_get_corpora, name="ajax_get_corpora"),
    url(r"^delete_corpus/$", views.ajax_delete_corpus, name="ajax_delete_corpus"),
    url(r"^insert_item/$", views.ajax_insert_item, name="ajax_insert_item"),
    url(r"^resource_to_item/$", views.ajax_resource_to_item, name="ajax_resource_to_item"),
    url(r"^file_to_item/(?P<file_key>[\w\d-]+)/$", views.ajax_file_to_item, name="ajax_file_to_item"),
    url(r"^add_terms_to_item/$", views.ajax_add_terms_to_item, name="ajax_add_terms_to_item"),
    url(r"^remove_item/$", views.ajax_remove_item, name="ajax_remove_item"),
    url(r"^corpus_update/$", views.ajax_corpus_update, name="ajax_corpus_update"),
    url(r"^compare_resources/$", views.ajax_compare_resources, name="ajax_compare_resources"),

    url(r"^glossaries/$", views.tbx_edit, name="tbx_edit"),
    url(r"^tbx_upload/$", views.tbx_upload, name="tbx_upload"),

    url(r"^test_vue$", TemplateView.as_view(template_name="test_vue.html"), name="test_vue"),
]

if 'commons' in settings.INSTALLED_APPS:
    urlpatterns += [
        url(r"^tbx_view/$", views.tbx_view, name="tbx_view"),
        url(r"^tbx_view/(?P<obj_type>[\w\.-]+)/(?P<obj_id>[\w\d-]+)/$", views.tbx_view, name="tbx_view_2"),
        url(r"^tbx_export/$", views.tbx_export, name="tbx_export"),
        url('glossary-autocomplete/$', views.glossary_autocomplete, name='glossary-autocomplete',),
        url(r"^corpora/$", views.corpora, name="corpora"),
    ]

urlpatterns += [
    url(r"^(?P<function>[\w\.-]+)/(?P<file_key>[\w\.-]+)/$", views.ta, name="text_analysis_1"),
    url(r"^(?P<function>[\w\.-]+)/(?P<file_key>[\w\.-]+)/(?P<obj_type>[\w\.-]+)/(?P<obj_id>[\w\d-]+)/$", views.ta, name="text_analysis_3"),
    url(r"^(?P<function>[\w\.-]+)/(?P<obj_type>[\w]{2,8})/(?P<obj_id>[\w\d-]+)/$", views.ta, name="text_analysis_2"),
]
