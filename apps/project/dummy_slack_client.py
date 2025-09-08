import typing

from slack_sdk.models.blocks.blocks import Block
from slack_sdk.web.slack_response import SlackResponse

from utils.slack import MapswipeSlack


class MapswipeSlackMock(MapswipeSlack):
    slack_thread_ts_counter = 0

    class DummySlackClient:
        def chat_postMessage(self, **kwargs):
            # Return a fake Slack response
            return {"ok": True, "ts": "FAKE_TS"}

        def chat_update(self, **kwargs):
            return {"ok": True, "ts": "FAKE TS"}

    @typing.override
    def __init__(self):
        self.client = self.DummySlackClient()

    @typing.override
    def send_slack_message(
        self,
        text: str | None = None,
        blocks: str | typing.Sequence[dict | Block] | None = None,
        thread_ts: str | None = None,
        reply_broadcast: bool = True,
    ) -> SlackResponse:
        self.slack_thread_ts_counter += 1
        return typing.cast(
            "SlackResponse",
            {"ts": f"{self.slack_thread_ts_counter}.7890"},
        )

    @typing.override
    def update_slack_message(
        self,
        ts: str,
        text: str | None = None,
        blocks: typing.Sequence[dict | Block] | None = None,
    ) -> SlackResponse:
        self.slack_thread_ts_counter += 1
        return typing.cast(
            "SlackResponse",
            {"ts": f"{self.slack_thread_ts_counter}.7890"},
        )
