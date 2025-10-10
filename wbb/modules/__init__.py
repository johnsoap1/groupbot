"""
MIT License

Copyright (c) 2024 TheHamkerCat

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import glob
import importlib
import sys
import traceback
from os.path import basename, dirname, isfile, join

# Initialize MOD_LOAD and MOD_NOLOAD with defaults if not set
MOD_LOAD = getattr(sys.modules.get('wbb'), 'MOD_LOAD', [])
MOD_NOLOAD = getattr(sys.modules.get('wbb'), 'MOD_NOLOAD', [])

def __list_all_modules():
    """Generate a list of all modules in the modules directory."""
    mod_paths = glob.glob(join(dirname(__file__), "*.py"))
    all_modules = [
        basename(f)[:-3]
        for f in mod_paths
        if isfile(f)
        and f.endswith(".py")
        and not f.endswith("__init__.py")
        and not f.endswith("__main__.py")
    ]
    
    print(f"[MODULE_LOADER] Found {len(all_modules)} modules: {', '.join(all_modules)}")
    
    # Apply MOD_LOAD and MOD_NOLOAD filters
    if MOD_LOAD:
        print(f"[MODULE_LOADER] MOD_LOAD is set, filtering modules: {MOD_LOAD}")
        all_modules = [m for m in all_modules if m in MOD_LOAD]
    
    if MOD_NOLOAD:
        print(f"[MODULE_LOADER] MOD_NOLOAD is set, excluding: {MOD_NOLOAD}")
        all_modules = [m for m in all_modules if m not in MOD_NOLOAD]
    
    print(f"[MODULE_LOADER] Final module list: {all_modules}")
    return all_modules

# Import __main__ module first to set up any required configurations
print("[MODULE_LOADER] Initializing core modules...")
try:
    importlib.import_module("wbb.modules.__main__")
    print("[MODULE_LOADER] Core modules initialized successfully")
except Exception as e:
    print(f"[MODULE_LOADER] Error initializing core modules: {e}")
    traceback.print_exc()

# Get the list of all modules to load
ALL_MODULES = sorted(__list_all_modules())
__all__ = ALL_MODULES + ["ALL_MODULES"]

print(f"[MODULE_LOADER] Total modules to load: {len(ALL_MODULES)}")
