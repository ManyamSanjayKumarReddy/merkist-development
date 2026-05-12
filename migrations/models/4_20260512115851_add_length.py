from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "ig_conversations" ALTER COLUMN "ig_conversation_id" TYPE VARCHAR(255) USING "ig_conversation_id"::VARCHAR(255);
        ALTER TABLE "ig_messages" ALTER COLUMN "ig_message_id" TYPE VARCHAR(255) USING "ig_message_id"::VARCHAR(255);
        ALTER TABLE "ig_messages" ALTER COLUMN "sender_ig_id" TYPE VARCHAR(255) USING "sender_ig_id"::VARCHAR(255);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "ig_messages" ALTER COLUMN "ig_message_id" TYPE VARCHAR(100) USING "ig_message_id"::VARCHAR(100);
        ALTER TABLE "ig_messages" ALTER COLUMN "sender_ig_id" TYPE VARCHAR(100) USING "sender_ig_id"::VARCHAR(100);
        ALTER TABLE "ig_conversations" ALTER COLUMN "ig_conversation_id" TYPE VARCHAR(100) USING "ig_conversation_id"::VARCHAR(100);"""
