"""Service for Email Verification management."""
import uuid
from datetime import datetime, timedelta
from http import HTTPStatus

from flask import current_app
from met_api.constants.email_verification import INTERNAL_EMAIL_DOMAIN, EmailVerificationType

from met_api.constants.subscription_type import SubscriptionTypes
from met_api.exceptions.business_exception import BusinessException
from met_api.models import Engagement as EngagementModel
from met_api.models import EngagementSlug as EngagementSlugModel
from met_api.models import Survey as SurveyModel
from met_api.models import Tenant as TenantModel
from met_api.models.email_verification import EmailVerification
from met_api.models.engagement_metadata import EngagementMetadataModel
from met_api.schemas.email_verification import EmailVerificationSchema
from met_api.services.participant_service import ParticipantService
from met_api.utils import notification
from met_api.utils.template import Template
from met_api.config import get_gc_notify_config


class EmailVerificationService:
    """Email Verification management service."""

    verification_expiry_hours = 24
    datetime_format = '%Y-%m-%d %H:%M:%S.%f'
    full_date_format = ' %B %d, %Y'
    date_format = '%Y-%m-%d'

    @classmethod
    def get(cls, verification_token):
        """Get an active email verification matching the provided token."""
        db_email_verification = EmailVerification.get(verification_token)
        return EmailVerificationSchema().dump(db_email_verification)

    @classmethod
    def get_active(cls, verification_token):
        """Get an active email verification matching the provided token."""
        db_email_verification = EmailVerification.get(verification_token)
        email_verification = EmailVerificationSchema().dump(db_email_verification)
        cls.validate_email_verification(email_verification)
        return email_verification

    @classmethod
    def create(cls, email_verification: EmailVerificationSchema,
               subscription_type='', session=None) -> EmailVerificationSchema:
        """Create an email verification."""
        cls.validate_fields(email_verification)
        email_address: str = email_verification.get('email_address')
        survey = SurveyModel.find_by_id(email_verification.get('survey_id'))
        engagement: EngagementModel = EngagementModel.find_by_id(
            survey.engagement_id)
        if engagement.is_internal and not email_address.endswith(INTERNAL_EMAIL_DOMAIN):
            raise BusinessException(
                error='Not an internal email address.',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR)

        if email_address is not None:
            participant = ParticipantService.get_or_create_by_email(
                email_address)
            email_verification['participant_id'] = participant.id

        email_verification['created_by'] = email_verification.get(
            'participant_id')
        email_verification['verification_token'] = uuid.uuid4()
        EmailVerification.create(email_verification, session)

        # TODO: remove this once email logic is brought over from submission service to here
        if email_verification.get('type', None) != EmailVerificationType.RejectedComment:
            cls._send_verification_email(email_verification, subscription_type)

        return email_verification

    @classmethod
    def verify(cls, verification_token, survey_id, submission_id, session):
        """Validate and update an email verification."""
        db_email_verification = EmailVerification.get(verification_token)
        email_verification = EmailVerificationSchema().dump(db_email_verification)
        cls.validate_email_verification(email_verification)

        verification_type = email_verification.get('type', None)

        if verification_type == EmailVerificationType.Survey and\
           email_verification.get('survey_id', None) != survey_id:
            raise ValueError('Email verification invalid for survey')

        if verification_type == EmailVerificationType.RejectedComment and\
           email_verification.get('submission_id', None) != submission_id:
            raise ValueError('Email verification invalid for submission')

        email_verification['updated_by'] = email_verification['participant_id']
        email_verification['is_active'] = False
        EmailVerification.update(email_verification, session)
        return email_verification

    @staticmethod
    def _send_verification_email(email_verification: dict, subscription_type) -> None:
        """Send an verification email.Throws error if fails."""
        survey_id = email_verification.get('survey_id')
        email_to = email_verification.get('email_address')
        survey: SurveyModel = SurveyModel.find_by_id(survey_id)

        if not survey:
            raise ValueError('Survey not found')
        if not survey.engagement_id:
            raise ValueError('Engagement not found')

        subject, body, args, template_id = EmailVerificationService._render_email_template(
            survey,
            email_verification.get('verification_token'),
            email_verification.get('type'),
            subscription_type
        )
        try:
            # user hasn't been created yet.so create token using SA.
            notification.send_email(
                subject=subject, email=email_to, html_body=body, args=args, template_id=template_id)
        except Exception as exc:  # noqa: B902
            current_app.logger.error(
                '<Notification for registration failed', exc)
            raise BusinessException(
                error='Error sending verification email.',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR) from exc

    @staticmethod
    def _render_email_template(survey: SurveyModel,
                               token,
                               email_type: EmailVerificationType,
                               subscription_type):
        if email_type == EmailVerificationType.Subscribe:
            return EmailVerificationService._render_subscribe_email_template(survey, token, subscription_type)
        # if email_type == EmailVerificationType.RejectedComment:
            # TODO: move reject comment email verification logic here
        #    return
        return EmailVerificationService._render_survey_email_template(survey, token)

    @staticmethod
    # pylint: disable-msg=too-many-locals
    def _render_subscribe_email_template(survey: SurveyModel, token, subscription_type):
        # url is origin url excluding context path
        engagement: EngagementModel = EngagementModel.find_by_id(
            survey.engagement_id)
        tenant_name = EmailVerificationService._get_tenant_name(
            engagement.tenant_id)
        project_name = EmailVerificationService._get_project_name(
            subscription_type, tenant_name, engagement)
        is_subscribing_to_tenant = subscription_type == SubscriptionTypes.TENANT.value
        is_subscribing_to_project = subscription_type != SubscriptionTypes.TENANT.value
        template_id = get_gc_notify_config('SUBSCRIBE_EMAIL_TEMPLATE_ID')
        template = Template.get_template('subscribe_email.html')
        confirm_path = current_app.config.get('SUBSCRIBE_PATH'). \
            format(engagement_id=engagement.id, token=token)
        confirm_url = notification.get_tenant_site_url(
            engagement.tenant_id, confirm_path)
        email_environment = get_gc_notify_config('EMAIL_ENVIRONMENT')
        args = {
            'project_name': project_name,
            'confirm_url': confirm_url,
            'email_environment': email_environment,
            'tenant_name': tenant_name,
            'is_subscribing_to_tenant': is_subscribing_to_tenant,
            'is_subscribing_to_project': is_subscribing_to_project,
        }
        subject = get_gc_notify_config('SUBSCRIBE_EMAIL_SUBJECT')
        body = template.render(
            project_name=args.get('project_name'),
            confirm_url=args.get('confirm_url'),
            email_environment=args.get('email_environment'),
            tenant_name=args.get('tenant_name'),
            is_subscribing_to_tenant=args.get('is_subscribing_to_tenant'),
            is_subscribing_to_project=args.get('is_subscribing_to_project'),
        )
        return subject, body, args, template_id

    @staticmethod
    def _render_survey_email_template(survey: SurveyModel, token):
        # url is origin url excluding context path
        engagement: EngagementModel = EngagementModel.find_by_id(
            survey.engagement_id)
        engagement_name = engagement.name
        template_id = get_gc_notify_config('VERIFICATION_EMAIL_TEMPLATE_ID')
        email_environment = get_gc_notify_config('EMAIL_ENVIRONMENT')
        template = Template.get_template('email_verification.html')
        subject_template = get_gc_notify_config('VERIFICATION_EMAIL_SUBJECT')
        survey_path = current_app.config.get('SURVEY_PATH'). \
            format(survey_id=survey.id, token=token)
        engagement_path = EmailVerificationService.get_engagement_path(
            engagement)
        site_url = notification.get_tenant_site_url(engagement.tenant_id)
        tenant_name = EmailVerificationService._get_tenant_name(
            engagement.tenant_id)
        args = {
            'engagement_name': engagement_name,
            'survey_url': f'{site_url}{survey_path}',
            'engagement_url': f'{site_url}{engagement_path}',
            'tenant_name': tenant_name,
            'end_date': datetime.strftime(engagement.end_date, EmailVerificationService.full_date_format),
            'email_environment': email_environment,
        }
        subject = subject_template.format(engagement_name=engagement_name)
        body = template.render(
            engagement_name=args.get('engagement_name'),
            survey_url=args.get('survey_url'),
            engagement_url=args.get('engagement_url'),
            tenant_name=args.get('tenant_name'),
            end_date=args.get('end_date'),
            email_environment=args.get('email_environment'),
        )
        return subject, body, args, template_id

    @staticmethod
    def get_engagement_path(engagement: EngagementModel):
        """Get an engagement path."""
        engagement_slug = EngagementSlugModel.find_by_engagement_id(
            engagement.id)
        if engagement_slug:
            return current_app.config.get('ENGAGEMENT_PATH_SLUG'). \
                format(slug=engagement_slug.slug)
        return current_app.config.get('ENGAGEMENT_PATH'). \
            format(engagement_id=engagement.id)

    @staticmethod
    def _get_tenant_name(tenant_id):
        tenant = TenantModel.find_by_id(tenant_id)
        return tenant.name

    @staticmethod
    def _get_project_name(subscription_type, tenant_name, engagement):
        metadata_model: EngagementMetadataModel = EngagementMetadataModel.find_by_id(engagement.id)
        if subscription_type == SubscriptionTypes.TENANT.value:
            return tenant_name

        if subscription_type == SubscriptionTypes.PROJECT.value:
            metadata_model: EngagementMetadataModel = EngagementMetadataModel.find_by_id(engagement.id)
            project_name = metadata_model.project_metadata.get('project_name', None)
            return project_name or engagement.name

        if subscription_type == SubscriptionTypes.ENGAGEMENT.value:
            return engagement.name

        return None

    @staticmethod
    def validate_email_verification(email_verification: EmailVerificationSchema):
        """Validate an email verification."""
        if email_verification.get('id', None) is None:
            raise ValueError('Email verification not found')

        is_active = email_verification.get('is_active')
        if not is_active:
            raise ValueError('Email verification already verified')

        if email_verification.get('type') == EmailVerificationType.Subscribe:
            return

        if email_verification.get('type') == EmailVerificationType.Survey:
            # New email verification expires in 24 hours
            verification_created_datetime = datetime.strptime(
                email_verification.get('created_date'), EmailVerificationService.datetime_format)
            verification_expiry_datetime = verification_created_datetime + \
                timedelta(
                    hours=EmailVerificationService.verification_expiry_hours)
            if datetime.now() >= verification_expiry_datetime:
                raise ValueError('Email verification is expired')

        survey_id = email_verification.get('survey_id')
        survey: SurveyModel = SurveyModel.get_open(survey_id)
        if not survey:
            raise ValueError('Engagement period is over')

    @staticmethod
    def validate_fields(data: EmailVerificationSchema):
        """Validate all required fields."""
        empty_fields = [not data[field] for field in [
            'survey_id'
        ]]

        if any(empty_fields):
            raise ValueError('Some required fields are empty')
