from fastapi import APIRouter, HTTPException, UploadFile, Request
from typing import Optional, List
from internal.Enums import StatusCodes
import docker
from os import listdir, path, environ, mkdir
from on_startup import create_specific_task


router = APIRouter(
    prefix="/docker",
    tags=["docker"],
)
router.client = docker.from_env()


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
    print(info)
    if logs:
        info.update({"Logs": inspect.logs().decode()})
    response = {"status_code": StatusCodes.OK, "message": StatusCodes(200).value, "data": info}
    return response


@router.api_route("/create_service/{service_name}", methods=['POST'])
async def create_new_docker_container(files: List[UploadFile], service_name):
    if service_name not in listdir(router.abs_path):
        mkdir(path.join(router.abs_path, service_name))
    abc_path = path.join(router.abs_path, service_name)
    for file in files:
        with open(path.join(abc_path, file.filename), "wb") as stream:
            stream.write(await file.read())
    message = create_specific_task(abc_path)
    return {"status": StatusCodes.OK, "message": StatusCodes(200).value, "data": "Files created successfully", **message}


@router.api_route("/create_templates/{service_name}", methods=["POST"])
async def create_templates(service_name: str, files: List[UploadFile]):
    if service_name not in listdir(router.abs_path):
        raise HTTPException(status_code=415, detail="No service found. To create service visit: "
                                                    "/create_service/{name}".format(name=service_name))
    abs_service_path = path.join(router.abs_path, service_name, "templates")
    if not path.exists(abs_service_path):
        mkdir(abs_service_path)
    for file in files:
        with open(path.join(abs_service_path, file.filename), "wb") as stream:
            stream.write(await file.read())
    return {"status": StatusCodes.OK, "message": StatusCodes(200).value, "data": "Files uploaded successfully"}
