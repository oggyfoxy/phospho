import os

import resend
from loguru import logger
from propelauth_fastapi import init_auth

from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()


# Check that the two env variables are set
assert (
    os.getenv("PROPELAUTH_PRODUCTION_URL") is not None
), "PROPELAUTH_PRODUCTION_URL is missing from the environment variables"
assert (
    os.getenv("PROPELAUTH_PRODUCTION_API_KEY") is not None
), "PROPELAUTH_PRODUCTION_API_KEY is missing from the environment variables"

assert (
    os.getenv("RESEND_API_KEY") is not None
), "RESEND_API_KEY is missing from the environment variables"

assert (
    os.getenv("RESEND_AUDIENCE_ID") is not None
), "RESEND_AUDIENCE_ID is missing from the environment variables"

# Init the PropelAuth client with PRODUCTION values (Read only API key is enough)
propelauth = init_auth(
    os.getenv("PROPELAUTH_PRODUCTION_URL"), os.getenv("PROPELAUTH_PRODUCTION_API_KEY")
)

logger.warning("Reading from Production")

# Get all the organizations
# Max number of orgs is 99
first_org_response = propelauth.fetch_org_by_query(
    page_size=99,
    page_number=0,
)

# Get the number of organizations
number_of_orgs = first_org_response.get("total_orgs")

organizations = first_org_response.get("orgs")

if number_of_orgs > 99:
    # Get all the organizations
    for page_number in tqdm(range(1, number_of_orgs // 99 + 1)):
        organizations += propelauth.fetch_org_by_query(
            page_size=99,
            page_number=page_number,
        ).get("orgs")

assert len(organizations) == number_of_orgs
logger.info(f"Number of organizations: {number_of_orgs}")

# For each organization, get all the users
total_users = []

for org in tqdm(organizations):
    org_id = org["org_id"]
    users = propelauth.fetch_users_in_org(org_id=org_id, page_size=99, page_number=0)

    # Get the number of users
    number_of_users = users.get("total_users")

    org_users = users.get("users")

    if number_of_users > 99:
        # Get all the users
        for page_number in range(1, number_of_users // 99 + 1):
            org_users += propelauth.fetch_users_in_org(
                org_id=org_id,
                page_size=99,
                page_number=page_number,
            ).get("users")

    assert len(org_users) == number_of_users

    total_users += org_users

logger.info(f"Number of users: {len(total_users)}")

# Set the resend API key
resend.api_key = os.environ["RESEND_API_KEY"]

# Add each user as a contact in resend
for user in tqdm(total_users):
    if user["email"]:
        logger.info(f"Adding {user['email']} as a resend contact")
        resend.Contacts.create(
            {"email": user["email"], "audience_id": os.environ["RESEND_AUDIENCE_ID"]}
        )
