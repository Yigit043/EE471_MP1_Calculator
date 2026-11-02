"""Library system classes: generic media items, their subtypes and a collection.

Week 4 additions: unique ids, to_dict(), custom exceptions and CRUD methods on
LibraryCollection. All business rules live here; app.py only translates HTTP.
"""


# --------------------------------------------------------------------------
# Exceptions
# --------------------------------------------------------------------------
class ItemNotFoundError(Exception):
    """Raised when no item with the requested id exists in the collection."""


class ItemStateError(Exception):
    """Raised when an action conflicts with the item's current state
    (e.g. checking out an item that is already out, deleting a checked-out item)."""


# --------------------------------------------------------------------------
# Items
# --------------------------------------------------------------------------
class MediaItem:
    """A generic item in a library that can be checked out and returned."""

    TYPE = "media"                       # overridden by subclasses
    EDITABLE_FIELDS = ("title", "author")

    def __init__(self, title, author, is_available=True):
        """Create an item with a title, an author and an availability flag."""
        self.id = None                   # assigned by LibraryCollection.add_item()
        self.title = self._check_text("title", title)
        self.author = self._check_text("author", author)
        self.is_available = bool(is_available)

    # --- validation helpers -------------------------------------------------
    @staticmethod
    def _check_text(name, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a non-empty string")
        return value.strip()

    @staticmethod
    def _check_positive_int(name, value):
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"{name} must be a positive integer")
        return value

    # --- state changes ------------------------------------------------------
    def checkout(self):
        """Check the item out. Raises ItemStateError if it is already out."""
        if not self.is_available:
            raise ItemStateError(f"'{self.title}' is already checked out")
        self.is_available = False
        return "Successful checkout"

    def return_item(self):
        """Return the item. Raises ItemStateError if it was not checked out."""
        if self.is_available:
            raise ItemStateError(f"'{self.title}' is not checked out")
        self.is_available = True
        return "Successful return"

    # --- editing ------------------------------------------------------------
    def update(self, **fields):
        """Update editable fields only. Anything else raises ValueError."""
        for name in fields:
            if name not in self.EDITABLE_FIELDS:
                raise ValueError(f"Field '{name}' cannot be changed on a {self.TYPE}")
        for name, value in fields.items():
            setattr(self, name, self._validate_field(name, value))

    def _validate_field(self, name, value):
        if name in ("title", "author"):
            return self._check_text(name, value)
        return value

    # --- representation -----------------------------------------------------
    def to_dict(self):
        """Return the item as a plain dict (used by the JSON API)."""
        return {
            "id": self.id,
            "type": self.TYPE,
            "title": self.title,
            "author": self.author,
            "is_available": self.is_available,
        }

    def __str__(self):
        """Return the item as "#id Title by Author [Available/Checked Out]"."""
        status = "Available" if self.is_available else "Checked Out"
        return f"#{self.id} {self.title} by {self.author} [{status}]"


class Book(MediaItem):
    """A library book that also knows its page count."""

    TYPE = "book"
    EDITABLE_FIELDS = ("title", "author", "page_count")

    def __init__(self, title, author, page_count, is_available=True):
        """Create a book with its page count."""
        super().__init__(title, author, is_available)
        self.page_count = self._check_positive_int("page_count", page_count)

    def _validate_field(self, name, value):
        if name == "page_count":
            return self._check_positive_int(name, value)
        return super()._validate_field(name, value)

    def to_dict(self):
        """Base fields plus page_count."""
        data = super().to_dict()
        data["page_count"] = self.page_count
        return data

    def __str__(self):
        """Return the base description followed by the page count."""
        return f"{super().__str__()} - {self.page_count} pages"


