from django.urls import path
from . import views

app_name = "stories"

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('gallery/', views.story_list, name='story_list'),
    path('story/<slug:slug_story>/', views.story_detail, name='story_detail'),
    path('entry/<slug:slug_entry>/', views.entry_detail, name='entry_detail'),
    path('search/', views.search, name='search'),
    path('story/<slug:slug_story>/settings/', views.story_settings, name='story_settings'),
    path('story/<slug:slug_story>/delete/', views.delete_story, name='delete_story'),
    path('story/<slug:slug_story>/edit_permissions/', views.edit_story_permissions, name='edit_story_permissions'),
    path('story/<slug:slug_story>/revoke_permission/<int:user_pk>/', views.revoke_user_permission, name='revoke_user_permission'),
    path('story/<slug:slug_story>/download/', views.story_download, name='story_download'),
    path('notifications/', views.notifications_all, name='notifications_all'),
    path('notifications/unread/', views.notifications_unread, name='notifications_unread'),
    path('notifications/read/', views.notifications_read, name='notifications_read'),
]