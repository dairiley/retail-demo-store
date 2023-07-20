from retail_demo_store import RetailDemoStoreStack
from aws_cdk import App

app = App()

RetailDemoStoreStack(app, "retail-demo-store5",
                     description="RETAIL_DS: This deploys the Retail Demo Store reference architecture and workshop notebooks. (uksb-1t80l2nq1)")

app.synth()