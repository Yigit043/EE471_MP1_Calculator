"""Voice commands for the library: spoken text -> REST request, and response -> spoken reply.

parse_command("Check out item 3")
    -> Command(intent="checkout", method="POST", path="/api/items/3/checkout", body=None, item_id=3)
reply_for(command, status, data, item)
    -> "Item 3, 'Dune', has been checked out."

Nothing here touches the library directly: app.py sends the parsed request to the real
REST endpoint, so voice and HTTP clients follow exactly the same rules and status codes.
"""
import re
from dataclasses import dataclass, field

# --------------------------------------------------------------------------
# Small text helpers
# --------------------------------------------------------------------------
NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "to": 2, "too": 2, "three": 3, "four": 4, "for": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30,
    "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}


def words_to_int(text):
    """'220' -> 220, 'two hundred twenty' -> 220, 'three' -> 3. Returns None if not a number."""
    text = text.strip().lower().replace(",", "").replace("-", " ")
    match = re.match(r"^\d+", text)
    if match:
        return int(match.group())
    total, current, seen = 0, 0, False
    for word in text.split():
        if word in NUMBER_WORDS:
            current += NUMBER_WORDS[word]
            seen = True
        elif word == "hundred" and seen:
            current *= 100
        elif word == "thousand" and seen:
            total += current * 1000
            current = 0
        elif word == "and" and seen:
            continue
        else:
            break
    return total + current if seen else None


def clean_value(text):
    """Strip separators the speech recogniser adds around a spoken value."""
    text = text.strip(" ,;:.!?\"'")
    text = re.sub(r"^(to|is|as|=)\s+", "", text, flags=re.I)        # "title to Dune" -> "Dune"
    return text.strip(" ,;:.!?\"'")


ITEM_ID = re.compile(
    r"\bitem\s*(?:number\s*|no\.?\s*|#\s*)?(\d+|[a-z]+(?:[\s-][a-z]+)*?)(?=$|[\s,.!?])", re.I)


def find_item_id(text):
    """'check out item 3' / 'item number three' / 'item #3' -> 3."""
    for match in ITEM_ID.finditer(text):
        value = words_to_int(match.group(1))
        if value is not None:
            return value
    return None


# Field keywords a user can say, mapped to the API's field names
FIELD_WORDS = [
    (r"page\s*count|number of pages|pages?", "page_count"),
    (r"duration|length|minutes?", "duration"),
    (r"title|name", "title"),
    (r"author|director|by", "author"),
    (r"type", "type"),
]
FIELD_PATTERN = re.compile(
    r"\b(" + "|".join(p for p, _ in FIELD_WORDS) + r")\b", re.I)


def field_name(word):
    for pattern, name in FIELD_WORDS:
        if re.fullmatch(pattern, word, re.I):
            return name
    return None


def extract_fields(text):
    """'title The Hobbit, author Tolkien, pages 310' -> {'title': 'The Hobbit', ...}.

    The value of a field is everything between its keyword and the next keyword.
    "116 minutes" (number before the word) is also understood as a duration.
    """
    fields = {}
    matches = list(FIELD_PATTERN.finditer(text))
    for i, match in enumerate(matches):
        name = field_name(match.group(1))
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        value = clean_value(text[match.end():end])
        # "author Ridley Scott 117 minutes": the number belongs to the next field (duration)
        if i + 1 < len(matches) and re.fullmatch(r"minutes?", matches[i + 1].group(1), re.I):
            value = re.sub(r"[\s,]*\d+$", "", value)
        if name == "duration" and not value:
            # "116 minutes": the number came before the keyword
            before = text[:match.start()].rstrip(" ,")
            number = re.search(r"(\d+)\s*$", before)
            value = number.group(1) if number else ""
        if not value or name in fields:
            continue
        fields[name] = value

    for key in ("page_count", "duration"):
        if key in fields:
            number = words_to_int(fields[key])
            fields[key] = number if number is not None else fields[key]
    if "type" in fields:
        fields["type"] = normalise_type(fields["type"])
    return fields


