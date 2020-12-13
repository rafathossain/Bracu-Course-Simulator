from django import template
from django.contrib.auth.models import User, Group
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

register = template.Library()


# @register.filter(name='group_has_permission')
@register.simple_tag
def get_updated_by(name):
    return name[:4] + "******" + name[-4:]
