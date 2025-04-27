from datetime import datetime

import pytz

from ip_files.get_timezone import get_timezone
from models import User
from flask_login import current_user


def set_offset():
    user = User.query.get(current_user.id)
    ip = user.ip_address
    timezone_str = get_timezone(ip)
    if not timezone_str:
        print("Не удалось определить временную зону")
    try:
        tz = pytz.timezone(timezone_str)
        offset = datetime.now(tz).utcoffset().total_seconds() / 3600
        return offset
    except pytz.UnknownTimeZoneError:
        print(f"Неизвестная временная зона: {timezone_str}")
        print('Установили по гринвичу')
    except Exception as e:
        print(f"Ошибка: {e}")
    return 0
