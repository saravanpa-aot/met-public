# Copyright © 2021 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""API endpoints for managing an comment resource."""

from http import HTTPStatus

from flask import Response, request
from flask_cors import cross_origin
from flask_restx import Namespace, Resource

from met_api.auth import auth
from met_api.auth import jwt as _jwt
from met_api.models.pagination_options import PaginationOptions
from met_api.services.comment_service import CommentService
from met_api.utils.util import allowedorigins, cors_preflight


API = Namespace('comments', description='Endpoints for Comments Management')
"""Custom exception messages
"""


@cors_preflight('GET, OPTIONS')
@API.route('/survey/<survey_id>')
class SurveyComments(Resource):
    """Resource for managing multiple comments."""

    @staticmethod
    @cross_origin(origins=allowedorigins())
    @auth.optional
    def get(survey_id):
        """Get comments page."""
        try:
            args = request.args

            pagination_options = PaginationOptions(
                page=args.get('page', None, int),
                size=args.get('size', None, int),
                sort_key=args.get('sort_key', 'name', str),
                sort_order=args.get('sort_order', 'asc', str),
            )
            comment_records = CommentService()\
                .get_comments_paginated(
                    survey_id,
                    pagination_options,
                    args.get('search_text', '', str),
            )
            return comment_records, HTTPStatus.OK
        except ValueError as err:
            return str(err), HTTPStatus.INTERNAL_SERVER_ERROR


@cors_preflight('GET, OPTIONS')
@API.route('/survey/<survey_id>/sheet/staff')
class GeneratedStaffCommentsSheet(Resource):
    """Resource for managing multiple comments."""

    @staticmethod
    @cross_origin(origins=allowedorigins())
    @_jwt.requires_auth
    def get(survey_id):
        """Export comments."""
        try:

            response = CommentService().export_comments_to_spread_sheet_staff(survey_id)
            response_headers = dict(response.headers)
            headers = {
                'content-type': response_headers.get('content-type'),
                'content-disposition': response_headers.get('content-disposition'),
            }
            return Response(
                response=response.content,
                status=response.status_code,
                headers=headers
            )
        except ValueError as err:
            return str(err), HTTPStatus.INTERNAL_SERVER_ERROR


@cors_preflight('GET, OPTIONS')
@API.route('/survey/<survey_id>/sheet/proponent')
class GeneratedProponentCommentsSheet(Resource):
    """Resource for managing multiple comments."""

    @staticmethod
    @cross_origin(origins=allowedorigins())
    @_jwt.requires_auth
    def get(survey_id):
        """Export comments."""
        try:

            response = CommentService().export_comments_to_spread_sheet_proponent(survey_id)
            response_headers = dict(response.headers)
            headers = {
                'content-type': response_headers.get('content-type'),
                'content-disposition': response_headers.get('content-disposition'),
            }
            return Response(
                response=response.content,
                status=response.status_code,
                headers=headers
            )
        except ValueError as err:
            return str(err), HTTPStatus.INTERNAL_SERVER_ERROR
