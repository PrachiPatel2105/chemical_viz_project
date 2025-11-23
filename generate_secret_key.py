#!/usr/bin/env python
"""
Generate a secure Django SECRET_KEY
Run this script to generate a new random secret key for production
"""

from django.core.management.utils import get_random_secret_key

if __name__ == "__main__":
    secret_key = get_random_secret_key()
    print("\n" + "="*60)
    print("DJANGO SECRET_KEY GENERATED")
    print("="*60)
    print(f"\n{secret_key}\n")
    print("="*60)
    print("\nCopy this key and use it in your Render environment variables:")
    print("SECRET_KEY = " + secret_key)
    print("\n⚠️  IMPORTANT: Keep this key secret and never commit it to Git!")
    print("="*60 + "\n")
