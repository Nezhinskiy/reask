"""Postgres-backed stores. The shared Redis is used only by the job queue (worker/)."""

import os

DATABASE_URL = os.environ["DATABASE_URL"]
