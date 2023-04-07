from aws_cdk import (
    Stack, CfnOutput, RemovalPolicy, Duration,
    aws_apigateway as apigateway,
    aws_lambda as lambda_,
    aws_s3 as s3,
    aws_iam as iam
)
from constructs import Construct

class SpAwsLineChatGptStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bucket = s3.Bucket(self, "aws-scu-dlab")

        lambda_role = iam.Role(
            self,"aws-line-chatgpt-role",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("lambda.amazonaws.com"),
                iam.ServicePrincipal("dynamodb.amazonaws.com")
            )
        )

        # handler.add_layers("arn:aws:lambda:us-east-1:274251673384:layer:AWS-LINE-ChatGPT-Layer:1")
        lambda_layer = lambda_.LayerVersion(
            self, "aws-line-chatgpt-layer",
            removal_policy=RemovalPolicy.RETAIN,
            code=lambda_.Code.from_asset("python.zip"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_9],
            compatible_architectures=[lambda_.Architecture.X86_64, lambda_.Architecture.ARM_64]
        )

        handler = lambda_.Function(
            self, "aws-line-chatgpt-lambda",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset("src"),
            handler="lambda_function.lambda_handler",
            role=lambda_role,
            layers=[lambda_layer],
            environment={ "BUCKET" : bucket.bucket_name },
            timeout=Duration.seconds(30)
        )

        bucket.grant_read_write(handler)

        api = apigateway.RestApi(
            self, "aws-line-chatgpt-api",
            rest_api_name="aws-line-chatgpt-api-gateway",
            description="LINE Webhook Endpoint for ChatGPT"
        )

        get_widgets_integration = apigateway.LambdaIntegration(
            handler,
            request_templates={"application/json": '{ "statusCode": "200" }'}
        )

        api.root.add_method("POST", get_widgets_integration)

        CfnOutput(self,"API Endpoint",value=api.url)

