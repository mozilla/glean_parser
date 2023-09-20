# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# AUTOGENERATED BY glean_parser v0.1.dev1004+g4822435. DO NOT EDIT.

# frozen_string_literal: true

# requires json, securerandom, and logger libs
require 'json'
require 'securerandom'
require 'logger'
require 'rbconfig'


# this will be used for identifying logs that need to forward to Moz Data Pipeline
GLEAN_EVENT_MOZLOG_TYPE = 'glean-server-event'

module OS
  def self.name
    case RbConfig::CONFIG['host_os']
    
    when /linux/
      'Linux'
    when /darwin/
      'OS X'
    when /mswin|mingw32|windows/
      'Windows'
    when /solaris/
      'Solaris'
    when /bsd/
      'BSD'
    else
      RbConfig::CONFIG['host_os']
    end
  end
  def self.version
    version = RbConfig::CONFIG['build_os'].match('\d{1,2}\.*\d{0,2}\.*\d{0,3}').to_s
    if !version.nil?
        version.to_s
    else
        'Unknown'
    end
  end
end

module GleanHelper
  class MastodonBackendServerEvent
    # see comments for init parameter descriptions
    def initialize(application_id:, app_display_version:, app_channel:, user_agent:, ip_address:, event_extra)
      @application_id = application_id # string - Application Id to identify application per Glean standards
      @app_display_version = app_display_version # string - Application Id to identify application per Glean standards
      @app_channel = app_channel # string - Application Id to identify application per Glean standards
      @user_agent = user_agent # string - The user agent per Glean standards
      @ip_address = ip_address # string - The IP address that will be used to decode Geo information and scrubbed at ingestion per Glean standards
      @event_extra = event_extra # string - JSON blob containing the backend event payload
    end

    def record
      t = Time.now
      t_utc = t.utc
      event_payload = {
        # `Unknown` fields below are required in the Glean schema, however they are not useful in server context.
        'client_info' => {
          'telemetry_sdk_build' => 'glean_parser v0.1.dev1004+g4822435',
          'first_run_date' => 'Unknown',
          'os' => OS.name,
          'os_version' => OS.version,
          'architecture' => 'Unknown',
          'app_build' => 'Unknown',
          'app_display_version' => @app_display_version,
          'app_channel' => @app_channel,
        },
        'ping_info' => {
          'seq' => 0, # this is required, however doesn't seem to be useful in server context.
          'start_time' => t_utc,
          'end_time' => t_utc,
        },
        'event' => 'mastodon.backend'
        'event_timestamp' => t_utc
        'event_extra' => event_extra,
      }
      serialized_event_payload = event_payload.to_json
      # This is the message structure that Decoder expects: https://github.com/mozilla/gcp-ingestion/pull/2400.
      ping = {
        'document_namespace' => @application_id,
        'document_type' => 'events',
        'document_version' => '1',
        'document_id' => SecureRandom.uuid,
        'user_agent' => @user_agent,
        'ip_address' => @ip_address,
        'payload' => serialized_event_payload,
      }
      # This structure is similar to how FxA currently logs with mozlog: https://github.com/mozilla/fxa/blob/4c5c702a7fcbf6f8c6b1f175e9172cdd21471eac/packages/fxa-auth-server/lib/log.js#L289
      logger = Logger.new($stdout)
      logger_name = 'events-glean'
      logger.formatter = proc do |severity, datetime, _progname, msg|
        date_format = datetime.to_i
        "#{JSON.dump(Timestamp: date_format.to_s, Logger: logger_name.to_s, Type: GLEAN_EVENT_MOZLOG_TYPE.to_s, Severity: severity.ljust(5).to_s, Pid: Process.pid.to_s, Fields: msg)}\n"
      end
      logger.info(ping)
    end
  end
end

# use the following examples for adding the loggers to your controller
# class ApplicationController < ActionController::Base
    # add glean server side log for controller calls
    # around_action :emit_server_side_events

# ...

# logic to create event extra json string

#...

# private
# def emit_server_side_events
  # yield
# ensure
  # GleanHelper::CategoryTypeServerEvent.new(
    # application_id:'ruby app name',
    # app_display_version:'ruby app name as `X.X.X`',
    # app_channel:'environment for exampe, `production` or `development`',
    # user_agent:'string or expression',
    # ip_address:'string or expression',
    # event_extra: 'json_string'
  # ).record
# end
# end
