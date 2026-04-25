"""
Management command to download real product images from Unsplash for each item.
Uses Unsplash's public source URLs (no API key required).
"""
import os
import urllib.request
import urllib.error
from django.core.management.base import BaseCommand
from django.conf import settings
from hub.models import Item

# Map item name keywords → Unsplash search query → direct source URL
# Using unsplash.com/photos/<id>/download?force=true style or picsum for reliable delivery
# We use specific curated Unsplash photo IDs for each product type

PRODUCT_IMAGE_MAP = {
    # Engineering drawing tools
    'mini drafter':         'https://images.unsplash.com/photo-1611532736597-de2d4265fba3?w=600&q=80',
    'roller scale':         'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&q=80',
    'drawing board':        'https://images.unsplash.com/photo-1503387762-592deb58ef4e?w=600&q=80',
    'set squares':          'https://images.unsplash.com/photo-1509228468518-180dd4864904?w=600&q=80',
    'compass set':          'https://images.unsplash.com/photo-1509228468518-180dd4864904?w=600&q=80',
    'french curves':        'https://images.unsplash.com/photo-1611532736597-de2d4265fba3?w=600&q=80',
    'mechanical pencil':    'https://images.unsplash.com/photo-1583485088034-697b5bc54ccd?w=600&q=80',
    'drafting brush':       'https://images.unsplash.com/photo-1513364776144-60967b0f800f?w=600&q=80',
    'drawing sheets':       'https://images.unsplash.com/photo-1568667256549-094345857637?w=600&q=80',
    'sheet protector':      'https://images.unsplash.com/photo-1568667256549-094345857637?w=600&q=80',
    'flap file':            'https://images.unsplash.com/photo-1568667256549-094345857637?w=600&q=80',
    'zipper file':          'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&q=80',
    # Textbooks
    'textbook':             'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600&q=80',
    'book':                 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600&q=80',
    # Lab equipment
    'microscope':           'https://images.unsplash.com/photo-1576086213369-97a306d36557?w=600&q=80',
    'calculator':           'https://images.unsplash.com/photo-1611532736597-de2d4265fba3?w=600&q=80',
    'lab coat':             'https://images.unsplash.com/photo-1582719471384-894fbb16e074?w=600&q=80',
    'arduino':              'https://images.unsplash.com/photo-1518770660439-4636190af475?w=600&q=80',
    # Appliances
    'fridge':               'https://images.unsplash.com/photo-1571175443880-49e1d25b2bc5?w=600&q=80',
    # Decor
    'decor':                'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=600&q=80',
}

# Category fallback images
CATEGORY_FALLBACKS = {
    'equipment': 'https://images.unsplash.com/photo-1509228468518-180dd4864904?w=600&q=80',
    'textbook':  'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600&q=80',
    'appliance': 'https://images.unsplash.com/photo-1571175443880-49e1d25b2bc5?w=600&q=80',
    'decor':     'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=600&q=80',
    'other':     'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&q=80',
}


def get_image_url(item):
    name_lower = item.name.lower()
    for keyword, url in PRODUCT_IMAGE_MAP.items():
        if keyword in name_lower:
            return url
    return CATEGORY_FALLBACKS.get(item.category, CATEGORY_FALLBACKS['other'])


class Command(BaseCommand):
    help = 'Download real product images from Unsplash for all items'

    def handle(self, *args, **options):
        media_dir = os.path.join(settings.MEDIA_ROOT, 'item_images')
        os.makedirs(media_dir, exist_ok=True)

        items = Item.objects.all()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        for item in items:
            url = get_image_url(item)
            safe_name = item.name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_').replace('°', '')
            filename = f'real_{item.id}_{safe_name}.jpg'
            filepath = os.path.join(media_dir, filename)

            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=15) as response:
                    with open(filepath, 'wb') as f:
                        f.write(response.read())

                item.image1 = f'item_images/{filename}'
                item.save(update_fields=['image1'])
                self.stdout.write(self.style.SUCCESS(f'✓ {item.name}'))

            except Exception as e:
                self.stdout.write(self.style.WARNING(f'✗ {item.name}: {e}'))
