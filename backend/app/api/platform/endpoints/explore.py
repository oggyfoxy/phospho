import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from loguru import logger
from propelauth_fastapi import User

from app.api.platform.models import (
    ABTests,
    AggregateMetricsRequest,
    Cluster,
    Clusterings,
    Clusters,
    DashboardMetricsFilter,
    DetectClustersRequest,
    Events,
    FetchClustersRequest,
    ProjectDataFilters,
    ClusteringRequest,
)
from app.core import config
from app.security import verify_if_propelauth_user_can_access_project
from app.security.authentification import propelauth
from app.security.authorization import get_quota
from app.services.mongo.ai_hub import clustering
from app.services.mongo.events import get_event_definition_from_event_id
from app.services.mongo.explore import (
    compute_nb_items_with_metadata_field,
    compute_session_length_per_metadata,
    compute_successrate_metadata_quantiles,
    create_ab_tests_table,
    deprecated_get_dashboard_aggregated_metrics,
    fetch_all_clusterings,
    fetch_all_clusters,
    fetch_single_cluster,
    get_dashboard_aggregated_metrics,
    get_events_aggregated_metrics,
    get_sessions_aggregated_metrics,
    get_tasks_aggregated_metrics,
    nb_items_with_a_metadata_field,
    project_has_enough_labelled_tasks,
    project_has_sessions,
    project_has_tasks,
)
from app.services.mongo.extractor import bill_on_stripe
from app.services.mongo.events import get_all_events
from app.services.mongo.tasks import get_total_nb_of_tasks

router = APIRouter(tags=["Explore"])


@router.post(
    "/explore/{project_id}/has-tasks",
    description="Check if a project has tasks. Used to nudge the user to create tasks.",
)
async def post_project_has_tasks(
    project_id: str,
    user: User = Depends(propelauth.require_user),
) -> dict:
    """
    Check if a project has tasks. If not, display a tutorial to the user.
    Should be super fast.
    """
    if not project_id:
        raise HTTPException(
            status_code=400,
            detail="Missing project_id in request.",
        )
    await verify_if_propelauth_user_can_access_project(user, project_id)
    has_tasks = await project_has_tasks(project_id=project_id)
    if not has_tasks:
        logger.info(f"Project {project_id} has no tasks (user: {user.email})")
    return {"has_tasks": has_tasks}


@router.post(
    "/explore/{project_id}/has-sessions",
    description="Check if a project has sessions. Used to nudge the user to create sessions.",
)
async def post_project_has_sessions(
    project_id: str,
    user: User = Depends(propelauth.require_user),
) -> dict:
    """
    Check if a project has sessions. If not, display a tutorial to the user.
    Should be super fast.
    """
    if not project_id:
        raise HTTPException(
            status_code=400,
            detail="Missing project_id in request.",
        )
    await verify_if_propelauth_user_can_access_project(user, project_id)
    has_sessions = await project_has_sessions(project_id=project_id)
    if not has_sessions:
        logger.info(f"Project {project_id} has no sessions (user: {user.email})")
    return {"has_sessions": has_sessions}


@router.post(
    "/explore/{project_id}/has-enough-labelled-tasks",
    description="Check if a project has labelled tasks. Used to nudge the user to label tasks.",
)
async def post_project_has_enough_labelled_tasks(
    project_id: str,
    user: User = Depends(propelauth.require_user),
) -> dict:
    """
    Check if a project has labelled tasks. If not, display a tutorial to the user.
    Should be super fast.
    """
    if not project_id:
        raise HTTPException(
            status_code=400,
            detail="Missing project_id in request.",
        )
    await verify_if_propelauth_user_can_access_project(user, project_id)
    # The number of labelled tasks to consider the project as having enough labelled tasks
    enough = config.FEW_SHOT_MIN_NUMBER_OF_EXAMPLES
    currently_labelled_tasks = await project_has_enough_labelled_tasks(
        project_id=project_id, enough=enough
    )
    logger.info(
        f"Project {project_id} has {currently_labelled_tasks}/{enough} labelled tasks (user: {user.email})"
    )
    return {
        "project_id": project_id,
        "enough_labelled_tasks": enough,
        "has_enough_labelled_tasks": bool(currently_labelled_tasks >= enough),
        "currently_labelled_tasks": currently_labelled_tasks,
    }


