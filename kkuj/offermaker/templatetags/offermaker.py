from django import template
from django.templatetags.static import static

register = template.Library()

@register.simple_tag
def offermaker_javascript_tag(name=None):
    """
    HTML tag to insert bootstrap_toolkit javascript file
    """
    url = static('kkuj_offer_maker.js')
    if url:
        return u'<script src="%s"></script>' % url
    return u''
