# PROMPTS.md – Section 2 (Library App)

AI tool used: Claude (claude.ai chat). Prompts are paraphrased in English; the
conversation was in Turkish.

## Main prompts

1. **Part 2 – classes.** *"Here is my Week 3 custom_classes.py and main.py. Extend them for Week 4:
   add ItemNotFoundError and ItemStateError; give every item a unique integer id assigned by
   LibraryCollection.add_item() (1, 2, 3 … never reused); add to_dict() to MediaItem and override
   it in Book/DVD; make checkout()/return_item() raise ItemStateError instead of returning
   'Already out'; DVD.checkout() must not print, return the reminder in the message; add
   get_item, list_items(available=None, item_type=None), update_item(item_id, **fields) and
   remove_item to LibraryCollection. In main.py call every method once and trigger every
   exception inside try/except."*

2. **Part 3 – REST API.** *"Write library/app.py with Flask. One LibraryCollection seeded with
   3 mixed items. Expose POST/GET /api/items (with ?available= and ?type= filters),
   GET/PUT/PATCH/DELETE /api/items/<id>, POST /api/items/<id>/checkout and /return. Use exactly
   these status codes: 201 create, 204 delete, 400 bad input / bad filter, 404 unknown id,
   409 state conflicts. Every error is {"error": "<message>"}. The routes must only translate
   HTTP to method calls – all rules stay in custom_classes.py. Also requirements.txt."*

3. **Part 4 – frontend.** *"Turn my Figma library design into index.html / style.css / script.js
   served by Flask at http://127.0.0.1:5000. Item list with title, author, type chip, pages or
   minutes, availability badge, Checkout/Return button, edit and delete icons; Add/Edit form
   whose last field switches between Page count and Duration; 'Available only' toggle and
   All/Book/DVD filter; empty state; and an error area that shows the API's error messages
   (e.g. the 409 when deleting a checked-out item). Every action must go through the API;
   do not duplicate any rule in JavaScript."*

## Things the AI got wrong that I fixed

1. **HTML validation hid the API's 400 errors.** The first version of `index.html` had
   `required` and `min="1"` on the form inputs. The browser blocked the submit before the
   request reached Flask, so the server's messages ("page_count must be a positive integer",
   "title must be a non-empty string") never appeared in the error area – the input rules were
   effectively duplicated on the client, which the exercise explicitly warns against. I removed
   the attributes; the server is now the single place where input rules live and its 400
   message is shown in the error area. (Found while testing: submitting page_count = 0 showed
   nothing instead of the API error.)

2. **Badge text wrapped onto two lines.** In the generated CSS the "Checked out" badge broke
   into two lines inside the row, which did not match the Figma design. Added
   `white-space: nowrap` to `.badge`.

Everything else (status codes, PUT vs PATCH behaviour, 204 handling in the fetch helper,
type not editable in edit mode) was checked against the endpoint table with Thunder Client
and worked as generated.
