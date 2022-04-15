from fastapi import APIRouter
from internal.Enums import StatusCodes
from dramatiq.results import ResultMissing
from tasks_logic.docker_tasks import run_docker_instance, build_docker_instance

router = APIRouter(
    prefix="/dramatiq",
    tags=["dramatiq", "broker"]
)

@router.api_route("/on_startup")
def get_info_about_startup():
    messages = {}
    for service_dockerfile in router.custom_messages:
        for logs_type in router.custom_messages[service_dockerfile]:
            if logs_type == "build_logs":
                messages.update({service_dockerfile: {logs_type: build_docker_instance.message().copy(
                    message_id=router.custom_messages[service_dockerfile][logs_type])}})
            else:
                messages.update({service_dockerfile: {logs_type: run_docker_instance.message().copy(
                    message_id=router.custom_messages[service_dockerfile][logs_type])}})
            print(router.custom_messages[service_dockerfile][logs_type])
            try:
                message = messages[service_dockerfile][logs_type].get_result()
            except ResultMissing:
                message = "Not ready or already expired"
            messages[service_dockerfile][logs_type] = message
    return {"status": StatusCodes.OK, "message": StatusCodes(200).value, "data": messages}
