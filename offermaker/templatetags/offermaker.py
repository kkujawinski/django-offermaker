from django import template
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def offermaker_javascript(skip=''):
    """
    HTML tag to insert offermaker javascript file
    """
    skip = (skip or '').split(',')

    output = []
    if 'sprintf' not in skip:
        url = static('sprintf.min.js')
        if url:
            output.append(u'<script src="%s"></script>' % url)

    url = static('offermaker.js')
    if url:
        output.append(u'<script src="%s"></script>' % url)


    return u''.join(output)


@register.simple_tag
def offermaker_css():
    """
    HTML tag to insert offermaker css file
    """
    url = static('offermaker.css')
    if url:
        return u'<link rel="stylesheet" href="%s">' % url
    return u''
