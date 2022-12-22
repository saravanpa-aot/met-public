"""Engagement model class.

Manages the engagement
"""

from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from sqlalchemy import asc, desc
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.sql import text
from sqlalchemy.sql.schema import ForeignKey
from met_api.constants.engagement_status import Status, SubmissionStatus
from met_api.constants.user import SYSTEM_USER
from met_api.models.pagination_options import PaginationOptions
from met_api.schemas.engagement import EngagementSchema
from met_api.utils.datetime import local_datetime
from .base_model import BaseModel
from .db import db
from .default_method_result import DefaultMethodResult
from .engagement_status import EngagementStatus


class EngagementStatusBlock(BaseModel):
    """Definition of the Engagement status block entity."""

    __tablename__ = 'engagement_status_block'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    engagement_id = db.Column(db.Integer, ForeignKey('engagement.id', ondelete='CASCADE'))
    survey_status = db.Column(db.Enum(SubmissionStatus), nullable=False)
    block_text = db.Column(JSON, unique=False, nullable=False)

