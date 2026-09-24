import os
import json
import logging
from google.adk.cli.service_registry import get_service_registry
from google.adk.memory.vertex_ai_memory_bank_service import VertexAiMemoryBankService

logger = logging.getLogger("google_adk.app.services")

DEPLOYMENT_METADATA_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "deployment_metadata.json"
)
if not os.path.exists(DEPLOYMENT_METADATA_PATH):
    DEPLOYMENT_METADATA_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "deployment_metadata.json"
    )

def _get_resource_info():
    if os.path.exists(DEPLOYMENT_METADATA_PATH):
        try:
            with open(DEPLOYMENT_METADATA_PATH, "r") as f:
                data = json.load(f)
                res_id = data.get("remote_agent_runtime_id")
                if res_id and "reasoningEngines" in res_id:
                    parts = res_id.split("/")
                    return parts[1], parts[3], parts[5]
        except Exception as e:
            logger.warning("Could not load deployment metadata: %s", e)
    return "qwiklabs-gcp-03-5bec0b757af4", "us-east4", "6314965869294256128"

def memory_service_factory(uri: str, **kwargs):
    project, location, agent_engine_id = _get_resource_info()
    return VertexAiMemoryBankService(
        project=project,
        location=location,
        agent_engine_id=agent_engine_id,
    )

registry = get_service_registry()
registry.register_memory_service("memory", memory_service_factory)
