from django.urls import path, include
from .views import *

urlpatterns = [
	path('', welcome, name='welcome'),
	path('update-db/', updateDB, name='update.db'),
	path('courses/', coursesPage, name='courses'),
	path('courses/view/', coursesView, name='courses.view'),
	path('courses/session/', courseSession, name='courses.session')
]
