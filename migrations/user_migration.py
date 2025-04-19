from models import User, db


def migrate_users():
    session = db.create_session()
    session.add(
        User(
            username='Guest',
            email='demo@gmail.com',
            theme='light',
        )
        .set_password("123")
    )
    session.add(
        User(
            username='Ilya',
            email='ilya@mail.ru',
            theme='light',
        )
        .set_password("123")
    )
    session.add(
        User(
            username='Andrey',
            email='andrey@mail.ru',
            theme='dark',
        )
        .set_password("123")
    )
    session.add(
        User(
            username='Danyil',
            email='danyil@gmail.com',
            theme='light',
        )
        .set_password("123")
    )

    session.commit()
