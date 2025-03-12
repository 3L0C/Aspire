#!/usr/bin/env python3

from datetime import datetime

def inject_now():
    """Inject the current datetime into templates."""
    return {'now': datetime.now()}
