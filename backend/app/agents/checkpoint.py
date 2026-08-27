from langgraph.checkpoint.postgres import PostgresSaver

from app.core.config import settings


def get_checkpoint_database_url() -> str:
    database_url = settings.database_url

    if database_url.startswith("postgresql+psycopg://"):
        return database_url.replace(
            "postgresql+psycopg://",
            "postgresql://",
            1,
        )

    return database_url


def create_checkpointer() -> PostgresSaver:
    return PostgresSaver.from_conn_string(
        get_checkpoint_database_url()
    )


def setup_checkpointer() -> None:
    with create_checkpointer() as checkpointer:
        checkpointer.setup()