@router.post(
    "/explore/{project_id}/aggregated",
    description="Get aggregated metrics for a project. Used for the main dashboard.",
)
async def get_dashboard_project_metrics(
    project_id: str,
    request: AggregateMetricsRequest,
    user: User = Depends(propelauth.require_user),
) -> List[dict]:
    """
    Get aggregated metrics for a project. Used for dashboard.
    """
    logger.info(f"Dashboard request: {request.model_dump()}")
    await verify_if_propelauth_user_can_access_project(user, project_id)

    output = await deprecated_get_dashboard_aggregated_metrics(
        project_id=project_id,
        limit=request.limit,
        index=request.index,
        columns=request.columns,
        count_of=request.count_of,
        timerange=request.timerange,
        filters=request.filters,
    )
    return output


@router.post(
    "/explore/{project_id}/aggregated/tasks",
    description="Get aggregated metrics for the tasks of a project. Used for the Tasks dashboard.",
)
async def get_tasks_project_metrics(
    project_id: str,
    metrics: Optional[List[str]] = None,
    filters: Optional[ProjectDataFilters] = None,
    user: User = Depends(propelauth.require_user),
) -> dict:
    """
    Get aggregated metrics for the tasks of a project. Used for the Tasks dashboard.
    """
    await verify_if_propelauth_user_can_access_project(user, project_id)
    if filters is None:
        filters = ProjectDataFilters(flag=None, event_name=None)
    if isinstance(filters.event_name, str):
        filters.event_name = [filters.event_name]
    # Convert to UNIX timestamp in seconds
    if isinstance(filters.created_at_start, datetime.datetime):
        filters.created_at_start = int(filters.created_at_start.timestamp())
    if isinstance(filters.created_at_end, datetime.datetime):
        filters.created_at_end = int(filters.created_at_end.timestamp())

    output = await get_tasks_aggregated_metrics(
        project_id=project_id,
        metrics=metrics,
        filters=filters,
    )
    return output


@router.post(
    "/explore/{project_id}/aggregated/sessions",
    description="Get aggregated metrics for the sessions of a project. Used for the Sessions dashboard.",
)
async def get_sessions_project_metrics(
    project_id: str,
    metrics: Optional[List[str]] = None,
    filters: Optional[ProjectDataFilters] = None,
    user: User = Depends(propelauth.require_user),
) -> dict:
    """
    Get aggregated metrics for the sessions of a project. Used for the Sessions dashboard.
    """
    await verify_if_propelauth_user_can_access_project(user, project_id)
    logger.info(f"Sessions request: {filters}")
    if filters is None:
        filters = ProjectDataFilters(event_name=None)
    if isinstance(filters.event_name, str):
        filters.event_name = [filters.event_name]
    # Convert to UNIX timestamp in seconds
    if isinstance(filters.created_at_start, datetime.datetime):
        filters.created_at_start = int(filters.created_at_start.timestamp())
    if isinstance(filters.created_at_end, datetime.datetime):
        filters.created_at_end = int(filters.created_at_end.timestamp())

    output = await get_sessions_aggregated_metrics(
        project_id=project_id,
        metrics=metrics,
        filters=filters,
    )
    return output


@router.post(
    "/explore/{project_id}/aggregated/events",
    description="Get aggregated metrics for the events of a project. Used for the Events dashboard.",
)
async def get_events_project_metrics(
    project_id: str,
    metrics: Optional[List[str]] = None,
    filters: Optional[ProjectDataFilters] = None,
    user: User = Depends(propelauth.require_user),
):
    """
    Get aggregated metrics for the events of a project. Used for the Events dashboard.
    """
    await verify_if_propelauth_user_can_access_project(user, project_id)
    # Convert to UNIX timestamp in seconds
    if filters is None:
        filters = ProjectDataFilters()
    if isinstance(filters.created_at_start, datetime.datetime):
        filters.created_at_start = int(filters.created_at_start.timestamp())
    if isinstance(filters.created_at_end, datetime.datetime):
        filters.created_at_end = int(filters.created_at_end.timestamp())

    output = await get_events_aggregated_metrics(
        project_id=project_id,
        metrics=metrics,
        filters=filters,
    )
    return output


@router.post(
    "/explore/{project_id}/events",
    response_model=Events,
    description="Get the events of a project that match the filter",
)
async def get_filtered_events(
    project_id: str,
    limit: int = 1000,
    filters: Optional[ProjectDataFilters] = None,
    user: User = Depends(propelauth.require_user),
) -> Events:
    await verify_if_propelauth_user_can_access_project(user, project_id)

    events = await get_all_events(project_id=project_id, limit=limit, filters=filters)
    return Events(events=events)


