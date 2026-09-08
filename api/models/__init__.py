# Import all models here so that Base.metadata picks them up.
# Also used by Alembic (via migrations/env.py) for autogenerate support.

import sys, os
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from api.models.user import User
from api.models.case import Case, Document, Message, CaseStatus, DisputeType

