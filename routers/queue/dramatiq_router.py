from fastapi import APIRouter
from uuid import UUID
import enum
from internal.Enums import StatusCodes
from dramatiq.results import ResultMissing
from tasks_logic.docker_tasks import run_docker_instance, build_docker_instance
import tasks_logic.docker_tasks
from on_startup import create_tasks

router = APIRouter(
    prefix="/dramatiq",
    tags=["dramatiq", "broker"]
)
router.custom_messages = create_tasks()


@router.api_route("/on_startup")
async def get_info_about_startup():
    messages = {}
    for service_dockerfile in router.custom_messages:
        for logs_type in router.custom_messages[service_dockerfile]:
            if logs_type == "build_logs":
                messages.update({service_dockerfile: {logs_type: build_docker_instance.message().copy(
                    message_id=router.custom_messages[service_dockerfile][logs_type])}})
            else:
                messages.update({service_dockerfile: {logs_type: run_docker_instance.message().copy(
                    message_id=router.custom_messages[service_dockerfile][logs_type])}})
            try:
                message = messages[service_dockerfile][logs_type].get_result()
            except ResultMissing:
                message = "Not ready or already expired"
            messages[service_dockerfile][logs_type] = message
    return {"status": StatusCodes.OK, "message": StatusCodes(200).value, "data": messages}


class LogType(str, enum.Enum):
    build_logs = "build_docker_instance"
    run_logs = "run_docker_instance"
    stop_logs = 'stop_docker_instance'


@router.api_route("/get_task_info/{task_id}")
async def get_task_info(task_id: UUID, log_type: LogType):
    try:
        func = getattr(tasks_logic.docker_tasks, log_type)
        message = func.message().copy(message_id=task_id)
        message = message.get_result()
        error = False
    except ResultMissing:
        message = "Result is missing"
        error = True
    return {"status": StatusCodes.OK, "message":message, "error": error}
