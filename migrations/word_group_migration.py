from models import WordGroup, db, User


def migrate_word_groups():
    guest = User.query.filter_by(username='Guest').one()
    english = WordGroup(
        name="English",
        user_id=guest.id,
    )
    db.session.add(english)
    db.session.add(
        WordGroup(
            name="Food",
            user_id=guest.id,
            parent_group_id=english.id,
        )
    )
    db.session.add(
        WordGroup(
            name="Technology",
            user_id=guest.id,
            parent_group_id=english.id,
        )
    )
    db.session.add(
        WordGroup(
            name="Chemistry",
            user_id=guest.id,
        )
    )
    db.session.commit()
