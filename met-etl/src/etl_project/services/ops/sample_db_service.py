from dagster import Out, Output, op
from met_api.models.user import User as MetUserModel
from datetime import datetime


@op(required_resource_keys={"met_db_session"}, out={"newusers": Out(is_required=True)})
def run_sample_db_test(context):
    """Verify Connect DB."""
    met_db_session = context.resources.met_db_session
    default_datetime = datetime(1900, 1, 1, 15, 59, 56, 721228)
    new_users = met_db_session.query(MetUserModel).filter(MetUserModel.created_date > default_datetime).all()
    context.log.info(new_users)
    yield Output(new_users, "newusers")