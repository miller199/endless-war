import ewcfg
import ewutils
import ewitem
from ew import EwUser
from ewcasino import check
from ewmarket import EwMarket
from ewitem import EwItem

class EwBook:
    id_book = 0
    id_user = ""
    id_server = ""

    # The name of the book
    title = ""

    # The name of the author
    author = ""

    # If its been published or not
    book_state = 0

    # The in-game day it was published
    date_published = 0

    # The contents of the book
    book_pages = {}

    def __init__(
            self,
            id_book = None
    ):
        if (id_book != None):
            self.id_book = id_book

            self.book_pages = {}

            try:
                conn_info = ewutils.databaseConnect()
                conn = conn_info.get('conn')
                cursor = conn.cursor()

                # Retrieve object
                cursor.execute("SELECT {}, {}, {}, {}, {}, {} FROM books WHERE id_book = %s".format(
                    ewcfg.col_id_server,
                    ewcfg.col_id_user,
                    ewcfg.col_title,
                    ewcfg.col_author,
                    ewcfg.col_book_state,
                    ewcfg.col_date_published,
                ), (
                    self.id_book,
                ))
                result = cursor.fetchone();

                if result != None:
                    # Record found: apply the data to this object.
                    self.id_server = result[0]
                    self.id_user = result[1]
                    self.title = result[2]
                    self.author = result[3]
                    self.book_state = result[4]
                    self.date_published = result[5]

                    # Retrieve additional properties
                    cursor.execute("SELECT {}, {} FROM book_pages WHERE id_book = %s".format(
                        ewcfg.col_page,
                        ewcfg.col_contents
                    ), (
                        self.id_book,
                    ))

                    for row in cursor:
                        # this try catch is only necessary as long as extraneous props exist in the table
                        try:
                            self.book_pages[row[0]] = row[1]
                        except:
                            ewutils.logMsg("extraneous book_pages row detected.")

                else:
                    # Item not found.
                    self.id_book = -1

            finally:
                # Clean up the database handles.
                cursor.close()
                ewutils.databaseClose(conn_info)

    def persist(self):
        try:
            conn_info = ewutils.databaseConnect()
            conn = conn_info.get('conn')
            cursor = conn.cursor()

            # Save the object.
            cursor.execute(
                "REPLACE INTO books({}, {}, {}, {}, {}, {}, {}) VALUES(%s, %s, %s, %s, %s, %s, %s)".format(
                    ewcfg.col_id_book,
                    ewcfg.col_id_server,
                    ewcfg.col_id_user,
                    ewcfg.col_title,
                    ewcfg.col_author,
                    ewcfg.col_book_state,
                    ewcfg.col_date_published,
                ), (
                    self.id_book,
                    self.id_server,
                    self.id_user,
                    self.title,
                    self.author,
                    self.book_state,
                    self.date_published
                ))

            # Remove all existing property rows.
            cursor.execute("DELETE FROM book_pages WHERE {} = %s".format(
                ewcfg.col_id_book
            ), (
                self.id_book,
            ))

            # Write out all current property rows.
            for name in self.book_pages:
                cursor.execute("INSERT INTO book_pages({}, {}, {}) VALUES(%s, %s, %s)".format(
                    ewcfg.col_id_book,
                    ewcfg.col_page,
                    ewcfg.col_contents
                ), (
                    self.id_book,
                    name,
                    self.book_pages[name]
                ))

            conn.commit()
        finally:
            # Clean up the database handles.
            cursor.close()
            ewutils.databaseClose(conn_info)

readers = {}

