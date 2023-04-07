import aws_cdk as core
import aws_cdk.assertions as assertions

from sp_aws_line_chat_gpt.sp_aws_line_chat_gpt_stack import SpAwsLineChatGptStack

# example tests. To run these tests, uncomment this file along with the example
# resource in sp_aws_line_chat_gpt/sp_aws_line_chat_gpt_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = SpAwsLineChatGptStack(app, "sp-aws-line-chat-gpt")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
