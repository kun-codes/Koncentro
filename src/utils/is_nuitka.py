def is_nuitka() -> bool:
    # Check if the code is being run by Nuitka
    return globals().get("__compiled__", False)
