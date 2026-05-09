from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "ig_accounts" ADD "profile_picture_url" TEXT;
        ALTER TABLE "ig_accounts" ADD "followers_count" INT;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "ig_accounts" DROP COLUMN "profile_picture_url";
        ALTER TABLE "ig_accounts" DROP COLUMN "followers_count";"""
