from models import db, Word, WordGroup


def migrate_words():
    english_food = WordGroup.query.filter_by(name="Food").one()
    english_technology = WordGroup.query.filter_by(name="Technology").one()
    chemistry = WordGroup.query.filter_by(name="Chemistry").one()

    db.session.add(
        Word(
            original="apple",
            translation="яблоко",
            group_id=english_food.id,
            difficulty=1,
        )
    )

    db.session.add(
        Word(
            original="car",
            translation="машина",
            group_id=english_technology.id,
            difficulty=1,
        )
    )

    db.session.add(
        Word(
        original="water's formula",
            translation="H2O",
            group_id=chemistry.id,
            difficulty=1,
        )
    )

    db.session.commit()
