"""Database models"""
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Import all models here for Alembic autogenerate
from hyperagent.models.user import User
from hyperagent.models.workflow import Workflow
from hyperagent.models.contract import GeneratedContract
from hyperagent.models.audit import SecurityAudit
from hyperagent.models.deployment import Deployment
from hyperagent.models.template import ContractTemplate

