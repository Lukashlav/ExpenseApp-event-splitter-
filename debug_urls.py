import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.urls import get_resolver

resolver = get_resolver()

for pattern in resolver.url_patterns:
    print(pattern)