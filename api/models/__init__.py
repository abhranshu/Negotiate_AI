# Import all models here so that Base.metadata.create_all() picks them up
from api.models.user import User
from api.models.case import Case, Document, Message
