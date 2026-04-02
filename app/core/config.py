from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Claire Observability"
    api_token: str = Field(default="changeme", description="Simple bearer/token auth secret")
    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_events_topic: str = "ai.events.raw"
    kafka_normalized_topic: str = "ai.events.normalized"
    kafka_anomalies_topic: str = "ai.events.anomalies"
    elasticsearch_url: str = "http://elasticsearch:9200"
    influxdb_url: str = "http://influxdb:8086"
    influxdb_token: str = "dev-token"
    influxdb_org: str = "claire"
    influxdb_bucket: str = "metrics"
    slack_webhook_url: str | None = None
    alert_email_recipient: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_prefix="CLAIRE_")


settings = Settings()
