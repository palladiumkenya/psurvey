from django.shortcuts import render


# Create your views here.
def error403(request, *args, **kwargs):
    return render(request, 'errorPages/403_forbidden.html')


def error_404(request, *args, **kwargs):
    data = {}
    return render(request, 'errorPages/404_pagenotfound.html', data)
