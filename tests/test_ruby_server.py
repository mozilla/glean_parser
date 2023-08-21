# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from pathlib import Path

from glean_parser import ruby_server, translate

ROOT = Path(__file__).parent


def test_parser_rb_server_ping_no_metrics(tmpdir):
    """Test that no files are generated if only ping definitions
    are provided without any metrics."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "mastodon_pings.yaml",
        "ruby_server",
        tmpdir,
    )

    assert all(False for _ in tmpdir.iterdir())


def test_parser_rb_server_metrics_no_ping(tmpdir):
    """Test that no files are generated if only metric definitions
    are provided without pings."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "mastodon_metrics.yaml",
        "ruby_server",
        tmpdir,
    )

    assert all(False for _ in tmpdir.iterdir())


def test_parser_rb_server_metrics_unsupported_type(tmpdir, capfd):
    """Test that no files are generated if only metric definitions
    are provided without pings."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        [
            ROOT / "data" / "mastodon_pings.yaml",
            ROOT / "data" / "all_metrics.yaml",
        ],
        "ruby_server",
        tmpdir,
    )
    out, err = capfd.readouterr()
    assert len(out.split("\n")) == 20


def test_parser_js_server(tmpdir):
    """Test that parser works"""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        [
            ROOT / "data" / "mastodon_pings.yaml",
            ROOT / "data" / "mastodon_metrics.yaml",
        ],
        "ruby_server",
        tmpdir,
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(["server_events.rb"])

    # Make sure string metric made it in
    with (tmpdir / "server_events.rb").open("r", encoding="utf-8") as fd:
        content = fd.read()
        content_1 = """# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/."""
        content_2 = """# frozen_string_literal: true

# requires json, securerandom, and logger libs
require 'json'
require 'securerandom'
require 'logger'

# this will be used for identifying logs that need to forward to Moz Data Pipeline
GLEAN_EVENT_MOZLOG_TYPE = 'glean-server-event'

module GleanHelper
  class MastodonActionServerEvent
    # see comments for init parameter descriptions
    def initialize(application_id:, app_display_version:, app_channel:, user_agent:, ip_address:, action_account_id:, action_controller:, action_method:, action_path:, action_status_code:, action_user_id:)
      @application_id = application_id # string - Application Id to identify application per Glean standards
      @app_display_version = app_display_version # string - Application Id to identify application per Glean standards
      @app_channel = app_channel # string - Application Id to identify application per Glean standards
      @user_agent = user_agent # string - The user agent per Glean standards
      @ip_address = ip_address # sting - The IP address that will be used to decode Geo information and scrubbed at ingestion per Glean standards
      @action_account_id = action_account_id # { string } - Mastodon account id as int associated with the action. This can be from another instance..
      @action_controller = action_controller # { string } - Mastodon application controller class managing the request..
      @action_method = action_method # { string } - API method used for request..
      @action_path = action_path # { string } - API path requested by the call..
      @action_status_code = action_status_code # { string } - API status code returned in response..
      @action_user_id = action_user_id # { string } - Mastodon user id as int associated with the action. These are users local to the Mozilla Social instance..
    end

    def record
      t = Time.now
      t_utc = t.utc
      event_payload = {
        # `Unknown` fields below are required in the Glean schema, however they are not useful in server context.
        'client_info' => {"""
        content_3 = """'first_run_date' => 'Unknown',
          'os' => 'Unknown',
          'os_version' => 'Unknown',
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
        'metrics' => {
          'string' => {
            'action.account_id' => @action_account_id.to_s,
            'action.controller' => @action_controller.to_s,
            'action.method' => @action_method.to_s,
            'action.path' => @action_path.to_s,
            'action.status_code' => @action_status_code.to_s,
            'action.user_id' => @action_user_id.to_s,
          },
        },
      }
      serialized_event_payload = event_payload.to_json
      # This is the message structure that Decoder expects: https://github.com/mozilla/gcp-ingestion/pull/2400.
      ping = {
        'document_namespace' => @application_id,
        'document_type' => 'mastodon-action',
        'document_version' => '1',
        'document_id' => SecureRandom.uuid,
        'user_agent' => @user_agent,
        'ip_address' => @ip_address,
        'payload' => serialized_event_payload,
      }
      # This structure is similar to how FxA currently logs with mozlog: https://github.com/mozilla/fxa/blob/4c5c702a7fcbf6f8c6b1f175e9172cdd21471eac/packages/fxa-auth-server/lib/log.js#L289
      logger = Logger.new($stdout)
      logger_name = 'mastodon-action-glean'
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
    # # add glean server side log for controller calls
    # around_action :emit_server_side_events

# ...

# private
# def emit_server_side_events
  # yield
# ensure
  # GleanHelper::MastodonActionServerEvent.new(
    # application_id:'ruby app name',
    # app_display_version:'ruby app name as `X.X.X`',
    # app_channel:'environment for exampe, `production` or `development`',
    # user_agent:'string or expression',
    # ip_address:'string or expression',
    # action_account_id:'string or expression',
    # action_controller:'string or expression',
    # action_method:'string or expression',
    # action_path:'string or expression',
    # action_status_code:'string or expression',
    # action_user_id:'string or expression',
  # ).record
# end
# end"""
        assert content_1.strip().replace(" ", "").replace("\n", "").replace(
            "\\n", ""
        ) in content.strip().replace(" ", "").replace("\n", "").replace("\\n", "")
        assert content_2.strip().replace(" ", "").replace("\n", "").replace(
            "\\n", ""
        ) in content.strip().replace(" ", "").replace("\n", "").replace("\\n", "")
        assert content_3.strip().replace(" ", "").replace("\n", "").replace(
            "\\n", ""
        ) in content.strip().replace(" ", "").replace("\n", "").replace("\\n", "")
