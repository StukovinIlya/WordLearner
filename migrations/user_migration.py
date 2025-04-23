from models import User, db


def migrate_users():
    db.session.add(
        User(
            username='Guest',
            email='demo@gmail.com',
            theme='light',
        )
        .set_password("123")
    )
    db.session.add(
        User(
            username='Ilya',
            email='ilya@mail.ru',
            theme='light',
        )
        .set_password("123")
    )
    db.session.add(
        User(
            username='Andrey',
            email='andrey@mail.ru',
            theme='dark',
        )
        .set_password("123")
    )
    db.session.add(
        User(
            username='Danyil',
            email='danyil@gmail.com',
            theme='light',
        )
        .set_password("123")
    )

    db.session.commit()
