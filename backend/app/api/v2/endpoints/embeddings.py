from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from loguru import logger
import tiktoken

from app.api.v2.models import (
    Embedding,
    EmbeddingRequest,
    EmbeddingResponseData,
    EmbeddingUsage,
    EmbeddingResponse,
)
from app.services.mongo.ai_hub import generate_embeddings
from app.services.mongo.predict import metered_prediction
from app.core import config

from app.security import authenticate_org_key

router = APIRouter(tags=["embeddings"])

encoding = tiktoken.get_encoding("cl100k_base")


@router.post(
    "/embeddings",
    description="Generate intent embeddings for a text",
    response_model=EmbeddingResponse,
)
async def post_embeddings(
    background_tasks: BackgroundTasks,
    request_body: EmbeddingRequest,
    org: dict = Depends(authenticate_org_key),
):
    org_metadata = org["org"].get("metadata", {})
    org_id = org["org"]["org_id"]

    # Check if the organization has a payment method
    customer_id = None

    if "customer_id" in org_metadata.keys():
        customer_id = org_metadata.get("customer_id", None)

    if (
        not customer_id
        and org_id != config.PHOSPHO_ORG_ID
        and config.ENVIRONMENT != "test"
    ):
        raise HTTPException(
            status_code=402,
            detail="You need to add a payment method to access this service. Please update your payment details: https://platform.phospho.ai/org/settings/billing",
        )

    # Handle the emebedding model in the request
    if request_body.model != "intent-embed":
        raise HTTPException(
            status_code=400,
            detail="Model not supported. Only 'intent-embed' is supported for now.",
        )

    # If the input is a list of string, only accept one string
    if isinstance(request_body.input, list):
        if len(request_body.input) > 1:
            logger.warning(
                f"User input is a list of strings of len > 1. Only one string is allowed. Raising an error. org_id: {org_id}"
            )
            raise HTTPException(
                status_code=400,
                detail="Only one string is allowed in the input list for now.",
            )
        request_body.input = request_body.input[0]

    # Add the organization id to the request body
    request_body.org_id = org_id

    # Compute input token count
    inputs_token_count = sum([len(encoding.encode(request_body.input))])

    # Add limit to the token count
    if inputs_token_count > 15 * 1000:
        raise HTTPException(
            status_code=400,
            detail="Input token count is too high. Maximum allowed is 15k tokens.",
        )

    logger.debug(
        f"embedding request with input_token_count: {inputs_token_count} for org_id {org_id}"
    )

    # We assume the model is "phospho-intent-embed"
    embedding = await generate_embeddings(request_body)

    if embedding is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate embeddings for the request.",
        )

    # Format the response as an OpenAI compatible object
    embedding_response = EmbeddingResponse(
        model=request_body.model,
        data=[EmbeddingResponseData(embedding=embedding.embeddings, index=0)],
        usage=EmbeddingUsage(
            prompt_tokens=inputs_token_count,
            total_tokens=inputs_token_count,
        ),
    )

    # Bill the organization for the request
    # background_tasks.add_task(save_embedding, embeddings)
    if org_id != config.PHOSPHO_ORG_ID and config.ENVIRONMENT == "production":
        background_tasks.add_task(
            metered_prediction,
            org_id=org["org"]["org_id"],
            model_id=f"phospho:{request_body.model}",
            inputs=[request_body.input],
            predictions=[embedding.model_dump()],
            project_id=request_body.project_id,
        )

    return embedding_response