async def begin_manuscript(cmd):
    user_data = EwUser(member = cmd.message.author)
    boots = ewitem.find_item_all(item_search="oldboot", id_user=user_data.id_user, id_server=user_data.id_server)
    title = cmd.message.content[(len(cmd.tokens[0])):].strip()

    if cmd.message.channel.name not in ["slime-cafe", "nlac-university", "neo-milwaukee-state"]:
        response = "You'd love to begin writing a book, however your current location doesn't strike you as a particularly good place to write. Try heading over the the Cafe or one of the colleges (NLACU/NMS)."

    #elif boots < 3:
    #    response = "You don't have enough boot leather to create a manuscript. ({}/3)".format(boots)

    elif user_data.hunger >= user_data.get_hunger_max() and user_data.life_state != ewcfg.life_state_corpse:
        response = "You are just too hungry to begin writing your masterpiece!"

    elif title == "":
        response = "Specify a title."

    elif len(title) > 24:
        response = "Alright buddy, reel it in. That title is just too long. ({}/24)".format(len(title))

    else:
        if user_data.manuscript != -1:
            response = "You already have a manuscript deployed you eager beaver!"
        else:
            book = EwBook()
            book.id_user = user_data.id_user
            book.id_server = user_data.id_server
            book.author = cmd.message.author.display_name
            book.title = title
            book.book_state = 1
            book.persist()
            user_data.manuscript = book.id_book
            user_data.persist()
            response = "You violently tear apart the old boots, using the laces to tie the torn up leather together in order to create a shoddily-bound manuscript. You scrawl the name \"{} by {}\" into the cover.".format(book.title, book.author)

    await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

async def set_pen_name(cmd):
    user_data = EwUser(member = cmd.message.author)

    if cmd.message.channel.name not in ["slime-cafe", "nlac-university", "neo-milwaukee-state"]:
        response = "You'd love work on your book, however your current location doesn't strike you as a particularly good place to write. Try heading over the the Cafe or one of the colleges (NLACU/NMS)."

    elif user_data.hunger >= user_data.get_hunger_max() and user_data.life_state != ewcfg.life_state_corpse:
        response = "You are just too hungry to alter the pen name of your masterpiece!"

    elif user_data.manuscript == -1:
        response = "You have yet to create a manuscript. Try !createmanuscript"

    else:
        book = EwBook(id_book=user_data.manuscript)
        book.author = cmd.message.author.display_name
        book.persist()
        response = "You scratch out the author name and scrawl \"{}\" under it.".format(book.author)

    await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

async def set_title(cmd):
    user_data = EwUser(member = cmd.message.author)
    title = cmd.message.content[(len(cmd.tokens[0])):].strip()

    if cmd.message.channel.name not in ["slime-cafe", "nlac-university", "neo-milwaukee-state"]:
        response = "You'd love to work on your book, however your current location doesn't strike you as a particularly good place to write. Try heading over the the Cafe or one of the colleges (NLACU/NMS)."

    elif user_data.hunger >= user_data.get_hunger_max() and user_data.life_state != ewcfg.life_state_corpse:
        response = "You are just too hungry to alter the title of your masterpiece!"

    elif user_data.manuscript == -1:
        response = "You have yet to create a manuscript. Try !createmanuscript"

    elif title == "":
        response = "Please specify the title you want to change it to."

    elif len(title) > 24:
        response = "Alright buddy, reel it in. That title is just too long. ({}/24)".format(len(title))

    else:
        book = EwBook(id_book=user_data.manuscript)
        book.title = title
        book.persist()
        response = "You scratch out the title and scrawl \"{}\" over it.".format(book.title)

    await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

