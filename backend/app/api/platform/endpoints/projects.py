import datetime
from typing import Dict, Optional, List

from app.services.mongo.files import process_file_upload_into_log_events
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from loguru import logger
import pandas as pd
from propelauth_fastapi import User

from app.api.platform.models import (
    Events,
    Project,
    ProjectUpdateRequest,
    SearchQuery,
    SearchResponse,
    Sessions,
    Tasks,
    Tests,
    AddEventsQuery,
    Users,
    ProjectDataFilters,
    QuerySessionsTasksRequest,
)
from app.security.authentification import (
    propelauth,
    verify_if_propelauth_user_can_access_project,
)
from app.services.mongo.projects import (
    delete_project_from_id,
    delete_project_related_resources,
    email_project_tasks,
    get_all_sessions,
    get_all_tests,
    get_project_by_id,
    get_all_users_metadata,
    update_project,
    add_project_events,
    collect_languages,
)
from app.services.mongo.tasks import get_all_tasks
from app.services.mongo.events import get_all_events


from app.services.mongo.search import (
    search_tasks_in_project,
    search_sessions_in_project,
)

from app.services.mongo.extractor import collect_langsmith_data
from app.security.authorization import get_quota
from app.core import config

router = APIRouter(tags=["Projects"])


@router.get(
    "/projects/{project_id}",
    response_model=Project,
    description="Get a specific project",
)
async def get_project(
    project_id: str,
    user: User = Depends(propelauth.require_user),
) -> Project:
    """
    Get a specific project
    """
    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)
    return project


@router.delete(
    "/projects/{project_id}/delete",
    response_model=None,
    description="Delete a project",
)
async def delete_project(
    project_id: str,
    background_tasks: BackgroundTasks,
    cascade_delete: bool = False,
    user: User = Depends(propelauth.require_user),
) -> Project:
    """
    Delete a project. Pass cascade_delete=True to delete all the related resources (sessions, events, tasks, tests).
    """
    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)

    await delete_project_from_id(project_id=project_id)

    # If cascade, delete all the related resources
    if cascade_delete:
        background_tasks.add_task(
            delete_project_related_resources, project_id=project_id
        )

    return project


@router.post(
    "/projects/{project_id}",
    response_model=Project,
    description="Update a project. Only the fields that are specified in the request will be updated. Specified fields will be overwritten (WARNING for nested fields like settings))",
)
async def post_update_project(
    project_id: str,
    project_update_request: ProjectUpdateRequest,
    user: User = Depends(propelauth.require_user),
) -> Project:
    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)
    updated_project = await update_project(
        project, **project_update_request.model_dump()
    )
    return updated_project


@router.post(
    "/projects/{project_id}/sessions",
    response_model=Sessions,
    description="Get all the sessions of a project",
)
async def post_sessions(
    project_id: str,
    query: Optional[QuerySessionsTasksRequest] = None,
    user: User = Depends(propelauth.require_user),
) -> Sessions:
    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)
    if query is None:
        query = QuerySessionsTasksRequest()
    # Convert to UNIX timestamp in seconds
    if isinstance(query.filters.created_at_start, datetime.datetime):
        query.filters.created_at_start = int(query.filters.created_at_start.timestamp())
    if isinstance(query.filters.created_at_end, datetime.datetime):
        query.filters.created_at_end = int(query.filters.created_at_end.timestamp())

    sessions = await get_all_sessions(
        project_id=project_id,
        get_events=True,
        get_tasks=False,
        filters=query.filters,
        pagination=query.pagination,
        sorting=query.sorting,
    )
    return Sessions(sessions=sessions)


@router.get(
    "/projects/{project_id}/sessions",
    response_model=Sessions,
    description="Get all the sessions of a project",
)
async def get_sessions(
    project_id: str,
    user: User = Depends(propelauth.require_user),
) -> Sessions:
    return await post_sessions(project_id=project_id, user=user)


@router.get(
    "/projects/{project_id}/events",
    response_model=Events,
    description="Get all the events of a project",
)
async def get_events(
    project_id: str,
    limit: int = 1000,
    user: User = Depends(propelauth.require_user),
) -> Events:
    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)
    events = await get_all_events(project_id=project_id, limit=limit)
    return Events(events=events)


