from sqlalchemy import or_, desc
from flask import request

def apply_search_and_pagination(query, model, search_fields=None, filter_params=None):
    """
    Apply search filters and pagination to a query.
    
    Args:
        query: SQLAlchemy query object
        model: The model being queried
        search_fields: List of model attributes (strings) to search against
        filter_params: Dictionary of filter parameters (e.g., {'status': 'Approved'})
        
    Returns:
        pagination object, search_query string
    """
    search_query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Apply global search
    if search_query and search_fields:
        search_filters = []
        for field in search_fields:
            attr = getattr(model, field)
            search_filters.append(attr.ilike(f'%{search_query}%'))
        query = query.filter(or_(*search_filters))

    # Apply specific filters
    if filter_params:
        for key, value in filter_params.items():
            if value:
                attr = getattr(model, key)
                query = query.filter(attr == value)

    # Sort by ID or creation date if possible
    if hasattr(model, 'created_at'):
        query = query.order_by(model.created_at.desc())
    elif hasattr(model, 'id'):
        query = query.order_by(model.id.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return pagination, search_query
