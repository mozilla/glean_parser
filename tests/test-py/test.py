from glean.server_events import create_events_server_event_logger


logger = create_events_server_event_logger(
    application_id="accounts_backend",
    app_display_version="0.0.1",
    channel="nightly",
)

logger.record_backend_object_update(
    user_agent="Mozilla/5.0 ...",
    ip_address="2a02:a311:803c:6300:4074:5cf2:91ac:d546",
    identifiers_fxa_account_id="test-py-project",
    object_type="some_object_type",
    object_state="some_object_state",
    linking=True,
)
