"""
Utility functions and helpers for the application.
"""

from datetime import datetime


def format_file_size(size_bytes: int) -> str:
    """
    Format bytes to human-readable file size.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Human-readable file size string
    """
    if size_bytes == 0:
        return "0B"
    
    size_names = ("B", "KB", "MB", "GB", "TB")
    i = int((len(str(int(size_bytes))) - 1) // 3)
    p = pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"


def format_datetime(dt: datetime, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    Format datetime object to string.
    
    Args:
        dt: Datetime object
        format_str: Format string
        
    Returns:
        Formatted datetime string
    """
    if dt is None:
        return ''
    return dt.strftime(format_str)


def get_page_number(request, default: int = 1) -> int:
    """
    Get page number from request args.
    
    Args:
        request: Flask request object
        default: Default page number
        
    Returns:
        Page number (integer >= 1)
    """
    try:
        page = int(request.args.get('page', default))
        return max(page, 1)
    except (ValueError, TypeError):
        return default


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def get_paginated_results(query, page: int = 1, per_page: int = 20):
    """
    Get paginated query results.
    
    Args:
        query: SQLAlchemy query object
        page: Page number (1-indexed)
        per_page: Results per page
        
    Returns:
        Paginated query results
    """
    page = max(page, 1)
    per_page = max(per_page, 1)
    return query.paginate(page=page, per_page=per_page)
