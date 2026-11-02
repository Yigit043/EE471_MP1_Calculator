"""Tests for the voice commands: run with   python -m unittest -v"""
import unittest

from app import app
from voice_commands import parse_command


class ParseTests(unittest.TestCase):
    def test_create_book_from_the_project_example(self):
        cmd = parse_command("Create item, type book, title The Catcher in the Rye, "
                            "author J.D. Salinger, pages 220.")
        self.assertEqual((cmd.method, cmd.path), ("POST", "/api/items"))
        self.assertEqual(cmd.body, {"type": "book", "title": "The Catcher in the Rye",
                                    "author": "J.D. Salinger", "page_count": 220})

    def test_create_dvd_with_minutes(self):
        cmd = parse_command("Add a new DVD title Blade Runner author Ridley Scott 117 minutes")
        self.assertEqual(cmd.body, {"type": "dvd", "title": "Blade Runner",
                                    "author": "Ridley Scott", "duration": 117})

    def test_every_endpoint_is_reachable_by_voice(self):
        cases = {
            "List available books.": ("GET", "/api/items?available=true&type=book"),
            "Get item 2.": ("GET", "/api/items/2"),
            "Replace item 2, title Arrival, author Denis Villeneuve, duration 116.": ("PUT", "/api/items/2"),
            "Change item 1 title to Dune Messiah.": ("PATCH", "/api/items/1"),
            "Delete item 3.": ("DELETE", "/api/items/3"),
            "Check out item three.": ("POST", "/api/items/3/checkout"),
            "Return item 3.": ("POST", "/api/items/3/return"),
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                cmd = parse_command(text)
                self.assertEqual((cmd.method, cmd.path), expected)


class VoiceEndpointTests(unittest.TestCase):
    def say(self, client, text):
        return client.post("/api/voice", json={"text": text}).get_json()

    def test_project_examples(self):
        client = app.test_client()
        created = self.say(client, "Create item, type book, title The Catcher in the Rye, "
                                   "author J.D. Salinger, pages 220.")
        new_id = created["response"]["id"]
        self.assertEqual(created["status"], 201)
        self.assertEqual(created["reply"],
                         f"Successfully created book 'The Catcher in the Rye' with ID {new_id}.")

        first = self.say(client, f"Check out item {new_id}")
        self.assertEqual(first["reply"],
                         f"Item {new_id}, 'The Catcher in the Rye', has been checked out.")
        again = self.say(client, f"Check out item {new_id}")
        self.assertEqual(again["status"], 409)
        self.assertEqual(again["reply"], f"Sorry, item {new_id} is already checked out.")

    def test_not_found(self):
        result = self.say(app.test_client(), "Get item 999")
        self.assertEqual(result["status"], 404)
        self.assertEqual(result["reply"], "Sorry, I could not find item 999.")


if __name__ == "__main__":
    unittest.main()
