#!/usr/bin/env python
"""
Patch script for fixing django.core.urlresolvers import in dynamic_forms package
"""
import os
import sys
import fileinput

def patch_dynamic_forms():
    try:
        # Get the site-packages directory
        import site
        site_packages = site.getsitepackages()[0]
        
        # Path to the dynamic_forms models.py file
        models_path = os.path.join(site_packages, 'dynamic_forms', 'models.py')
        
        if not os.path.exists(models_path):
            print(f"Error: Could not find {models_path}")
            return False
        
        print(f"Patching file: {models_path}")
        
        # Replace the import
        with fileinput.FileInput(models_path, inplace=True) as file:
            for line in file:
                if "from django.core.urlresolvers import reverse" in line:
                    print("from django.urls import reverse  # Fixed import for Django 2.0+", end='\n')
                else:
                    print(line, end='')
        
        print("Successfully patched dynamic_forms package!")
        return True
    
    except Exception as e:
        print(f"Error patching dynamic_forms: {str(e)}")
        return False

if __name__ == "__main__":
    success = patch_dynamic_forms()
    sys.exit(0 if success else 1)
