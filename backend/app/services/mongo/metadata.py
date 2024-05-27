from typing import Dict, List, Literal, Optional
from app.api.v2.models.projects import UserMetadata
from fastapi import HTTPException
from loguru import logger
from app.services.mongo.sessions import compute_session_length, compute_task_position

from app.db.mongo import get_mongo_db
from phospho.models import ProjectDataFilters


async def fetch_count(
    project_id: str, collection_name: str, metadata_field: str
) -> int:
    """
    Fetch the number of users that are in a projects
    """
    mongo_db = await get_mongo_db()
    nb_users = await mongo_db[collection_name].distinct(
        key=f"metadata.{metadata_field}",
        filter={
            "project_id": project_id,
            # Ignore null values
            f"metadata.{metadata_field}": {"$ne": None},
        },
    )
    return len(nb_users)


async def calculate_average_for_metadata(
    project_id: str, collection_name: str, metadata_field: str
) -> float:
    mongo_db = await get_mongo_db()

    pipeline = [
        {
            "$match": {
                "project_id": project_id,
                f"metadata.{metadata_field}": {"$exists": True},
            }
        },  # Filter for a specific project_id
        {"$group": {"_id": f"$metadata.{metadata_field}", "count": {"$sum": 1}}},
        {"$group": {"_id": None, "average": {"$avg": "$count"}}},
    ]

    result = await mongo_db[collection_name].aggregate(pipeline).to_list(length=None)
    if not result or "average" not in result[0]:
        raise HTTPException(status_code=404, detail="No data found")
    average = result[0]["average"]
    return average


async def calculate_top10_percent(
    project_id: str, collection_name: str, metadata_field: str
) -> int:
    mongo_db = await get_mongo_db()

    # Define the pipeline
    pipeline = [
        {"$match": {"project_id": project_id}},
        {"$match": {f"metadata.{metadata_field}": {"$exists": True}}},
        {
            "$group": {
                "_id": f"$metadata.{metadata_field}",
                "metadataValueCount": {"$sum": 1},
            }
        },
        {"$sort": {"metadataValueCount": -1}},
        {
            "$facet": {
                "totalKeyCount": [{"$count": "count"}],
                "sortedData": [{"$match": {}}],
            }
        },
    ]

    # Run the aggregation pipeline
    result = await mongo_db[collection_name].aggregate(pipeline).to_list(None)
    if not result or not result[0]["totalKeyCount"]:
        raise HTTPException(status_code=404, detail="No data found")

    total_users = result[0]["totalKeyCount"][0]["count"]
    ten_percent_index = max(
        int(total_users * 0.1) - 1, 0
    )  # Calculate the 10% index, ensure it's not negative

    # Retrieve the task count of the user at the 10% threshold
    # Ensure that the list is long enough
    if ten_percent_index < len(result[0]["sortedData"]):
        ten_percent_user_task_count = result[0]["sortedData"][ten_percent_index][
            "metadataValueCount"
        ]
        logger.debug(
            f"{metadata_field} count at the 10% threshold in {collection_name}: {ten_percent_user_task_count}"
        )
        return ten_percent_user_task_count

    else:
        logger.warning(
            "The dataset does not have enough users to determine the 10% threshold."
        )
        return 0


async def calculate_bottom10_percent(
    project_id: str, collection_name: str, metadata_field: str
) -> int:
    mongo_db = await get_mongo_db()

    # Define the pipeline with ascending sort order
    pipeline = [
        {"$match": {"project_id": project_id}},
        {"$match": {f"metadata.{metadata_field}": {"$exists": True}}},
        {"$group": {"_id": "$metadata.user_id", "metadataValueCount": {"$sum": 1}}},
        {"$sort": {"metadataValueCount": 1}},  # Sort in ascending order
        {
            "$facet": {
                "totalMetadataKeyCount": [{"$count": "count"}],
                "sortedData": [{"$match": {}}],
            }
        },
    ]

    # Run the aggregation pipeline
    result = await mongo_db["tasks"].aggregate(pipeline).to_list(None)
    if not result or not result[0]["totalMetadataKeyCount"]:
        raise HTTPException(status_code=404, detail="No data found")

    total_users = result[0]["totalMetadataKeyCount"][0]["count"]
    ten_percent_index = min(
        int(total_users * 0.1), total_users - 1
    )  # Calculate the bottom 10% index

    # Retrieve the task count of the user at the bottom 10% threshold
    # Ensure that the list is long enough
    if ten_percent_index < len(result[0]["sortedData"]):
        bottom_ten_percent_user_task_count = result[0]["sortedData"][ten_percent_index][
            "metadataValueCount"
        ]
        logger.debug(
            f"{metadata_field} count at the 10% bottom threshold in {collection_name}: {bottom_ten_percent_user_task_count}"
        )
        return bottom_ten_percent_user_task_count

    else:
        logger.warning(
            "The dataset does not have enough users to determine the bottom 10% threshold."
        )
        return 0


