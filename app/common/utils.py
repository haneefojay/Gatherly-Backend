def paginate_list(items: list, page: int, size: int):
    """
    Paginate list

    Args:
        items (list): The list of items
        page (int): The page
        size (int): The size

    Returns:
        list
    """
    start = (page - 1) * size
    end = start + size

    return items[start:end] if start < len(items) else []
