import typing

from slack_sdk.models.blocks.blocks import Block
from slack_sdk.webhook import WebhookClient, WebhookResponse

from main import config


class MapswipeSlackInitializationError(Exception): ...


class MapswipeSlack:
    class MapswipeSlackMessageArgumentType(typing.TypedDict):
        text: str
        blocks: typing.Sequence[Block] | None

    def __init__(self):
        slack_config = config.Slack.load_slack_config()
        if slack_config.enabled is False:
            raise MapswipeSlackInitializationError
        self.webhook = WebhookClient(url=slack_config.webhook_url)
        self.bot_name = slack_config.bot_name

    def send_slack_message(
        self,
        text: str | None = None,
        blocks: typing.Sequence[Block] | None = None,
    ) -> WebhookResponse:
        return self.webhook.send(
            blocks=blocks,
            text=text,
        )
