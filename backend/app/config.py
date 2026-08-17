from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    azure_storage_connection_string: str
    azure_storage_container: str = "subcontract-attachments"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8010
    cors_origins: str = "http://localhost:3001"

    jwt_secret_key: str = "dev-only-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    internal_auth_secret: str = "dev-only-insecure-secret-change-me"
    # One-click test login (Admin/Requester/Approver) on the login screen, bypassing Microsoft
    # sign-in entirely. Set to false in production.
    enable_quick_login: bool = True
    frontend_base_url: str = "http://localhost:3001"
    backend_base_url: str = "http://localhost:8010"

    microsoft_tenant_id: str = ""
    microsoft_client_id: str = ""
    microsoft_client_secret: str = ""
    microsoft_sender_mailbox: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