async def fetch_user_metadata(
    project_id: str,
    user_id: Optional[str] = None,
) -> List[UserMetadata]:
    """
    Get the user metadata for a specific user in a project

    The UserMetadata contains:
        user_id: str
        nb_tasks: int
        avg_success_rate: float
        avg_session_length: float
        nb_tokens: int
        events: List[Event]
        tasks_id: List[str]
        sessions: List[Session]
    """
    mongo_db = await get_mongo_db()

    match_pipeline: List[Dict[str, object]] = []
    if user_id is not None:
        match_pipeline = [
            {"$match": {"project_id": project_id, "metadata.user_id": user_id}},
        ]
    else:
        match_pipeline = [
            {
                "$match": {
                    "project_id": project_id,
                    "metadata.user_id": {"$ne": None},
                },
            },
        ]

    # First, we update the relevant sessions collection with the session_length
    # await compute_session_length(project_id)

    # Then, we fetch the user metadata
    metadata_pipeline = match_pipeline + [
        {
            "$set": {
                "is_success": {"$cond": [{"$eq": ["$flag", "success"]}, 1, 0]},
                # If metadata.total_tokens is not present, set to 0
                "metadata.total_tokens": {
                    "$cond": [
                        {"$eq": [{"$type": "$metadata.total_tokens"}, "missing"]},
                        0,
                        "$metadata.total_tokens",
                    ]
                },
            }
        },
        {
            "$group": {
                "_id": "$metadata.user_id",
                "nb_tasks": {"$sum": 1},
                "avg_success_rate": {"$avg": {"$toInt": "$is_success"}},
                "tasks": {"$push": "$$ROOT"},
                "total_tokens": {"$sum": "$metadata.total_tokens"},
                "events": {"$push": "$events"},
            }
        },
        {
            "$lookup": {
                "from": "sessions",
                "localField": "tasks.session_id",
                "foreignField": "id",
                "as": "sessions",
            }
        },
        {
            "$set": {
                "events": {
                    "$reduce": {
                        "input": "$events",
                        "initialValue": [],
                        "in": {"$setUnion": ["$$value", "$$this"]},
                    }
                }
            }
        },
        # If events or sessions are None, set to empty list
        {
            "$addFields": {
                "events": {"$ifNull": ["$events", []]},
                "sessions": {"$ifNull": ["$sessions", []]},
            }
        },
        # Deduplicate events names and sessions ids. We want the unique event_names of the session
        {
            "$addFields": {
                "events": {
                    "$reduce": {
                        "input": "$events",
                        "initialValue": [],
                        "in": {
                            "$concatArrays": [
                                "$$value",
                                {
                                    "$cond": [
                                        {
                                            "$in": [
                                                "$$this.event_name",
                                                "$$value.event_name",
                                            ]
                                        },
                                        [],
                                        ["$$this"],
                                    ]
                                },
                            ]
                        },
                    }
                },
                "sessions": {
                    "$reduce": {
                        "input": "$sessions",
                        "initialValue": [],
                        "in": {
                            "$concatArrays": [
                                "$$value",
                                {
                                    "$cond": [
                                        {
                                            "$in": [
                                                "$$this.id",
                                                "$$value.id",
                                            ]
                                        },
                                        [],
                                        ["$$this"],
                                    ]
                                },
                            ]
                        },
                    }
                },
            }
        },
        # Compute the average session length
        {
            "$project": {
                "user_id": "$_id",
                "nb_tasks": 1,
                "avg_success_rate": 1,
                "avg_session_length": {"$avg": "$sessions.session_length"},
                "events": 1,
                # "tasks": 1,
                "tasks_id": "$tasks.id",
                "sessions": 1,
                # "sessions_id": "$sessions.id",
                "total_tokens": 1,
            }
        },
        # Sort by user_id
        {"$sort": {"user_id": 1}},
    ]

    users = await mongo_db["tasks"].aggregate(metadata_pipeline).to_list(length=None)
    if users is None or (user_id is not None and len(users) == 0):
        raise HTTPException(status_code=404, detail="No user found")

    users = [UserMetadata.model_validate(data) for data in users]
    # logger.debug(f"User metadata: {users}")

    return users