def normalise_type(text):
    text = text.lower().replace(".", "").replace(" ", "")
    if text.startswith("book"):
        return "book"
    if text.startswith("dvd") or text.startswith("movie") or text.startswith("film"):
        return "dvd"
    return text


def detect_type(text):
    """Type mentioned without the 'type' keyword: 'create a DVD ...', 'list available books'."""
    lowered = text.lower()
    if re.search(r"\b(d\.?\s?v\.?\s?d\.?s?|movies?|films?)\b", lowered):
        return "dvd"
    if re.search(r"\bbooks?\b", lowered):
        return "book"
    return None


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------
@dataclass
class Command:
    intent: str                 # create, list, get, replace, update, delete, checkout, return, help
    method: str = ""
    path: str = ""
    body: dict = field(default_factory=dict)
    item_id: int = None
    heard: str = ""


HELP_TEXT = ("You can say, for example: create item, type book, title Dune, author Frank Herbert, "
             "pages 412. Or: list available books, get item 2, change item 2 title to Arrival, "
             "check out item 3, return item 3, or delete item 3.")


def parse_command(text):
    """Turn the recognised sentence into a REST request (method, path, JSON body)."""
    heard = text.strip()
    t = heard.lower()
    item_id = find_item_id(heard)

    def needs_id(intent, method, suffix=""):
        if item_id is None:
            return Command("missing_id", heard=heard, body={"for": intent})
        return Command(intent, method, f"/api/items/{item_id}{suffix}", None, item_id, heard)

    # Order matters: "check out" before "check", "return" before anything else with "item"
    if re.search(r"\bcheck\s*-?\s*out\b|\bborrow\b|\blend\b", t):
        return needs_id("checkout", "POST", "/checkout")
    if re.search(r"\breturn(ed)?\b|\bgive back\b|\bbring back\b", t):
        return needs_id("return", "POST", "/return")
    if re.search(r"\b(delete|remove)\b", t):
        return needs_id("delete", "DELETE")

    if re.search(r"\b(create|add|new)\b", t):
        fields = extract_fields(heard)
        body = {"type": fields.get("type") or detect_type(heard)}
        for key in ("title", "author", "page_count", "duration"):
            if key in fields:
                body[key] = fields[key]
        if body["type"] == "book":
            body.pop("duration", None)
        elif body["type"] == "dvd":
            body.pop("page_count", None)
        return Command("create", "POST", "/api/items", body, None, heard)

    if re.search(r"\breplace\b", t):
        cmd = needs_id("replace", "PUT")
        if cmd.intent == "replace":
            cmd.body = fields_for_update(heard)
        return cmd
    if re.search(r"\b(update|change|set|edit|rename|modify)\b", t):
        cmd = needs_id("update", "PATCH")
        if cmd.intent == "update":
            cmd.body = fields_for_update(heard)
        return cmd

    if item_id is not None and re.search(r"\b(get|show|find|what|tell|describe|details|info|read)\b", t):
        return Command("get", "GET", f"/api/items/{item_id}", None, item_id, heard)

    if re.search(r"\b(list|show|items|books|dvds?|movies|catalog|catalogue|available)\b", t):
        query = []
        if re.search(r"\bavailable\b|\bnot checked out\b|\bin stock\b", t):
            query.append("available=true")
        elif re.search(r"\b(checked out|borrowed|unavailable)\b", t):
            query.append("available=false")
        kind = detect_type(heard)
        other = re.search(r"\blist (?:all |available )?(magazines?|cds?|games?|newspapers?)\b", t)
        if kind:
            query.append(f"type={kind}")
        elif other:                                   # an unsupported type -> the API answers 400
            query.append(f"type={other.group(1).rstrip('s')}")
        path = "/api/items" + ("?" + "&".join(query) if query else "")
        return Command("list", "GET", path, None, None, heard)

    if item_id is not None:
        return Command("get", "GET", f"/api/items/{item_id}", None, item_id, heard)
    if re.search(r"\bhelp\b|what can i say", t):
        return Command("help", heard=heard)
    return Command("unknown", heard=heard)


