#!/usr/bin/env python3
import os
from celery_app import celery_app

if __name__ == '__main__':
    celery_app.start()
