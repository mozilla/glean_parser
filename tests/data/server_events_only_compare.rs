// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/.

// AUTOGENERATED BY glean_parser v. DO NOT EDIT.

// Required imports
use chrono::Utc;
use serde::{Deserialize, Serialize};
use serde_json;
use std::collections::HashMap;
use uuid::Uuid;

// log type string used to identify logs to process in the Moz Data Pipeline
const GLEAN_EVENT_MOZLOG_TYPE: &str = "glean-server-event";

// Code below is static, regardless of what is defined in `metrics.yaml`:
pub struct GleanEventsLogger {
    // Application Id to identify application per Glean standards
    pub app_id: String,
    // Version of application emitting the event
    pub app_display_version: String,
    // Channel to differentiate logs from prod/beta/staging/devel
    pub app_channel: String,
}

// Exported type for public method parameters
// Default impl empty values will be omitted in json from ping struct definition
#[derive(Default, Serialize, Deserialize)]
pub struct RequestInfo {
    pub user_agent: String,
    pub ip_address: String,
}

// Struct to construct the glean ping
#[derive(Serialize, Deserialize, Debug)]
pub struct ClientInfo {
    telemetry_sdk_build: String,
    first_run_date: String,
    os: String,
    os_version: String,
    architecture: String,
    app_build: String,
    app_display_version: String,
    app_channel: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct PingInfo {
    seq: u32,
    start_time: String,
    end_time: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct Ping {
    document_namespace: String,
    document_type: String,
    document_version: String,
    document_id: String,
    user_agent: Option<String>,
    ip_address: Option<String>,
    payload: String,
}

type Metrics = HashMap<String, HashMap<String, serde_json::Value>>;

#[derive(Debug, Serialize, Deserialize)]
pub struct GleanEvent {
    category: String,
    name: String,
    timestamp: i64,
    extra: HashMap<String, String>,
}

pub fn new_glean_event(
    category: &str,
    name: &str,
    extra: std::collections::HashMap<String, String>,
) -> GleanEvent {
    GleanEvent {
        category: category.to_string(),
        name: name.to_string(),
        timestamp: Utc::now().timestamp_millis(),
        extra,
    }
}
#[derive(Serialize, Deserialize, Debug)]
struct PingPayload {
    client_info: ClientInfo,
    ping_info: PingInfo,
    metrics: Metrics,
    events: Vec<GleanEvent>,
}

#[derive(Serialize, Deserialize)]
struct LogEnvelope {
    timestamp: String,
    logger: String,
    #[serde(rename = "type")]
    log_type: String,
    fields: Ping,
}

impl GleanEventsLogger {
    fn create_client_info(&self) -> ClientInfo {
        // Fields with default values are required in the Glean schema, but not used in server context
        ClientInfo {
            telemetry_sdk_build: "glean_parser v15.0.2.dev17+g81fec69a".to_string(),
            first_run_date: "Unknown".to_string(),
            os: "Unknown".to_string(),
            os_version: "Unknown".to_string(),
            architecture: "Unknown".to_string(),
            app_build: "Unknown".to_string(),
            app_display_version: self.app_display_version.clone(),
            app_channel: self.app_channel.clone(),
        }
    }

    fn create_ping_info() -> PingInfo {
        // times are ISO-8601 strings, e.g. "2023-12-19T22:09:17.440Z"
        let now = Utc::now().to_rfc3339();
        PingInfo {
            seq: 0,
            start_time: now.clone(),
            end_time: now,
        }
    }

    fn create_ping(
        &self,
        document_type: &str,
        config: &RequestInfo,
        payload: &PingPayload,
    ) -> Ping {
        let payload_json =
            serde_json::to_string(payload).expect("unable to marshal payload to json.");
        let document_id = Uuid::new_v4().to_string();
        Ping {
            document_namespace: self.app_id.clone(),
            document_type: document_type.to_string(),
            document_version: "1".to_string(),
            document_id,
            user_agent: Some(config.user_agent.clone()),
            ip_address: Some(config.ip_address.clone()),
            payload: payload_json,
        }
    }

    /// Method called by each ping-specific record method.
    /// The goal is to construct the ping, wrap it in the envelope
    /// and print to stdout.
    fn record(
        &self,
        document_type: &str,
        request_info: &RequestInfo,
        metrics: Metrics,
        events: Vec<GleanEvent>,
    ) {
        let telemetry_payload: PingPayload = PingPayload {
            client_info: self.create_client_info(),
            ping_info: GleanEventsLogger::create_ping_info(),
            metrics,
            events,
        };

        let ping: Ping = self.create_ping(document_type, request_info, &telemetry_payload);

        let envelope: LogEnvelope = LogEnvelope {
            timestamp: Utc::now().timestamp().to_string(),
            logger: "glean".to_string(),
            log_type: GLEAN_EVENT_MOZLOG_TYPE.to_string(),
            fields: ping,
        };
        let envelope_json =
            serde_json::to_string(&envelope).expect("unable to marshal payload to json.");
        println!("{}", envelope_json);
    }
}

// Code below is generated based on the provided `metrics.yaml` file:

// Metrics of the `event` type. Anything defined in `extra_keys` has it's own struct field.
// The appended `Event` term to any metric of the event type implies the ping event.

pub struct BackendTestEventEvent {
    // metadata for event in `extra_keys`
    pub event_field_string: String, // A string extra field
    pub event_field_quantity: u64, // A quantity extra field
    pub event_field_bool: bool, // A boolean extra field
}

// Implementing the EventsPingEvent trait for the generated struct BackendTestEventEvent
impl EventsPingEvent for BackendTestEventEvent {
    /// Create a GleanEvent for the above-defined Event struct (BackendTestEventEvent).
    /// Any metadata `extra` values are passed into the extra HashMap.
    fn glean_event(&self) -> GleanEvent {
        // Any `extra_keys` will be output below to be inserted into `extra`. 
        // If there are none, an empty, immutable HashMap is created.
        let mut extra: HashMap<String, String> = HashMap::new();

        extra.insert("event_field_string".to_string(), self.event_field_string.to_string());
        extra.insert("event_field_quantity".to_string(), self.event_field_quantity.to_string());
        extra.insert("event_field_bool".to_string(), self.event_field_bool.to_string());

        new_glean_event(
            "backend",
            "test_event",
            extra
        )
    }
}


/// Marker trait for events per ping
pub trait EventsPingEvent {
    fn glean_event(&self) -> GleanEvent;  // Returns an instance of GleanEvent
}

pub struct EventsPing {
    pub metric_name: String, // Test string metric
    pub metric_request_bool: bool, // boolean
    pub metric_request_count: u64, // Test quantity metric
    pub metric_request_datetime: chrono::DateTime<Utc>, // Test datetime metric
    pub event: Option<Box<dyn EventsPingEvent>>, // valid event of  `EventsPingEvent` for this ping
}

// Record and submit `events` ping
impl GleanEventsLogger {
    /// General `record_events_ping` function
    pub fn record_events_ping(&self, request_info: &RequestInfo, params: &EventsPing) {
        // Define the outer `Metrics` map that holds the metric type.
        let mut metrics = Metrics::new();
        // Create corresponding metric value maps to insert into `Metrics`.
        let mut string_map: HashMap<String, serde_json::Value> = std::collections::HashMap::new();
        string_map.insert(
            "metric.name".to_string(),
            serde_json::Value::String(params.metric_name.to_string()),
        );
        metrics.insert("string".to_string(), string_map);

        let mut boolean_map: HashMap<String, serde_json::Value> = std::collections::HashMap::new();
        boolean_map.insert(
            "metric.request_bool".to_string(),
            serde_json::Value::Bool(params.metric_request_bool.into()),
        );
        metrics.insert("boolean".to_string(), boolean_map);

        let mut quantity_map: HashMap<String, serde_json::Value> = std::collections::HashMap::new();
        quantity_map.insert(
            "metric.request_count".to_string(),
            serde_json::Value::Number(params.metric_request_count.into()),
        );
        metrics.insert("quantity".to_string(), quantity_map);

        let mut datetime_map: HashMap<String, serde_json::Value> = std::collections::HashMap::new();
        datetime_map.insert(
		    "metric.request_datetime".to_string(),
            serde_json::Value::String(params.metric_request_datetime.format("%Y-%m-%dT%H:%M:%S%.3fZ").to_string()),
        );
        metrics.insert("datetime".to_string(), datetime_map);


        let mut events: Vec<GleanEvent> = Vec::new();
        if let Some(event) = &params.event {
            events.push(event.glean_event());
        }
        
        self.record("events", request_info, metrics, events);
    }
}

// Record and submit `events` ping omitting user request info
impl GleanEventsLogger {
    pub fn record_events_ping_without_user_info(
    &self,
    params: &EventsPing
    ) {
        self.record_events_ping(&RequestInfo::default(), params)
    }
}
