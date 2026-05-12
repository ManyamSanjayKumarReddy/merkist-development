from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "ig_accounts" ADD "last_synced_at" TIMESTAMPTZ;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "ig_accounts" DROP COLUMN "last_synced_at";"""