async def edit_page(cmd):
    user_data = EwUser(member = cmd.message.author)

    if cmd.tokens_count == 1:
        response = "You must specify a valid page to edit."

    else:
        page = cmd.tokens[1]
        content = cmd.message.content[(len(cmd.tokens[0])+len(cmd.tokens[1])+2):]

        if cmd.message.channel.name not in ["slime-cafe", "nlac-university", "neo-milwaukee-state"]:
            response = "You'd love to work on your book, however your current location doesn't strike you as a particularly good place to write. Try heading over the the Cafe or one of the colleges (NLACU/NMS)."

        elif user_data.hunger >= user_data.get_hunger_max() and user_data.life_state != ewcfg.life_state_corpse:
            response = "You are just too hungry to write your masterpiece!"

        elif user_data.manuscript == -1:
            response = "You have yet to create a manuscript. Try !createmanuscript"

        elif not page.isdigit():
            response = "You must specify a valid page to edit."

        elif int(page) not in range(1, 11):
            response = "You must specify a valid page to edit."

        elif content == "":
            response = "What are you writing down exactly?"

        elif len(content) > 1024:
            response = "Alright buddy, reel it in. That just won't fit on a single page. ({}/1024)".format(len(content))

        else:
            page = int(page)
            book = EwBook(id_book=user_data.manuscript)
            accepted = True
            if book.book_pages.get(page, "") != "":
                accepted = False
                response = "There is already writing on this page. Are you sure you want to overwrite it? **!accept** or **!refuse**"
                await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
                try:
                    message = await cmd.client.wait_for_message(timeout=20, author=cmd.message.author, check=check)

                    if message != None:
                        if message.content.lower() == "!accept":
                            accepted = True
                        if message.content.lower() == "!refuse":
                            accepted = False
                except:
                    accepted = False
            if not accepted:
                response = "The page remains unchanged."
            else:
                book.book_pages[page] = content

                book.persist()
                response = "You spend some time contemplating your ideas before scribbling them onto the page."

    await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

async def view_page(cmd):
    user_data = EwUser(member=cmd.message.author)

    if cmd.tokens_count == 1:
        response = "You must specify a valid page to view."

    else:
        page = cmd.tokens[1]

        if cmd.message.channel.name not in ["slime-cafe", "nlac-university", "neo-milwaukee-state"]:
            response = "You'd love to work on your manuscript, however your current location doesn't strike you as a particularly good place to write. Try heading over the the Cafe or one of the colleges (NLACU/NMS)."

        elif user_data.manuscript == -1:
            response = "You have yet to create a manuscript. Try !createmanuscript"

        elif not page.isdigit():
            response = "You must specify a valid page to view."

        elif int(page) not in range(1,11):
            response = "You must specify a valid page to view."

        else:
            page = int(page)
            book = EwBook(id_book = user_data.manuscript)
            content = book.book_pages.get(page, "")
            if content == "":
                response = "This page is blank. Try !editpage {}.".format(page)
            else:
                response = '"{}"'.format(content)

    await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

async def check_manuscript(cmd):
    user_data = EwUser(member=cmd.message.author)

    if cmd.message.channel.name not in ["slime-cafe", "nlac-university", "neo-milwaukee-state"]:
        response = "You'd love to check on your manuscript, however your current location doesn't strike you as a particularly good place to write. Try heading over the the Cafe or one of the colleges (NLACU/NMS)."

    elif user_data.manuscript == -1:
        response = "You have yet to create a manuscript. Try !createmanuscript"

    else:
        book = EwBook(id_book=user_data.manuscript)
        title = book.title
        author = book.author
        length = 0
        for page in range (1,11):
            length += len(book.book_pages.get(page, ""))

        response = "{} by {}. It is {} characters long.".format(title, author, length)

    await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

async def publish_manuscript(cmd):
    user_data = EwUser(member=cmd.message.author)
    market_data = EwMarket(id_server = user_data.id_server)

    if cmd.message.channel.name not in ["slime-cafe", "nlac-university", "neo-milwaukee-state"]:
        response = "You'd love to publish your manuscript, however your current location doesn't strike you as a particularly good place to write. Try heading over the the Cafe or one of the colleges (NLACU/NMS)."

    elif user_data.manuscript == -1:
        response = "You have yet to create a manuscript. Try !createmanuscript"

    else:
        response = "Are you sure you want to publish your manuscript? This cannot be undone. **!accept** or **!refuse**"
        await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
        try:
            message = await cmd.client.wait_for_message(timeout=20, author=cmd.message.author, check=check)

            if message != None:
                if message.content.lower() == "!accept":
                    accepted = True
                if message.content.lower() == "!refuse":
                    accepted = False
        except:
            accepted = False
        if not accepted:
            response = "The manuscript was not published."
        else:
            book = EwBook(id_book = user_data.manuscript)
            book.book_state = 1
            book.date_published = market_data.day
            user_data.manuscript = -1
            user_data.persist()
            book.persist()
            ewitem.item_create(
                item_type=ewcfg.it_book,
                id_user=user_data.id_user,
                id_server=book.id_server,
                item_props={
                    "title": book.title,
                    "author": book.author,
                    "date_published": book.date_published,
                    "id_book": book.id_book,
                    "book_desc": "A book by {}, published on {}.".format(book.author, book.date_published)
                })
            response = "You've published your manuscript! You can now read it anywhere and distribute it how you deem fit. Use **!reprintbook** to make another copy of it in exchange for a poudrin."

    await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

