import neomodel


def test_basic_db_write(clear_db):
    from test_app.models import Person

    p = Person(name="John Smith")
    p.save()

    assert Person.nodes.all()[0] == p


def test_add_relation(clear_db):
    from test_app.models import Person, Pet

    person = Person(name="John Smith")
    person.save()

    pet = Pet(name="Tiny")
    pet.save()

    person.owns_pets.connect(pet, {"purchased_when": "yesterday"})

    assert person.owns_pets.all()[0] == pet


def test_build_read_query(clear_db):
    from pros_core.query_utils.query_builders import build_read_query
    from pros_core.setup_app import ModelManager
    from test_app.models import Book, Calendar, DatePrecise, Person, Pet

    with neomodel.db.write_transaction:
        p = Person(name="John Smith")
        p.save()
        d = DatePrecise(date="1 March 2023")
        d.save()
        p.date_of_birth.connect(d)
        c = Calendar()
        c.save()
        d.calendar_format.connect(c)
        c2 = Calendar(type="Gregorian")
        c2.save()
        d.calendar_format.connect(c2)
        pet = Pet(name="Wuffles")
        pet.save()
        p.owns_pets.connect(pet, {"purchased_when": "Yesterday"})
        b = Book(label="Tales of the Mysterious Database")
        b.save()
        p.has_books.connect(b)

    read_query = build_read_query(Person)

    response = read_query("self", p.uid)
    print(response)

    assert response["uid"] == Person.nodes.all()[0].uid
    assert response["real_type"] == "Person"
    assert response["date_of_birth"][0]["date"] == "1 March 2023"

    # As date has multiple formats for some reason (test purposes!), can't be sure
    # which order we'll get them back in; so check length and then turn types into a set so we can compare
    assert len(response["date_of_birth"][0]["calendar_format"]) == 2
    calendar_formats = {
        calendar["type"] for calendar in response["date_of_birth"][0]["calendar_format"]
    }
    assert calendar_formats == {"Julian", "Gregorian"}

    # Now test we can unpack pets
    assert response["owns_pets"][0]["name"] == "Wuffles"
    assert (
        response["owns_pets"][0]["_relationship_data"]["purchased_when"] == "Yesterday"
    )
    assert response["has_books"][0]["label"] == "Tales of the Mysterious Database"

    book_read_query = build_read_query(Book)
    response = book_read_query("self", b.uid)
    assert response["real_type"] == "Book"
    assert response["label"] == "Tales of the Mysterious Database"
    assert response["belongs_to_person"][0]["name"] == "John Smith"