def fields_for_update(text):
    """Fields for PUT/PATCH. 'item 3' itself is removed first so '3' is not read as a value."""
    without_id = ITEM_ID.sub(" ", text)
    without_id = re.sub(r"\bof\s*(?=,|$|\s)", " ", without_id)       # "the title of item 3 to X"
    fields = extract_fields(without_id)
    fields.pop("type", None)                 # type is not editable; let the API decide via body
    return fields


# --------------------------------------------------------------------------
# Replies ("the librarian")
# --------------------------------------------------------------------------
def describe(item):
    extra = (f"{item['page_count']} pages" if item.get("type") == "book"
             else f"{item.get('duration')} minutes")
    state = "available" if item.get("is_available") else "checked out"
    return f"the {item_kind(item)} '{item['title']}' by {item['author']}, {extra}, currently {state}"


def item_kind(item):
    return "DVD" if item.get("type") == "dvd" else "book"


def join_titles(items):
    titles = [f"'{i['title']}'" for i in items]
    if len(titles) <= 1:
        return "".join(titles)
    return ", ".join(titles[:-1]) + " and " + titles[-1]


def reply_for(cmd, status, data, before=None):
    """The sentence the librarian says after the REST call.

    status/data: the REST endpoint's response. before: the item as it was before the call
    (used to name the item in replies to DELETE, which returns no body).
    """
    data = data or {}
    error = data.get("error", "") if isinstance(data, dict) else ""
    iid = cmd.item_id
    title = (before or {}).get("title")
    named = f"Item {iid}, '{title}'," if title else f"Item {iid}"

    if status == 404:
        return f"Sorry, I could not find item {iid}."

    if cmd.intent == "create":
        if status == 201:
            return f"Successfully created {item_kind(data)} '{data['title']}' with ID {data['id']}."
        return f"Sorry, I could not create the item. {error}"

    if cmd.intent == "checkout":
        if status == 200:
            item = data.get("item", {})
            extra = " Please handle the disc with care." if item.get("type") == "dvd" else ""
            return f"Item {iid}, '{item.get('title')}', has been checked out.{extra}"
        if status == 409:
            return f"Sorry, item {iid} is already checked out."

    if cmd.intent == "return":
        if status == 200:
            return f"Item {iid}, '{data.get('item', {}).get('title')}', has been returned. Thank you."
        if status == 409:
            return f"Sorry, item {iid} is not checked out."

    if cmd.intent == "delete":
        if status == 204:
            return f"{named} has been deleted."
        if status == 409:
            return f"Sorry, item {iid} is checked out, so it cannot be deleted."

    if cmd.intent in ("replace", "update"):
        if status == 200:
            changed = ", ".join(
                f"{k.replace('_', ' ')} {data.get(k)}" for k in (cmd.body or {}) if k in data)
            return f"Item {iid} has been updated: {changed}." if changed else f"Item {iid} has been updated."
        return f"Sorry, I could not update item {iid}. {error}"

    if cmd.intent == "get" and status == 200:
        return f"Item {iid} is {describe(data)}."

    if cmd.intent == "list":
        if status == 200:
            kind = "DVDs" if "type=dvd" in cmd.path else "books" if "type=book" in cmd.path else "items"
            which = ("available " if "available=true" in cmd.path
                     else "checked out " if "available=false" in cmd.path else "")
            if not data:
                return f"There are no {which}{kind} in the library."
            noun = kind if len(data) != 1 else kind[:-1]
            return f"I found {len(data)} {which}{noun}: {join_titles(data)}."
        return f"Sorry, {error}"

    return f"Sorry, something went wrong. {error}".strip()
