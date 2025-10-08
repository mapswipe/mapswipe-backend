import json
import logging
import typing

from slack_sdk import WebClient
from slack_sdk.models.blocks.blocks import Block

from main import config

logger = logging.getLogger(__name__)


class MapswipeSlack:
    client: WebClient | None
    channel: str

    class MapswipeSlackMessageArgumentType(typing.TypedDict):
        text: str
        blocks: typing.Sequence[dict | Block] | None  # type: ignore[reportMissingTypeArgument]

    def __init__(self):
        slack_config = config.Slack.load_slack_config()
        if slack_config.enabled is False:
            self.channel = "mock_channel"
            self.client = None
            return

        self.client = WebClient(token=slack_config.token)
        self.channel = slack_config.channel

    def send_slack_message(
        self,
        text: str | None = None,
        blocks: typing.Sequence[dict | Block] | None = None,  # type: ignore[reportMissingTypeArgument]
        thread_ts: str | None = None,
        reply_broadcast: bool = False,
    ) -> str | None:
        if not self.client:
            logger.info("Sending message on slack for thread %s", thread_ts)
            logger.info(
                json.dumps(
                    {
                        "text": text,
                        "blocks": blocks,
                    },
                ),
            )
            return None

        res = self.client.chat_postMessage(
            channel=self.channel,
            blocks=blocks,
            text=text,
            thread_ts=thread_ts,
            unfurl_links=False,
            reply_broadcast=reply_broadcast,
        )
        return typing.cast("str", res.get("ts"))

    def update_slack_message(
        self,
        ts: str,
        text: str | None = None,
        blocks: typing.Sequence[dict | Block] | None = None,  # type: ignore[reportMissingTypeArgument]
    ) -> str | None:
        if not self.client:
            logger.info("Sending message on slack for thread %s", ts)
            logger.info(
                json.dumps(
                    {
                        "text": text,
                        "blocks": blocks,
                    },
                ),
            )
            return None

        res = self.client.chat_update(
            channel=self.channel,
            ts=ts,
            text=text,
            blocks=blocks,
        )
        return typing.cast("str", res.get("ts"))
