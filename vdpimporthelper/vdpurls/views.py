from django.shortcuts import render


def home(request):
    # Keep nav state explicit for template-driven highlighting.
    context = {'expand': 'expand', 'hh': 'active'}
    return render(request, 'home.html', context)


def vdp_urls(request, highlight):
    # Preserve `highlight` in context for future template use.
    context = {'expand': 'expand', 'vh': 'active', 'highlight': highlight}
    return render(request, 'about.html', context)