@router.get(
    "/explore/{project_id}/ab-tests",
    response_model=ABTests,
    description="Get the different scores of the ab tests of a project",
)
async def get_ab_tests(
    project_id: str,
    limit: int = 10000,
    user: User = Depends(propelauth.require_user),
) -> ABTests:
    """
    Get the different scores of the ab tests of a project.

    AB tests are tasks with a version_id. The version_id is used to group the tasks together.
    """
    await verify_if_propelauth_user_can_access_project(user, project_id)
    ab_tests = await create_ab_tests_table(project_id=project_id, limit=limit)
    return ABTests(abtests=ab_tests)


@router.post(
    "/explore/{project_id}/clusterings",
    response_model=Clusterings,
    description="Get the all the clusterings of a project",
)
async def post_all_clusterings(
    project_id: str,
    user: User = Depends(propelauth.require_user),
) -> Clusterings:
    """
    Get all the clusterings of a project.

    Clusterings are groups of clusters.
    """
    await verify_if_propelauth_user_can_access_project(user, project_id)
    clusterings = await fetch_all_clusterings(project_id=project_id)
    return Clusterings(clusterings=clusterings)


@router.post(
    "/explore/{project_id}/clusters",
    response_model=Clusters,
    description="Get the different clusters of a project",
)
async def post_all_clusters(
    project_id: str,
    query: Optional[FetchClustersRequest] = None,
    user: User = Depends(propelauth.require_user),
) -> Clusters:
    """
    Get all the clusters of a project.

    Clusters are groups of tasks.
    """
    await verify_if_propelauth_user_can_access_project(user, project_id)
    if query is None:
        query = FetchClustersRequest()
    clusters = await fetch_all_clusters(
        project_id=project_id,
        clustering_id=query.clustering_id,
        limit=query.limit,
    )
    return Clusters(clusters=clusters)


@router.post(
    "/explore/{project_id}/clusters/{cluster_id}",
    response_model=Cluster,
    description="Get the different clusters of a project",
)
async def post_single_cluster(
    project_id: str,
    cluster_id: str,
    user: User = Depends(propelauth.require_user),
) -> Cluster:
    """
    Get a cluster data
    """
    await verify_if_propelauth_user_can_access_project(user, project_id)
    cluster = await fetch_single_cluster(project_id=project_id, cluster_id=cluster_id)
    if cluster is None:
        raise HTTPException(
            status_code=404,
            detail=f"Cluster {cluster_id} not found in project {project_id}",
        )
    return cluster


@router.post(
    "/explore/{project_id}/detect-clusters",
    response_model=None,
    description="Run the clusters detection algorithm on a project",
)
async def post_detect_clusters(
    project_id: str,
    query: DetectClustersRequest,
    user: User = Depends(propelauth.require_user),
) -> dict:
    """
    Run the clusters detection algorithm on a project
    """
    org_id = await verify_if_propelauth_user_can_access_project(user, project_id)
    org_plan = await get_quota(project_id)
    current_usage = org_plan.get("current_usage", 0)
    max_usage = org_plan.get("max_usage", config.PLAN_HOBBY_MAX_NB_DETECTIONS)

    if query is None:
        query = DetectClustersRequest()

    # Convert to UNIX timestamp in seconds for JSON serialization
    if query.filters.created_at_start is not None:
        query.filters.created_at_start = round(
            query.filters.created_at_start.timestamp()
        )
    if query.filters.created_at_end is not None:
        query.filters.created_at_end = round(query.filters.created_at_end.timestamp())

    total_nb_tasks = await get_total_nb_of_tasks(project_id)
    if total_nb_tasks:
        clustering_sample_size = min(total_nb_tasks, query.limit)
    else:
        raise HTTPException(
            status_code=404,
            detail="No tasks found in the project.",
        )

    if org_plan.get("plan") == "hobby" or org_plan.get("plan") is None:
        if current_usage + clustering_sample_size >= max_usage:
            raise HTTPException(
                status_code=403,
                detail="Payment details required to run the cluster detection algorithm.",
            )

    await bill_on_stripe(org_id=org_id, nb_credits_used=clustering_sample_size * 2)
    await clustering(
        clustering_request=ClusteringRequest(
            project_id=project_id,
            org_id=org_id,
            limit=query.limit,
            filters=query.filters,
        )
    )
    return {"status": "ok"}


@router.get(
    "/explore/{project_id}/nb_items_with_a_metadata_field/{collection_name}/{metadata_field}",
    description="Get the number of different metadata values in a project.",
)
async def get_nb_items_with_a_metadata_field(
    project_id: str,
    collection_name: str,
    metadata_field: str,
    user: User = Depends(propelauth.require_user),
) -> dict:
    await verify_if_propelauth_user_can_access_project(user, project_id)

    count = await nb_items_with_a_metadata_field(
        project_id=project_id,
        collection_name=collection_name,
        metadata_field=metadata_field,
    )

    return {"value": count}