async def _build_unique_metadata_fields_pipeline(
    project_id: str, type: Literal["number", "string"] = "number"
) -> List[Dict[str, object]]:
    pipeline: List[Dict[str, object]] = [
        {
            "$match": {
                "project_id": project_id,
                "$and": [
                    {"metadata": {"$exists": True}},
                    {"metadata": {"$ne": {}}},
                ],
            },
        },
        {
            "$project": {"metadata_keys": {"$objectToArray": "$metadata"}},
        },
        {"$unwind": "$metadata_keys"},
    ]
    # Filter by type
    # https://www.mongodb.com/docs/manual/reference/operator/query/type/
    if type == "number":
        pipeline.append(
            {
                "$match": {
                    "$expr": {"$eq": [{"$isNumber": "$metadata_keys.v"}, True]},
                }
            }
        )
    if type == "string":
        pipeline.append(
            {
                "$match": {
                    "$expr": {"$eq": [{"$type": "$metadata_keys.v"}, "string"]},
                }
            }
        )

    return pipeline


async def collect_unique_metadata_fields(
    project_id: str,
    type: Literal["number", "string"] = "number",
) -> List[str]:
    """
    Get the unique metadata keys for a project
    """
    mongo_db = await get_mongo_db()
    pipeline = await _build_unique_metadata_fields_pipeline(project_id, type)
    pipeline += [
        {
            "$group": {
                "_id": None,
                "metadata_keys": {
                    "$addToSet": "$metadata_keys.k",
                },
                "count": {"$sum": 1},
            },
        },
        {"$sort": {"count": -1}},
    ]

    keys = await mongo_db["tasks"].aggregate(pipeline).to_list(length=None)
    if not keys or len(keys) == 0 or "metadata_keys" not in keys[0]:
        # No metadata keys found
        return []
    keys = keys[0]["metadata_keys"]
    return keys


async def collect_unique_metadata_field_values(
    project_id: str, type: Literal["number", "string"] = "string"
) -> Dict[str, List[str]]:
    """
    Get the unique metadata values for all the metadata fields of a certain
    type in a project.
    """
    if type not in ["string"]:
        raise NotImplementedError("Only string metadata values are supported")

    mongo_db = await get_mongo_db()
    pipeline = await _build_unique_metadata_fields_pipeline(project_id, type)

    # Extend the pipeline to create a dict: metadata_key: [metadata_values]
    pipeline += [
        {
            "$match": {
                "metadata_keys.k": {"$ne": "task_id"},
            }
        },
        {
            "$group": {
                "_id": "$metadata_keys.k",
                "metadata_values": {
                    "$addToSet": "$metadata_keys.v",
                },
                # "count": {"$sum": 1},
            },
        },
        {
            "$project": {
                "metadata_key": "$_id",
                "metadata_values": 1,
            }
        },
        {
            "$sort": {"metadata_key": 1, "metadata_values": 1},
        },
    ]
    keys_and_values = await mongo_db["tasks"].aggregate(pipeline).to_list(length=None)
    if not keys_and_values or len(keys_and_values) == 0:
        return {}
    keys_to_values = {
        key["metadata_key"]: key["metadata_values"] for key in keys_and_values
    }

    return keys_to_values


