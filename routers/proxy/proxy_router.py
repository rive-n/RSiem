from fastapi import APIRouter, HTTPException
from fastapi import Depends, Request
from aiohttp import TCPConnector, ClientSession
import docker
from os import environ, path
from on_startup import parse_yaml
from pydantic import ValidationError

router = APIRouter(
    prefix="/proxy",
    tags=["proxy", "forward"]
)


async def get_docker_client():
    return docker.from_env()


async def return_props(service_name: str, request: Request):
    #TODO: parse JSON body + headers and make request with em
    if any(service in service_name.strip().lower() for service in ["postgres", "rabbitmq", "ampq", "api-backend", "redis"]):
        raise HTTPException(status_code=401, detail="No permissions")
    if any(service_name in container.name for container in (await get_docker_client()).containers.list()):
        abs_path = path.join(environ.get("SERVICES_DIR"), service_name)
        try:
            parsed_data = parse_yaml(abs_path)
            if not parsed_data.proxy_path:
                parsed_data.proxy_path = "/logging"
        except ValidationError:
            # That's mean that user specified servername but proxy_path contain bad letters
            raise HTTPException(status_code=406, detail="Bad characters in proxy_path, please change config")
        connector = TCPConnector(verify_ssl=False, use_dns_cache=False, keepalive_timeout=5)
        async with ClientSession(connector=connector) as rq:
            async with rq.get(f"http://{parsed_data.proxy_servername}/{parsed_data.proxy_path}") as response:
                pass
        return service_name
    else:
        raise HTTPException(status_code=404, detail="Service not found")


@router.api_route("/sendto/{service_name:str}")
async def proxy_request(kwarg_path: dict = Depends(return_props)) -> dict:
    return kwarg_path
