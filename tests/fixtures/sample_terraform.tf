resource "aws_bedrockagent_agent" "test_agent" {
  agent_name       = "test-agent"
  foundation_model = "anthropic.claude-3-sonnet-20240229-v1:0"
}

resource "aws_sagemaker_endpoint" "test_endpoint" {
  name = "test-llm-endpoint"
  endpoint_config_name = "test-config"
}
