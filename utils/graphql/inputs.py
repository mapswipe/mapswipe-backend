import datetime

import strawberry


@strawberry.input
class DateRangeInput:
    from_date: datetime.date
    to_date: datetime.date
