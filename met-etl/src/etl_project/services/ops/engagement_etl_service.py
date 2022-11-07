from dagster import Out, Output, op
from met_api.models import EngagementStatus
from met_api.models.engagement import Engagement as MetEngagementModel
from met_cron.models.engagement import Engagement as EtlEngagementModel
from sqlalchemy import func
from datetime import datetime
from met_cron.models.etlruncycle import EtlRunCycle as EtlRunCycleModel


# get the last run cycle id for user detail etl
@op(required_resource_keys={"met_db_session", "met_etl_db_session"},
    out={"engagement_last_run_cycle_datetime": Out(), "engagement_new_run_cycle_id": Out()})
def get_engagement_last_run_cycle_time(context):
    met_etl_db_session = context.resources.met_etl_db_session
    default_datetime = datetime(1900, 1, 1, 0, 0, 0, 0)

    engagement_last_run_cycle_datetime = met_etl_db_session.query(
        func.coalesce(func.max(EtlRunCycleModel.enddatetime), default_datetime)).filter(
        EtlRunCycleModel.packagename == 'engagement', EtlRunCycleModel.success == True).first()

    max_run_cycle_id = met_etl_db_session.query(func.coalesce(func.max(EtlRunCycleModel.id), 0)).first()

    for last_run_cycle_time in engagement_last_run_cycle_datetime:

        for run_cycle_id in max_run_cycle_id:
            new_run_cycle_id = run_cycle_id + 1
            met_etl_db_session.add(
                EtlRunCycleModel(id=new_run_cycle_id, packagename='engagement', startdatetime=datetime.utcnow(),
                                 enddatetime=None, description='started the load for table engagement',
                                 success=False))
            met_etl_db_session.commit()

    met_etl_db_session.close()

    yield Output(engagement_last_run_cycle_datetime, "engagement_last_run_cycle_datetime")

    yield Output(new_run_cycle_id, "engagement_new_run_cycle_id")


# extract the surveys that have been created or updated after the last run
@op(required_resource_keys={"met_db_session", "met_etl_db_session"},
    out={"updated_engagements": Out(), "eng_new_runcycleid": Out()})
def extract_engagement(context, eng_last_run_cycle_time, eng_new_runcycleid):
    session = context.resources.met_db_session
    updated_engagements = []

    for last_run_cycle_time in eng_last_run_cycle_time:
        context.log.info("started extracting new data from engagement table")
        updated_engagements = session.query(MetEngagementModel).filter(
            MetEngagementModel.updated_date > last_run_cycle_time,
            MetEngagementModel.status_id != EngagementStatus.Draft.value).all()

    yield Output(updated_engagements, "updated_engagements")

    yield Output(eng_new_runcycleid, "eng_new_runcycleid")

    context.log.info("completed extracting data from engagement table")

    session.commit()

    session.close()


# load the surveys created or updated after last run to the analytics database
@op(required_resource_keys={"met_db_session", "met_etl_db_session"}, out={"engagement_new_runcycleid": Out()})
def load_engagement(context, updated_engagements, engagement_new_runcycleid):
    session = context.resources.met_etl_db_session
    if len(updated_engagements) > 0:

        context.log.info("loading new inputs")
        for engagement in updated_engagements:
            engagement_model = EtlEngagementModel(name=engagement.name,
                                                  source_engagement_id=engagement.id,
                                                  start_date=engagement.start_date,
                                                  end_date=engagement.end_date,
                                                  is_active=True,
                                                  published_date=engagement.published_date,
                                                  runcycle_id=1,
                                                  created_date=engagement.created_date,
                                                  updated_date=engagement.updated_date
                                                  )
            session.add(engagement_model)
            session.commit()

    yield Output(engagement_new_runcycleid, "engagement_new_runcycleid")

    context.log.info("completed loading engagement table")

    session.close()
