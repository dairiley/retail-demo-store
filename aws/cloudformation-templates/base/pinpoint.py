from aws_cdk import (
    Stack,
    Duration,
    aws_pinpoint as pinpoint
)
from constructs import Construct

class PinpointStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.pinpoint = pinpoint.CfnApp(self, "PinpointApp",
                                        name="retaildemostore")