def get_page(id_book, page):
    book = EwBook(id_book = id_book)
    contents = book.book_pages.get(page, "")
    return contents

async def read_book(cmd):
    user_data = EwUser(member=cmd.message.author)

    if len(cmd.tokens) < 2:
        response = "What book do you want to read?"

    else:
        book_title = cmd.tokens[1]
        if len(cmd.tokens) >= 3:
            page_number = cmd.tokens[2]
            if page_number not in range(1, 11):
                page_number = 1
        else:
            page_number = 1
        book_sought = ewitem.find_item(item_search=book_title, id_user=cmd.message.author.id, id_server=cmd.message.server.id if cmd.message.server is not None else None)
        if book_sought:
            book = EwItem(id_item = book_sought.get('id_item'))
            id_book = book.item_props.get("id_book")
            page_contents = get_page(id_book, page_number)
            response = "You open up to page {} and begin to read.\n\n\"{}\"".format(page_number, page_contents)
            readers[user_data.id_user] = (id_book, page_number)
            if page_contents == "":
                response = "You open up to page {} only to find that it's blank!".format(page_number)
            if page_number != 1:
                response += "\n\nUse **!previouspage** to go back one page."
            if page_number != 10:
                response += "\n\nUse **!nextpage** to go forward one page."
        else:
            response = "You don't have that book. Make sure you use **!read [book title] [page]**"

    await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

async def next_page(cmd):
    user_data = EwUser(member=cmd.message.author)

    if user_data.id_user in readers.keys():
        id_book = readers[user_data.id_user][0]
        page_number = readers[user_data.id_user][1]
        if page_number == 10:
            response = "You've reached the end of the book."
        else:
            page_number += 1
            page_contents = get_page(id_book, page_number)
            response = "You turn to page {} and begin to read.\n\n\"{}\"".format(page_number, page_contents)
            readers[user_data.id_user] = (id_book, page_number)
            if page_contents == "":
                response = "You open up to page {} only to find that it's blank!".format(page_number)
            if page_number != 1:
                response += "\n\nUse **!previouspage** to go back one page."
            if page_number != 10:
                response += "\n\nUse **!nextpage** to go forward one page."
    else:
        response = "You haven't opened a book yet!"

    await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))


async def previous_page(cmd):
    user_data = EwUser(member=cmd.message.author)

    if user_data.id_user in readers.keys():
        id_book = readers[user_data.id_user][0]
        page_number = readers[user_data.id_user][1]
        if page_number == 1:
            response = "You've reached the start of the book."
        else:
            page_number -= 1
            page_contents = get_page(id_book, page_number)
            response = "You turn to page {} and begin to read.\n\n\"{}\"".format(page_number, page_contents)
            readers[user_data.id_user] = (id_book, page_number)
            if page_contents == "":
                response = "You open up to page {} only to find that it's blank!".format(page_number)
            if page_number != 1:
                response += "\n\nUse **!previouspage** to go back one page."
            if page_number != 10:
                response += "\n\nUse **!nextpage** to go forward one page."
    else:
        response = "You haven't opened a book yet!"

    await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))