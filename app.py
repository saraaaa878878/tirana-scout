def get_apartments():
    """Return a list of fake Tirana apartment listings."""
    return [
        {"price": 450, "sqm": 55, "bedrooms": 1},
        {"price": 620, "sqm": 72, "bedrooms": 2},
        {"price": 380, "sqm": 40, "bedrooms": 1},
        {"price": 900, "sqm": 105, "bedrooms": 3},
        {"price": 550, "sqm": 65, "bedrooms": 2},
    ]


def print_apartments(apartments):
    """Print apartment listings in a readable format."""
    for i, apt in enumerate(apartments, start=1):
        print(f"Apartment {i}: {apt['price']}€/month | {apt['sqm']} m² | {apt['bedrooms']} bedroom(s)")


if __name__ == "__main__":
    apartments = get_apartments()
    print_apartments(apartments)