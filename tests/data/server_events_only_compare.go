package glean

// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/.

// AUTOGENERATED BY {current_version}. DO NOT EDIT.

// required imports
import (
	"encoding/json"
    "fmt"
	"strconv"
	"time"

	"github.com/google/uuid"
)

// log type string used to identify logs to process in the Moz Data Pipeline
var gleanEventMozlogType string = "glean-server-event"

type GleanEventsLogger struct {
	AppID             string // Application Id to identify application per Glean standards
	AppDisplayVersion string // Version of application emitting the event
	AppChannel        string // Channel to differentiate logs from prod/beta/staging/devel
}

// exported type for public method parameters
type RequestInfo struct {
	UserAgent string
	IpAddress string
}

// default empty values will be omitted in json from ping struct definition
var defaultRequestInfo = RequestInfo{
	UserAgent: "",
	IpAddress: "",
}

// structs to construct the glean ping
type clientInfo struct {
	TelemetrySDKBuild string `json:"telemetry_sdk_build"`
	FirstRunDate      string `json:"first_run_date"`
	OS                string `json:"os"`
	OSVersion         string `json:"os_version"`
	Architecture      string `json:"architecture"`
	AppBuild          string `json:"app_build"`
	AppDisplayVersion string `json:"app_display_version"`
	AppChannel        string `json:"app_channel"`
}

type pingInfo struct {
	Seq       int    `json:"seq"`
	StartTime string `json:"start_time"`
	EndTime   string `json:"end_time"`
}

type ping struct {
	DocumentNamespace string `json:"document_namespace"`
	DocumentType      string `json:"document_type"`
	DocumentVersion   string `json:"document_version"`
	DocumentID        string `json:"document_id"`
	UserAgent         string `json:"user_agent,omitempty"`
	IpAddress         string `json:"ip_address,omitempty"`
	Payload           string `json:"payload"`
}

type metrics map[string]map[string]interface{}

type pingPayload struct {
	ClientInfo clientInfo   `json:"client_info"`
	PingInfo   pingInfo     `json:"ping_info"`
	Metrics    metrics      `json:"metrics"`
	Events     []gleanEvent `json:"events"`
}

type gleanEvent struct {
	Category  string            `json:"category"`
	Name      string            `json:"name"`
	Timestamp int64             `json:"timestamp"`
	Extra     map[string]string `json:"extra"`
}

type logEnvelope struct {
	Timestamp string
	Logger    string
	Type      string
	Fields    ping
}

func (g GleanEventsLogger) createClientInfo() clientInfo {
	// Fields with default values are required in the Glean schema, but not used in server context
	return clientInfo{
		TelemetrySDKBuild: "{current_version}",
		FirstRunDate:      "Unknown",
		OS:                "Unknown",
		OSVersion:         "Unknown",
		Architecture:      "Unknown",
		AppBuild:          "Unknown",
		AppDisplayVersion: g.AppDisplayVersion,
		AppChannel:        g.AppChannel,
	}
}

func createPingInfo() pingInfo {
	now := time.Now().UTC().Format("2006-01-02T15:04:05.000Z")
	return pingInfo{
		Seq:       0,
		StartTime: now,
		EndTime:   now,
	}
}

func newDocumentID() string {
	uuid, err := uuid.NewRandom()
	if err != nil {
		return ""
	}
	return uuid.String()
}

func (g GleanEventsLogger) createPing(documentType string, config RequestInfo, payload pingPayload) (ping, error) {
	payloadJson, payloadErr := json.Marshal(payload)
	if payloadErr != nil {
		return ping{}, nil // TODO: define error
		//panic("Unable to marshal payload to json")
	}

	return ping{
		DocumentNamespace: g.AppID,
		DocumentType:      documentType,
		DocumentVersion:   "1",
		DocumentID:        newDocumentID(),
		UserAgent:         config.UserAgent,
		IpAddress:         config.IpAddress,
		Payload:           string(payloadJson),
	}, nil
}

// method called by each ping-specific record method.
// construct the ping, wrap it in the envelope, and print to stdout
func (g GleanEventsLogger) record(
	documentType string,
	requestInfo RequestInfo,
	metrics metrics,
	events []gleanEvent,
) error {
	telemetryPayload := pingPayload{
		ClientInfo: g.createClientInfo(),
		PingInfo:   createPingInfo(),
		Metrics:    metrics,
		Events:     events,
	}

	ping, err := g.createPing(documentType, requestInfo, telemetryPayload)
	if err != nil {
		return err
	}

	envelope := logEnvelope{
		Timestamp: strconv.FormatInt(time.Now().UnixNano(), 10),
		Logger:    "glean",
		Type:      gleanEventMozlogType,
		Fields:    ping,
	}
	envelopeJson, envelopeErr := json.Marshal(envelope)
	if envelopeErr != nil {
		return err
	}
	fmt.Println(string(envelopeJson))
	return nil
}

func newGleanEvent(category, name string, extra map[string]string) gleanEvent {
	return gleanEvent{
		Category:  category,
		Name:      name,
		Timestamp: time.Now().UnixMilli(),
		Extra: extra,
	}
}

type BackendTestEventEvent struct {
    EventFieldString string // A string extra field
    EventFieldQuantity int64 // A quantity extra field
    EventFieldBool bool // A boolean extra field
}

func (e BackendTestEventEvent) gleanEvent() gleanEvent {
    return newGleanEvent(
        "backend",
        "test_event",
        map[string]string{
            "event_field_string": e.EventFieldString,
            "event_field_quantity": fmt.Sprintf("%d", e.EventFieldQuantity),
            "event_field_bool": fmt.Sprintf("%t", e.EventFieldBool),
        },
    )
}

type EventsPingEvent interface {
    isEventsPingEvent()
    gleanEvent() gleanEvent
}

func (e BackendTestEventEvent) isEventsPingEvent() {}

type EventsPing struct {
    MetricName string // Test string metric
    MetricRequestBool bool // boolean
    MetricRequestCount int64 // Test quantity metric
    MetricRequestDatetime time.Time // Test datetime metric
    Event EventsPingEvent // valid event for this ping
}

// Record and submit `events` ping
func (g GleanEventsLogger) RecordEventsPing(
    requestInfo RequestInfo,
    params EventsPing,
) {
	metrics := metrics{
        "string": {
            "metric.name": params.MetricName,
        },
        "boolean": {
            "metric.request_bool": params.MetricRequestBool,
        },
        "quantity": {
            "metric.request_count": params.MetricRequestCount,
        },
        "datetime": {
			"metric.request_datetime": params.MetricRequestDatetime.Format("2006-01-02T15:04:05.000Z"),
        },
    }

    events := []gleanEvent{}
    if params.Event != nil {
		events = append(events, params.Event.gleanEvent())
	}
    g.record("events", requestInfo, metrics, events)
}

// Record and submit `events` ping omitting user request info
func (g GleanEventsLogger) RecordEventsPingWithoutUserInfo(
    params EventsPing,
) {
    g.RecordEventsPing(defaultRequestInfo, params)
}
