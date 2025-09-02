import typing

from slack_sdk import WebClient
from slack_sdk.models.blocks.blocks import Block
from slack_sdk.web.slack_response import SlackResponse

from main import config


class MapswipeSlackInitializationException(Exception): ...


class MapswipeSlack:
    class MapswipeSlackMessageArgumentType(typing.TypedDict):
        text: str
        blocks: typing.Sequence[dict | Block] | None

    def __init__(self):
        slack_config = config.Slack.load_slack_config()
        if slack_config.enabled is False:
            raise MapswipeSlackInitializationException
        self.client = WebClient(token=slack_config.token)
        self.channel = slack_config.channel
        self.bot_name = slack_config.bot_name

    def send_slack_message(
        self,
        text: str | None = None,
        blocks: typing.Sequence[dict | Block] | None = None,
        thread_ts: str | None = None,
        reply_broadcast: bool = True,
    ) -> SlackResponse:
        return self.client.chat_postMessage(
            channel=self.channel,
            username=self.bot_name,
            blocks=blocks,
            text=text,
            thread_ts=thread_ts,
            unfurl_links=False,
            reply_broadcast=reply_broadcast,
        )
