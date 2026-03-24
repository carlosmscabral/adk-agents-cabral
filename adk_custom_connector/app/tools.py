from google.adk.tools.application_integration_tool.application_integration_toolset import ApplicationIntegrationToolset

# The ApplicationIntegrationToolset gives your agent secure and governed access to enterprise applications 
# using Integration Connectors. Here, it is configured to use a Jira connection.
# Note: You can optionally provide an authentication scheme (`auth_scheme` and `auth_credential`) 
# for dynamic OAuth2, or a service account key string via `service_account_json`. 
# In this demo, it assumes default credentials environment.
connector_tool = ApplicationIntegrationToolset(
    project="vibe-cabral",
    location="us-central1",
    connection="jira-carlosmscabral",
    # Provide an empty list to allow all actions on 'Issue' entity (e.g., LIST, CREATE, GET)
    # If the exact operations aren't known or to limit scope, they can be explicitly listed.
    entity_operations={"Issues": []}, 
    actions=[], # Optional: specific actions if needed 
    tool_name_prefix="jira_",
    tool_instructions="Use this tool to interact with Jira. You can list, create, and get Jira issues."
)
