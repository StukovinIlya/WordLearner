from werkzeug.security import generate_password_hash


def set_password(password):
    password_hash = generate_password_hash(password)
    return password_hash