@router.get(
    "/explore/{project_id}/compute_nb_items_with_metadata_field/{collection_name}/{metadata_field}",
    description="Get the average number of metadata values in a project.",
)
async def get_compute_nb_items_with_metadata_field(
    project_id: str,
    collection_name: str,
    metadata_field: str,
    user: User = Depends(propelauth.require_user),
) -> dict:
    await verify_if_propelauth_user_can_access_project(user, project_id)

    quantile_value = 0.1

    (
        bottom_quantile,
        average,
        top_quantile,
    ) = await compute_nb_items_with_metadata_field(
        project_id=project_id,
        collection_name=collection_name,
        metadata_field=metadata_field,
        quantile_value=quantile_value,
    )

    return {
        "bottom_quantile": bottom_quantile,
        "average": average,
        "top_quantile": top_quantile,
        "quantile_value": quantile_value,
    }


@router.get(
    "/explore/{project_id}/compute_session_length_per_metadata/{metadata_field}",
    description="Get the average session length for a metadata field.",
)
async def get_compute_session_length_per_metadata(
    project_id: str,
    metadata_field: str,
    user: User = Depends(propelauth.require_user),
) -> dict:
    await verify_if_propelauth_user_can_access_project(user, project_id)

    quantile_value = 0.1

    (
        bottom_quantile,
        average,
        top_quantile,
    ) = await compute_session_length_per_metadata(
        project_id=project_id,
        metadata_field=metadata_field,
        quantile_value=quantile_value,
    )

    return {
        "bottom_quantile": bottom_quantile,
        "average": average,
        "top_quantile": top_quantile,
        "quantile_value": quantile_value,
    }


@router.get(
    "/metadata/{project_id}/successrate-stats/{collection_name}/{metdata_field}",
    description="Get the stats on success rate for a project's collection.",
)
async def get_successrate_stats(
    project_id: str,
    collection_name: str,
    metadata_field: str,
    user: User = Depends(propelauth.require_user),
) -> dict:
    await verify_if_propelauth_user_can_access_project(user, project_id)

    (
        bottom_quantile,
        average,
        top_quantile,
    ) = await compute_successrate_metadata_quantiles(
        project_id, metadata_field, collection_name=collection_name
    )

    return {
        "bottom_quantile": bottom_quantile,
        "average": average,
        "top_quantile": top_quantile,
    }


@router.post(
    "/explore/{project_id}/dashboard",
    description="Get the different graphs for the dashboard tab",
)
async def get_dashboard_graphs(
    project_id: str,
    metric: Optional[DashboardMetricsFilter] = None,
    user: User = Depends(propelauth.require_user),
):
    await verify_if_propelauth_user_can_access_project(user, project_id)
    if metric is None:
        metric = DashboardMetricsFilter()
    if metric.graph_name is None:
        metric.graph_name = []
    output = await get_dashboard_aggregated_metrics(
        project_id=project_id, metrics=metric.graph_name
    )
    return output


@router.post(
    "/explore/{project_id}/aggregated/events/{event_id}",
    description="Get aggregated metrics for an event. Used for the Events dashboard.",
)
async def get_event_detection_metrics(
    project_id: str,
    event_id: str,
    metrics: Optional[List[str]] = None,
    filters: Optional[ProjectDataFilters] = None,
    user: User = Depends(propelauth.require_user),
) -> dict:
    """
    Get aggregated metrics for an event. Used for the event dashboard.
    """
    await verify_if_propelauth_user_can_access_project(user, project_id)
    logger.info(f"Event request: {event_id} {filters}")
    event = await get_event_definition_from_event_id(
        project_id=project_id, event_id=event_id
    )
    logger.info(f"Event: {event}")

    # Convert to UNIX timestamp in seconds
    if filters is None:
        filters = ProjectDataFilters()
    if isinstance(filters.created_at_start, datetime.datetime):
        filters.created_at_start = int(filters.created_at_start.timestamp())
    if isinstance(filters.created_at_end, datetime.datetime):
        filters.created_at_end = int(filters.created_at_end.timestamp())

    # Override the event_name filter
    # TODO : Use event_id instead of event_name
    # filters.event_id = [event.id]
    filters.event_id = [event.id]

    output = await get_events_aggregated_metrics(
        project_id=project_id,
        metrics=metrics,
        filters=filters,
    )
    logger.info(f"Event output: {output}")
    return output
