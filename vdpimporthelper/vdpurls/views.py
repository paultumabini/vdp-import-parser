from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.


def home(request):
    context = {'expand': 'expand', 'hh': 'active'}
    return render(request, 'home.html', context)


def vdp_urls(request, highlight):
    print(highlight)
    context = {'expand': 'expand', 'vh': 'active'}
    return render(request, 'about.html', context)
