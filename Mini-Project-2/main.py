"""Demo script: calls every LibraryCollection / item method once and shows
every exception being raised and caught (Week 4, Section 2 - Part 2)."""

from custom_classes import (
    Book, DVD, LibraryCollection, ItemNotFoundError, ItemStateError,
)


def show(library):
    """Print every item in the collection."""
    for item in library.items:
        print("  ", item)


def main():
    library = LibraryCollection()

    # --- add_item(): ids are assigned 1, 2, 3 ... and returned ---------------
    print("--- add_item ---")
    id1 = library.add_item(Book("Dune", "Frank Herbert", 412))
    id2 = library.add_item(DVD("Arrival", "Denis Villeneuve", 116))
    id3 = library.add_item(Book("Neuromancer", "William Gibson", 271))
    print("assigned ids:", id1, id2, id3)
    show(library)

    # --- to_dict() -----------------------------------------------------------
    print("\n--- to_dict ---")
    for item in library.items:
        print("  ", item.to_dict())

    # --- get_item() ----------------------------------------------------------
    print("\n--- get_item ---")
    print("  ", library.get_item(2))
    try:
        library.get_item(99)
    except ItemNotFoundError as exc:
        print("   ItemNotFoundError:", exc)

    # --- checkout() / return_item() ------------------------------------------
    print("\n--- checkout / return_item ---")
    dvd = library.get_item(2)
    print("  ", dvd.checkout())            # reminder is in the message, not printed
    try:
        dvd.checkout()                      # already out
    except ItemStateError as exc:
        print("   ItemStateError:", exc)
    print("  ", dvd.return_item())
    try:
        dvd.return_item()                   # not checked out
    except ItemStateError as exc:
        print("   ItemStateError:", exc)

    # --- list_items() with filters ------------------------------------------
    print("\n--- list_items ---")
    library.get_item(1).checkout()
    print("   all:       ", [i.title for i in library.list_items()])
    print("   available: ", [i.title for i in library.list_items(available=True)])
    print("   books:     ", [i.title for i in library.list_items(item_type="book")])
    print("   avail dvds:", [i.title for i in library.list_items(available=True, item_type="dvd")])
    try:
        library.list_items(item_type="magazine")
    except ValueError as exc:
        print("   ValueError:", exc)

    # --- update_item() -------------------------------------------------------
    print("\n--- update_item ---")
    print("  ", library.update_item(3, title="Neuromancer (Remastered)", page_count=300))
    try:
        library.update_item(3, is_available=True)      # not editable
    except ValueError as exc:
        print("   ValueError:", exc)
    try:
        library.update_item(3, duration=90)            # a book has no duration
    except ValueError as exc:
        print("   ValueError:", exc)
    try:
        library.update_item(42, title="Ghost")         # unknown id
    except ItemNotFoundError as exc:
        print("   ItemNotFoundError:", exc)

    # --- remove_item() -------------------------------------------------------
    print("\n--- remove_item ---")
    try:
        library.remove_item(1)                         # Dune is checked out
    except ItemStateError as exc:
        print("   ItemStateError:", exc)
    library.remove_item(3)
    print("   after removing #3:")
    show(library)

    # --- ids are never reused -----------------------------------------------
    print("\n--- ids are never reused ---")
    new_id = library.add_item(DVD("Blade Runner", "Ridley Scott", 117))
    print("   new item got id", new_id, "(not 3)")
    show(library)

    # --- Week 3 helper still works ------------------------------------------
    print("\n--- list_available (Week 3) ---")
    print("  ", library.list_available())


if __name__ == "__main__":
    main()
