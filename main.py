from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from ujson import loads, dumps
from typing import Dict
import uvicorn

from os import environ
from uuid import uuid5
from on_startup import create_tasks

from internal.Enums import StatusCodes
from routers.docker.docker_router import router as docker_router
from routers.queue.dramatiq_router import router as dramatiq_router

app = FastAPI()
app.include_router(docker_router)
app.include_router(dramatiq_router)


@app.on_event("startup")
async def start_app():
    dramatiq_router.custom_messages = create_tasks()
    if environ.get("DEBUG", True) == 'True':
        print(f"[+] Docker router got messages: {dramatiq_router.custom_messages}")
        docker_router.abs_path = "/Users/d.saschenko/PycharmProjects/diplomSiem/internal/Services"
    else:
        docker_router.abs_path = environ.get("ROOT_PATH")


@app.api_route("/health", methods=["GET"])
async def index() -> Dict:
    return {"message": StatusCodes.OK.message, "status": StatusCodes.OK.value}


@app.get("/test")
async def test():
    return HTMLResponse("""
    <body>

<h1>The input multiple attribute</h1>

<p>Try selecting more than one file when browsing for files.</p>

<!-- make sure the attribute enctype is set to multipart/form-data -->
<form method="post" enctype="multipart/form-data" action="/docker/create_service/rivenService">
    <p>
        <label>Add files (multiple): </label><br/>
        <input type="file" name="files" multiple="multiple"/>
    </p>

    <p>
        <input type="submit"/>
    </p>
</form>

</body>""")


if __name__ == '__main__':
    if environ.get("DEBUG", True) == 'True':
        uvicorn.run("main:app", host="0.0.0.0", reload=True, port=8081)
