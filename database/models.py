from peewee import Model, SqliteDatabase, CharField, DateTimeField, TextField, FloatField
from datetime import datetime

db = SqliteDatabase('history.db')

class BaseModel(Model):
    class Meta:
        database = db

class HotelSearchHistory(BaseModel):
    date = DateTimeField(default=datetime.now)
    user_id = CharField()  # store as string for simplicity
    city = CharField()
    hotel_name = CharField()
    link = CharField()
    description = TextField(null=True)
    price = FloatField(null=True)
    checkin = CharField(null=True)
    checkout = CharField(null=True)
    photos = TextField(null=True)  # comma separated URLs
    latitude = CharField(null=True)
    longitude = CharField(null=True)

db.connect(reuse_if_open=True)
db.create_tables([HotelSearchHistory])
