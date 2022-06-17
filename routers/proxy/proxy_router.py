from fastapi import APIRouter, HTTPException
from fastapi import Depends, Request
from aiohttp import TCPConnector, ClientSession
import docker
from os import environ, path, listdir
from on_startup import parse_yaml
from pydantic import ValidationError
from internal.Enums import StatusCodes

import asyncpg

router = APIRouter(
    prefix="/proxy",
    tags=["proxy", "forward"]
)


async def get_docker_client():
    return docker.from_env()


async def return_props(service_name: str, request: Request):
    # TODO: refactor + add utils.py
    if any(service in service_name.strip().lower() for service in
           ["postgres", "rabbitmq", "ampq", "api-backend", "redis"]):
        raise HTTPException(status_code=401, detail="No permissions")
    abs_path = path.join(environ.get("SERVICES_DIR"), service_name)
    try:
        yaml_file = None
        for file in listdir(abs_path):
            if file.endswith(".yml") or file.endswith(".yaml"):
                yaml_file = file
        if not yaml_file:
            raise HTTPException(status_code=500, detail="This service is not configured with .yaml/.yml file")
        parsed_data = parse_yaml(path.join(abs_path, yaml_file), proxy=True)
        if not any(parsed_data.service_name.strip().lower() in container.name for container in
                   (await get_docker_client()).containers.list()):
            raise HTTPException(status_code=404, detail="Service not found")
        if not parsed_data.proxy_path:
            parsed_data.proxy_path = "/logging"
    except ValidationError:
        # That's mean that user specified servername but proxy_path contain bad letters
        raise HTTPException(status_code=406, detail="Bad characters in proxy_path, or proxy_servername not specified")
    else:
        # connector = TCPConnector(verify_ssl=False, use_dns_cache=False, keepalive_timeout=5)
        # async with ClientSession(connector=connector) as rq:
        async with ClientSession() as rq:
            headers, body = request.headers, (await request.body()).decode()
            async with rq.get(
                    f"http://{parsed_data.proxy_servername}:{parsed_data.service_port}{parsed_data.proxy_path}",
                    json=body) as response:
                if 199 < response.status < 400:
                    debug_info = {}
                    if environ.get("DEBUG") == 'true':
                        debug_info["response_data"] = await response.text()
                    return {"status": StatusCodes.OK, "message": StatusCodes(200).value, **debug_info}


@router.api_route("/sendto/{service_name:str}")
async def proxy_request(kwarg_path: dict = Depends(return_props)) -> dict:
    return kwarg_path


# {database: {database_name: {table_name: {col_1:[data], col_2:[data]}}}}
# TODO: make aio connection
async def json_parse(nasty_json: dict):
    first_key_obj = lambda obj: obj[list(obj.keys())[0]]
    if nasty_json.get('database'):
        database: dict = nasty_json['database']
        if len(database.keys()) == 1:
            database_name: dict = first_key_obj(database)
            if len(database_name.keys()) == 1:
                table_name: dict = first_key_obj(database_name)
                for col_name, col_values in table_name.items():
                    print(col_values, col_name)


@router.api_route("/database", methods=['POST'])
async def save_to_database(request: Request,
                           nasty_json: dict = {"database": {"database_name": {"table_name": {"col_1": [1, 2]}}}}):
    # TODO: split to utils
    if not request.headers.get('Content-type') and request.headers[
        'Content-type'] != 'application/json' or nasty_json is None:
        return HTTPException(status_code=400,
                             detail=f"Bad content type, use application/json instead of {request.headers['Content-type']}")
    await json_parse(nasty_json)
