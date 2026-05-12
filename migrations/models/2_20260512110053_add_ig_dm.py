from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "ig_conversations" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "ig_conversation_id" VARCHAR(100) NOT NULL UNIQUE,
    "participant_username" VARCHAR(150),
    "participant_ig_id" VARCHAR(100),
    "last_message_at" TIMESTAMPTZ,
    "last_message_preview" VARCHAR(255),
    "unread_count" INT NOT NULL  DEFAULT 0,
    "is_archived" BOOL NOT NULL  DEFAULT False,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "account_id" INT NOT NULL REFERENCES "ig_accounts" ("id") ON DELETE CASCADE
);
        CREATE TABLE IF NOT EXISTS "ig_messages" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "ig_message_id" VARCHAR(100) NOT NULL UNIQUE,
    "sender_type" VARCHAR(7) NOT NULL,
    "sender_ig_id" VARCHAR(100),
    "text" TEXT,
    "timestamp" TIMESTAMPTZ,
    "is_read" BOOL NOT NULL  DEFAULT False,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "conversation_id" INT NOT NULL REFERENCES "ig_conversations" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "ig_messages"."sender_type" IS 'USER: user\nCONTACT: contact';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "ig_conversations";
        DROP TABLE IF EXISTS "ig_messages";"""