class DVD(MediaItem):
    """A fragile DVD that reminds the borrower to handle it with care."""

    TYPE = "dvd"
    EDITABLE_FIELDS = ("title", "author", "duration")
    CARE_REMINDER = "Handle with care: Do not scratch the disc."

    def __init__(self, title, author, duration, is_available=True):
        """Create a DVD with its duration in minutes."""
        super().__init__(title, author, is_available)
        self.duration = self._check_positive_int("duration", duration)

    def checkout(self):
        """Check the DVD out. The care reminder is part of the returned
        message instead of being printed (Week 4 change)."""
        result = super().checkout()          # raises ItemStateError if already out
        return f"{result}. {self.CARE_REMINDER}"

    def _validate_field(self, name, value):
        if name == "duration":
            return self._check_positive_int(name, value)
        return super()._validate_field(name, value)

    def to_dict(self):
        """Base fields plus duration."""
        data = super().to_dict()
        data["duration"] = self.duration
        return data

    def __str__(self):
        """Return the base description followed by the duration."""
        return f"{super().__str__()} - {self.duration} min"


# --------------------------------------------------------------------------
# Collection
# --------------------------------------------------------------------------
class LibraryCollection:
    """A container that holds the library's media items and enforces the rules."""

    ITEM_TYPES = {"book": Book, "dvd": DVD}

    def __init__(self):
        """Create an empty collection."""
        self.items = []
        self._next_id = 1                # ids are never reused, even after delete

    # --- create -------------------------------------------------------------
    def add_item(self, item):
        """Add a MediaItem (or subclass), assign it the next id and return the id."""
        if not isinstance(item, MediaItem):
            raise ValueError("Only MediaItem objects can be added")
        item.id = self._next_id
        self._next_id += 1
        self.items.append(item)
        return item.id

    def create_item(self, data):
        """Build a Book or DVD from a dict like the API receives and add it.

        Expected keys: type ("book"/"dvd"), title, author and page_count (book)
        or duration (dvd). Raises ValueError on bad input. Returns the new item.
        """
        if not isinstance(data, dict):
            raise ValueError("Item data must be an object")
        item_type = str(data.get("type", "")).lower()
        cls = self.ITEM_TYPES.get(item_type)
        if cls is None:
            raise ValueError("type must be 'book' or 'dvd'")

        extra_key = "page_count" if cls is Book else "duration"
        missing = [k for k in ("title", "author", extra_key) if k not in data]
        if missing:
            raise ValueError(f"Missing field(s): {', '.join(missing)}")

        item = cls(data["title"], data["author"], data[extra_key])
        self.add_item(item)
        return item

    # --- read ---------------------------------------------------------------
    def get_item(self, item_id):
        """Return the item with this id, or raise ItemNotFoundError."""
        for item in self.items:
            if item.id == item_id:
                return item
        raise ItemNotFoundError(f"Item {item_id} not found")

    def list_items(self, available=None, item_type=None):
        """Return all items, optionally filtered by availability and/or type.

        available: None (all), True or False.
        item_type: None (all), "book" or "dvd". Unknown type raises ValueError.
        """
        if item_type is not None:
            item_type = str(item_type).lower()
            if item_type not in self.ITEM_TYPES:
                raise ValueError("type filter must be 'book' or 'dvd'")
        result = []
        for item in self.items:
            if available is not None and item.is_available != available:
                continue
            if item_type is not None and item.TYPE != item_type:
                continue
            result.append(item)
        return result

    def list_available(self):
        """Return the titles of the items that are currently available (Week 3 API)."""
        return [item.title for item in self.list_items(available=True)]

    # --- update -------------------------------------------------------------
    def update_item(self, item_id, **fields):
        """Update only editable fields (title, author, page_count, duration).

        Trying to change id, type or is_available (or any unknown field)
        raises ValueError. Returns the updated item.
        """
        item = self.get_item(item_id)           # may raise ItemNotFoundError
        if not fields:
            raise ValueError("No fields to update")
        item.update(**fields)                   # may raise ValueError
        return item

    # --- delete -------------------------------------------------------------
    def remove_item(self, item_id):
        """Remove the item. Raises ItemStateError if it is checked out."""
        item = self.get_item(item_id)
        if not item.is_available:
            raise ItemStateError(f"Cannot delete '{item.title}': it is checked out")
        self.items.remove(item)
