from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def filter_status(queryset, status):
    return queryset.filter(status=status)


@register.filter
def timesince_hours(datetime_obj):
    from django.utils import timezone
    delta = timezone.now() - datetime_obj
    return delta.total_seconds() / 3600