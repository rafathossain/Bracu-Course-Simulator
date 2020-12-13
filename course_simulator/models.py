from django.db import models


class CourseList(models.Model):
	semester = models.CharField(max_length=200)
	course_code = models.CharField(max_length=50)
	section = models.IntegerField()
	total_seat = models.IntegerField(blank=True)
	faculty = models.CharField(max_length=50)
	instructor = models.TextField()
	exam_date = models.CharField(max_length=200, blank=True)
	exam_time = models.CharField(max_length=200, blank=True)
	sunday = models.CharField(max_length=200, blank=True)
	monday = models.CharField(max_length=200, blank=True)
	tuesday = models.CharField(max_length=200, blank=True)
	wednesday = models.CharField(max_length=200, blank=True)
	thursday = models.CharField(max_length=200, blank=True)
	friday = models.CharField(max_length=200, blank=True)
	saturday = models.CharField(max_length=200, blank=True)

	class Meta:
		db_table = 'course_list'


class UpdateLog(models.Model):
	updated_by = models.CharField(max_length=200)
	update_status = models.CharField(max_length=200, default="Processing")
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		db_table = 'update_log'