@router.post(
    "/projects/{project_id}/search/tasks",
    response_model=SearchResponse,
    description="Perform a semantic search in the project's sessions",
)
async def post_search_tasks(
    project_id: str,
    search_query: SearchQuery,
    user: User = Depends(propelauth.require_user),
):
    """
    Get the resulting session_ids of a semantic search in the project's sessions.
    The search is based on embedding similarity of the text conversation to the query.
    """

    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)
    # Perform the semantic search
    relevant_tasks = await search_tasks_in_project(
        project_id=project_id,
        search_query=search_query.query,
    )
    return SearchResponse(task_ids=[task.id for task in relevant_tasks])


@router.get(
    "/projects/{project_id}/languages",
    description="Get the list of all unique languages detected in a project.",
    response_model=List[str],
)
async def get_languages(
    project_id: str,
    user: User = Depends(propelauth.require_user),
) -> List[str]:
    """
    Get the list of all unique languages detected in a project.
    """
    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)
    languages = await collect_languages(project_id=project_id)
    return languages


@router.post(
    "/projects/{project_id}/search/sessions",
    response_model=SearchResponse,
    description="Perform a semantic search in the project's sessions",
)
async def post_search_sessions(
    project_id: str,
    search_query: SearchQuery,
    user: User = Depends(propelauth.require_user),
):
    """
    Get the resulting session_ids of a semantic search in the project's sessions.
    The search is based on embedding similarity of the text conversation to the query.
    """

    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)
    # Perform the semantic search
    relevant_tasks, relevant_sessions = await search_sessions_in_project(
        project_id=project_id,
        search_query=search_query.query,
    )
    return SearchResponse(
        task_ids=[task.id for task in relevant_tasks],
        session_ids=[session.id for session in relevant_sessions],
    )


@router.post(
    "/projects/{project_id}/tasks",
    response_model=Tasks,
    description="Get all the tasks of a project",
)
async def post_tasks(
    project_id: str,
    query: Optional[QuerySessionsTasksRequest] = None,
    user: User = Depends(propelauth.require_user),
):
    """
    Get all the tasks of a project.

    Args:
        project_id: The id of the project
        limit: The maximum number of tasks to return
    """
    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)

    if query is None:
        query = QuerySessionsTasksRequest()
    if query.filters.user_id is not None:
        if query.filters.metadata is None:
            query.filters.metadata = {}
        query.filters.metadata["user_id"] = query.filters.user_id

    tasks = await get_all_tasks(
        project_id=project_id,
        limit=None,
        validate_metadata=True,
        filters=query.filters,
        sorting=query.sorting,
        pagination=query.pagination,
    )
    return Tasks(tasks=tasks)


@router.get(
    "/projects/{project_id}/tasks",
    response_model=Tasks,
    description="Get all the tasks of a project",
)
async def get_tasks(
    project_id: str,
    user: User = Depends(propelauth.require_user),
):
    return await post_tasks(project_id=project_id, user=user)


@router.get(
    "/projects/{project_id}/tasks/email",
    description="Get an email with the tasks of a project in csv and xlsx format",
)
async def email_tasks(
    project_id: str,
    background_tasks: BackgroundTasks,
    environment: Optional[str] = None,
    limit: int = 1000,
    user: User = Depends(propelauth.require_user),
) -> dict:
    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)
    # Trigger the email sending in the background
    background_tasks.add_task(
        email_project_tasks, project_id=project_id, uid=user.user_id
    )
    logger.info(f"Emailing tasks of project {project_id} to {user.email}")
    return {"status": "ok"}


@router.get(
    "/projects/{project_id}/tests",
    response_model=Tests,
    description="Get all the tests of a project",
)
async def get_tests(
    project_id: str,
    limit: int = 1000,
    user: User = Depends(propelauth.require_user),
) -> Tests:
    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)
    tests = await get_all_tests(project_id=project_id, limit=limit)
    return Tests(tests=tests)


@router.post(
    "/projects/{project_id}/add-events",
    response_model=Project,
    description="Add events to a project",
)
async def add_events(
    project_id: str,
    events: AddEventsQuery,
    user: User = Depends(propelauth.require_user),
) -> Project:
    """
    Add events to a project
    """
    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)
    # Add events to the project
    logger.debug(f"Adding events to project {project_id}: {events.events}")
    updated_project = await add_project_events(project_id, events.events)
    return updated_project


