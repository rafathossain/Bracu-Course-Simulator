from django import template
from django.contrib.auth.models import User, Group
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
import datetime

register = template.Library()


# @register.filter(name='group_has_permission')
@register.simple_tag
def parse_date(date):
	if str(date).strip() != "":
		dateTimeStr = datetime.datetime.strptime(date, "%d-%m-%Y")
		return datetime.date(int(dateTimeStr.year), int(dateTimeStr.month), int(dateTimeStr.day)).strftime("%d %B %Y")
	else:
		return ""
