def header(header_text, color = "bright_green"):
    """Prints header information for the script with the specified color and box frame."""
    colors = {
        "bright_green": "\033[92m",
        "yellow": "\033[93m",
        "reset": "\033[0m"
    }
    color_code = colors.get(color, colors["bright_green"])
    width = len(header_text) + 4
    print(f"\n{color_code}╔{'═' * width}╗")
    print(f"║  {header_text}  ║")
    print(f"╚{'═' * width}╝{colors['reset']}\n")