@router.get(
    "/projects/{project_id}/users",
    response_model=Users,
    description="Get metadata about the end-users of a project",
)
async def get_users(
    project_id: str,
    user: User = Depends(propelauth.require_user),
) -> Users:
    """
    Get metadata about the end-users of a project
    """
    await verify_if_propelauth_user_can_access_project(user, project_id)
    users = await get_all_users_metadata(project_id)
    return Users(users=users)


@router.get(
    "/projects/{project_id}/unique-events",
    response_model=Events,
)
async def get_project_unique_events(
    project_id: str,
    filters: Optional[ProjectDataFilters] = None,
    user: User = Depends(propelauth.require_user),
) -> Events:
    """
    Get the unique observed events in a project
    """
    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)
    events = await get_all_events(
        project_id=project_id,
        filters=filters,
        include_removed=True,
        unique=True,
    )
    return Events(events=events)


@router.post(
    "/projects/{project_id}/upload-tasks",
    response_model=dict,
)
async def post_upload_tasks(
    project_id: str,
    file: UploadFile,
    # file_params: UploadTasksRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(propelauth.require_user),
) -> dict:
    """
    Upload a file with tasks to a project

    Supported file formats: csv, xlsx

    The file should contain the following columns:
    - input: the input text
    - output: the expected output text

    Optional columns:
    - task_id: the task id
    - session_id: the session id to which the task is associated
    - created_at: the creation date of the task
    """
    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)

    if not file.filename:
        raise HTTPException(status_code=400, detail="Error: No file provided.")

    SUPPORTED_EXTENSIONS = ["csv", "xlsx"]  # Add the supported extensions here
    file_extension = file.filename.split(".")[-1]
    if file_extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Error: The extension {file_extension} is not supported (supported: {SUPPORTED_EXTENSIONS}).",
        )

    # Read file content -> into memory
    file_params = {}
    try:
        if file_extension == "csv":
            tasks_df = pd.read_csv(file.file, sep=None, **file_params)
        elif file_extension == "xlsx":
            tasks_df = pd.read_excel(file.file, **file_params)
        else:
            # This only happens if you add a new extension and forget to update the supported extensions list
            raise NotImplementedError(
                f"Error: The extension {file_extension} is not supported (supported: {SUPPORTED_EXTENSIONS})."
            )
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error: Could not read the file content. {e}"
        )

    # Strip and lowercase the columns
    tasks_df.columns = tasks_df.columns.str.strip().str.lower()

    # Verify if the required columns are present
    required_columns = ["input", "output"]
    missing_columns = set(required_columns) - set(tasks_df.columns)
    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail=f"Error: Missing columns: {missing_columns}",
        )

    # Process the csv file as a background task
    logger.info(f"File {file.filename} uploaded successfully. Processing tasks.")
    background_tasks.add_task(
        process_file_upload_into_log_events,
        tasks_df=tasks_df,
        project_id=project_id,
        org_id=project.org_id,
    )
    return {"status": "ok", "num_rows": tasks_df.shape[0]}


@router.post(
    "/projects/{project_id}/connect-langsmith",
    response_model=dict,
)
async def connect_langsmith(
    project_id: str,
    credentials: dict,
    background_tasks: BackgroundTasks,
    user: User = Depends(propelauth.require_user),
) -> dict:
    """
    Import data from Langsmith to a Phospho project
    """
    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)

    logger.debug(f"Connecting Langsmith to project {project_id}")

    try:
        # This snippet is used to test the connection with Langsmith and verify the API key/project name
        from langsmith import Client

        client = Client(api_key=credentials["langsmith_api_key"])
        runs = client.list_runs(
            project_name=credentials["project_name"],
            start_time=datetime.datetime.now() - datetime.timedelta(seconds=1),
        )
        _ = [run for run in runs]
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error: Could not connect to Langsmith. {e}"
        )

    org_plan = await get_quota(project_id)
    current_usage = org_plan.get("current_usage", 0)
    max_usage = org_plan.get("max_usage", config.PLAN_HOBBY_MAX_NB_DETECTIONS)

    background_tasks.add_task(
        collect_langsmith_data,
        project_id=project_id,
        org_id=project.org_id,
        langsmith_credentials=credentials,
        current_usage=current_usage,
        max_usage=max_usage,
    )
    return {"status": "ok", "message": "Langsmith connected successfully."}
