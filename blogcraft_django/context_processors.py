def font_awesome_kit(request):
    from django.conf import settings
    return {'font_awesome_kit': settings.FONT_AWESOME_KIT}