"""
Medicine Assistant Database Matcher Module
Delegates directly to database.py to maintain a single source of truth for
SQLite database management, fuzzy token matching, and persistent cache-on-the-fly storage.
"""

from database import MedicineDatabaseMatcher, MedicineDatabase

__all__ = ["MedicineDatabaseMatcher", "MedicineDatabase"]
