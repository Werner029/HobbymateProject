import django.conf
import django.http
import django.shortcuts

app_name = 'download'


def file(request, path):
    print(path)
    return django.shortcuts.redirect('h' + path)