async def breakdown_by_sum_of_metadata_field(
    project_id: str,
    metric: str,
    metadata_field: str,
    number_metadata_fields: List[str],
    category_metadata_fields: List[str],
    breakdown_by: Optional[str] = None,
    filters: Optional[ProjectDataFilters] = None,
):
    """
    Get the sum of a metadata field, grouped by another metadata field if provided.
    """

    if filters is None:
        filters = ProjectDataFilters()

    if breakdown_by in category_metadata_fields:
        breakdown_by_col = f"metadata.{breakdown_by}"
    elif breakdown_by == "None":
        breakdown_by_col = "id"
    else:
        breakdown_by_col = breakdown_by

    mongo_db = await get_mongo_db()
    main_filter: Dict[str, object] = {
        "project_id": project_id,
    }
    if filters.created_at_start is not None:
        main_filter["created_at"] = {"$gte": filters.created_at_start}
    if filters.created_at_end is not None:
        main_filter["created_at"] = {
            **main_filter.get("created_at", {}),
            "$lte": filters.created_at_end,
        }

    pipeline: list[dict[str, object]] = [
        {"$match": main_filter},
    ]

    if breakdown_by == "event_name":
        pipeline += [
            # Deduplicate the event by event_name and task_id
            {
                "$addFields": {
                    "events": {
                        "$reduce": {
                            "input": "$events",
                            "initialValue": [],
                            "in": {
                                "$concatArrays": [
                                    "$$value",
                                    {
                                        "$cond": [
                                            {
                                                "$in": [
                                                    "$$this.event_name",
                                                    "$$value.event_name",
                                                ]
                                            },
                                            [],
                                            ["$$this"],
                                        ]
                                    },
                                ]
                            },
                        }
                    }
                }
            },
            {"$unwind": "$events"},
            {
                "$match": {
                    "events.removed": {"$ne": True},
                }
            },
        ]
        breakdown_by_col = "events.event_name"

    if breakdown_by == "task_position":
        await compute_task_position(project_id=project_id, filters=filters)
        breakdown_by_col = "task_position"

    if metric.lower() == "nb tasks":
        pipeline += [
            {
                "$group": {
                    "_id": f"${breakdown_by_col}",
                    metric: {"$sum": 1},
                },
            },
        ]

    if metric.lower() == "avg success rate":
        pipeline += [
            {
                "$match": {
                    "flag": {"$exists": True},
                }
            },
            {"$set": {"is_success": {"$cond": [{"$eq": ["$flag", "success"]}, 1, 0]}}},
            {
                "$group": {
                    "_id": f"${breakdown_by_col}",
                    metric: {"$avg": "$is_success"},
                },
            },
        ]

    if metric.lower() == "avg session length":
        pipeline += [
            {
                "$lookup": {
                    "from": "sessions",
                    "localField": "session_id",
                    "foreignField": "id",
                    "as": "session",
                },
            },
            {
                "$addFields": {
                    "session": {"$ifNull": ["$session", []]},
                }
            },
            {
                "$unwind": "$session",
            },
            {
                "$group": {
                    "_id": f"${breakdown_by_col}",
                    metric: {"$avg": "$session.session_length"},
                },
            },
        ]

    if metric.lower() == "sum":
        if metadata_field in number_metadata_fields:
            pipeline += [
                {
                    "$match": {
                        f"metadata.{metadata_field}": {"$exists": True},
                    }
                },
                {
                    "$group": {
                        "_id": f"${breakdown_by_col}",
                        f"{metric}{metadata_field}": {
                            "$sum": f"$metadata.{metadata_field}"
                        },
                    },
                },
            ]
        else:
            raise HTTPException(
                status_code=400,
                detail="Metric 'sum' is only supported for number metadata fields",
            )
    if metric.lower() == "avg":
        if metadata_field in number_metadata_fields:
            pipeline += [
                {
                    "$match": {
                        f"metadata.{metadata_field}": {"$exists": True},
                    }
                },
                {
                    "$group": {
                        "_id": f"${breakdown_by_col}",
                        f"{metric}{metadata_field}": {
                            "$avg": f"$metadata.{metadata_field}"
                        },
                    },
                },
            ]
        else:
            raise HTTPException(
                status_code=400,
                detail="Metric 'avg' is only supported for number metadata fields",
            )

    pipeline.extend(
        [
            {"$match": {"_id": {"$ne": None}}},
            {
                "$project": {
                    breakdown_by: "$_id",
                    metric: 1,
                    f"{metric}{metadata_field}": 1,
                    "_id": 0,
                },
            },
        ]
    )
    if breakdown_by == "task_position":
        pipeline.append({"$sort": {f"{breakdown_by}": 1}})
    else:
        pipeline.append({"$sort": {f"{metric}{metadata_field}": -1, metric: -1}})

    result = await mongo_db["tasks_with_events"].aggregate(pipeline).to_list(length=200)

    return result
