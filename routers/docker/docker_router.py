from fastapi import APIRouter, HTTPException, UploadFile, Request, Depends
from typing import Optional, List

from pydantic import BaseModel

from internal.Enums import StatusCodes
import docker
from os import listdir, path, environ, mkdir
from on_startup import create_specific_task, parse_yaml
from tasks_logic.docker_tasks import stop_docker_instance, \
    run_docker_instance, print_error, print_result

router = APIRouter(
    prefix="/docker",
    tags=["docker"],
)
router.client = docker.from_env()
router.abs_path = environ.get("ROOT_PATH")


class Command(BaseModel):
    command: str


def get_yaml_object(abs_path: str):
    for file in listdir(abs_path):
        if file.endswith(".yml") or file.endswith(".yaml"):
            return parse_yaml(path.join(abs_path, file))
    return None


async def check_container_by_serviceName(service_name: str):
    if not any(name in service_name for name in ["redis", "postgres", "rabbitmq", "dramatiq"]):
        # if list(filter(lambda name: service_name in name, list(map(lambda cont: getattr(cont, "name"),
        # router.client.containers.list())))): pretty good line but too slow
        prep_dir = path.join(router.abs_path, service_name)
        if path.isdir(prep_dir):
            container_name = get_yaml_object(prep_dir).service_name
            container = router.client.containers.list(filters={"name": container_name})
            if container:
                return container
    raise HTTPException(status_code=400, detail="Bas service_name")


async def get_andCreate_abs_servicePath(service_name: str):
    if service_name.lower() not in map(lambda name: name.lower(), listdir(router.abs_path)):
        mkdir(path.join(router.abs_path, service_name))
    return path.join(router.abs_path, service_name)


@router.api_route("/get_ids", methods=['GET'])
async def get_docker_ids():
    res_images = [" ".join(["Long id: ", img.id, "Shord id: ", img.short_id]) for img in
                  router.client.containers.list()]
    if res_images:
        return {"status": StatusCodes.OK, "message": StatusCodes(200).value, "data": res_images}


@router.api_route("/info_by_id/{container_id}", methods=['GET', 'POST'])
async def get_docker_info_by_id(container_id: str, logs: bool = True):
    if len(container_id) == 10 or len(container_id) == 64:
        # short_id gain #
        inspect = router.client.containers.get(container_id)
    else:
        raise HTTPException(status_code=404, detail="Container ID length must be 10 or 64 bytes")
    info = {"Name": inspect.image.tags[0], "Ports": inspect.ports, "Status": inspect.status}
    if logs:
        info.update({"Logs": inspect.logs().decode()})
    response = {"status_code": StatusCodes.OK, "message": StatusCodes(200).value, "data": info}
    return response


@router.api_route("/create_service/{service_name}", methods=['POST'])
async def create_new_docker_container(files: List[UploadFile], abs_path=Depends(get_andCreate_abs_servicePath)):
    for file in files:
        with open(path.join(abs_path, file.filename), "wb") as stream:
            stream.write(await file.read())
    message = create_specific_task(abs_path)
    return {"status": StatusCodes.OK, "message": StatusCodes(200).value, "data": "Files created successfully",
            **message}


@router.api_route("/create_templates/{service_name}", methods=["POST"])
async def create_templates(files: List[UploadFile], abs_path=Depends(get_andCreate_abs_servicePath)):
    abs_service_path = path.join(abs_path, "templates")
    if not path.exists(abs_service_path):
        mkdir(abs_service_path)
    for file in files:
        with open(path.join(abs_service_path, file.filename), "wb") as stream:
            stream.write(await file.read())
    return {"status": StatusCodes.OK, "message": StatusCodes(200).value, "data": "Files uploaded successfully"}


@router.api_route("/execute_command/{service_name}", methods=['POST'])
async def execute_command(command: Command, container: dict = Depends(check_container_by_serviceName)):
    result = container[0].exec_run(command.command).output.decode()
    return {"status": StatusCodes.OK, "message": StatusCodes(200).value, "data": result}


@router.api_route("/stop_service/{service_name}", methods=['POST'])
async def stop_service(container: dict = Depends(check_container_by_serviceName)):
    message_id = stop_docker_instance.send_with_options(
        kwargs={"container_id": container[0].short_id,
                "container_name": container[0].name},
        on_failure=print_error,
        on_success=print_result
    ).message_id
    messages = {"stop_logs": message_id}
    return {"status": StatusCodes.OK, "message": StatusCodes(200).value, "data": messages}


@router.api_route("/start_service/{service_name}", methods=['POST'])
async def start_service_byName(service_name: str):
    abs_path = path.join(router.abs_path, service_name)
    if path.isdir(abs_path):
        yaml_object = get_yaml_object(abs_path)
        if yaml_object:
            message_id = run_docker_instance.send_with_options(
                kwargs=yaml_object.__dict__,
                on_failure=print_error,
                on_success=print_result
            ).message_id
            messages = {"run_logs": message_id}
            return {"status": StatusCodes.OK, "message": StatusCodes(200).value, "data": messages}
    raise HTTPException(status_code=400, detail="service not found")


@router.api_route("/service_logs/{service_name}")
async def service_get_logs(container: dict = Depends(check_container_by_serviceName)):
    container_logs = container[0].logs()
    return {"status": StatusCodes.OK, "message": StatusCodes(200).value, "data": container_logs}