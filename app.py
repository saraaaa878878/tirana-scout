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


def filter_by_max_price(apartments, max_price):
    """Return only the apartments priced at or below max_price."""
    return [apt for apt in apartments if apt["price"] <= max_price]


def score_deals(apartments):
    """Label each apartment as 'good deal' or 'bad deal' based on price per sqm vs the average."""
    for apt in apartments:
        apt["price_per_sqm"] = apt["price"] / apt["sqm"]

    average_price_per_sqm = sum(apt["price_per_sqm"] for apt in apartments) / len(apartments)

    for apt in apartments:
        apt["deal"] = "good deal" if apt["price_per_sqm"] <= average_price_per_sqm else "bad deal"

    return apartments, average_price_per_sqm


def print_deal_scores(apartments, average_price_per_sqm):
    """Print each apartment's price per sqm and deal label."""
    print(f"Average price per m²: {average_price_per_sqm:.2f}€")
    for i, apt in enumerate(apartments, start=1):
        print(f"Apartment {i}: {apt['price_per_sqm']:.2f}€/m² -> {apt['deal']}")


if __name__ == "__main__":
    apartments = get_apartments()
    print_apartments(apartments)

    print("\n--- Apartments under 500€ ---")
    cheap = filter_by_max_price(apartments, 500)
    print_apartments(cheap)

    print("\n--- Apartments under 700€ ---")
    mid_range = filter_by_max_price(apartments, 700)
    print_apartments(mid_range)

    print("\n--- Deal Scores ---")
    scored_apartments, avg = score_deals(apartments)
    print_deal_scores(scored_apartments, avg)