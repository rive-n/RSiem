from fastapi import APIRouter, HTTPException, UploadFile, Request
from typing import Optional, List
from internal.Enums import StatusCodes
from routers.docker.models import FileModel
import docker
from os import listdir, path, environ, mkdir


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
async def create_new_docker_container(request: Request, files: List[UploadFile], service_name):
    # TODO: validator or middleware
    # TODO: refactor
    if not request.headers.get("Content-type") and (request.headers["Content-type"] != "application/json" or
                                                    request.headers['Content-type'] != "multipart/form-data"):
        raise HTTPException(status_code=415, detail="Bad content type")
    if environ.get("DEBUG", True):
        abc_path = "/Users/d.saschenko/PycharmProjects/diplomSiem/internal/Services"
    else:
        abc_path = environ.get("ROOT_PATH")
    if service_name not in listdir(abc_path): mkdir(abc_path)
    abc_path = path.join(abc_path, service_name)
    for file in files:
        with open(path.join(abc_path, file.filename), "wb") as stream:
            stream.write(await file.read())
    return {"status": StatusCodes.OK, "message": StatusCodes(200).value, "data": "Files created successfully"}
