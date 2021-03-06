from os import path, environ, scandir, getcwd
from tasks_logic.docker_tasks import print_error, print_result, \
    run_docker_instance, build_docker_instance, redis_backend
from pydantic import BaseModel
from pydantic.main import ModelMetaclass
from pydantic import ValidationError, validator
from typing import Optional
import yaml
import io


class YamlMeta(ModelMetaclass):
    def __new__(mcs, name, bases, namespaces, *args, **kwargs):
        annotations = namespaces.get('__annotations__', {})
        for base in bases:
            annotations.update(base.__annotations__)
        return super().__new__(mcs, name, bases, namespaces, **kwargs)

    def __call__(self, *args, **kwargs):
        merge_kwargs = {}
        for arg in kwargs:
            if arg.startswith("port") or arg.startswith("name"):
                print(f"[!] Seems like configuration error: {arg}, trying to make: service_{arg}")
                merge_kwargs.update({f"service_{arg}": kwargs[arg]})
        kwargs.update(merge_kwargs)
        return ModelMetaclass.__call__(self, *args, **kwargs)


class ParsedYaml(BaseModel):
    service_name: str
    service_port: int
    dockerfile: str
    full_path: str

    @validator("service_name")
    def validate_service_name_field(cls, v):
        return v.lower()


class ParsedYamlProxy(ParsedYaml):
    proxy_servername: str
    proxy_path: Optional[str]

    @validator("proxy_path")
    def validate_proxy_path_field(cls, v):
        if any(letter in v for letter in ["..", "\0", "\n", "\t"]):
            raise ValidationError("Bad chars in proxy path")
        return v


class UpdatedYamlData(ParsedYaml, metaclass=YamlMeta):
    pass


class UpdatedParsedDataProxy(ParsedYamlProxy, metaclass=YamlMeta):
    pass


def parse_yaml(full_path: str, proxy: bool = False) -> UpdatedYamlData:
    if path.isfile(full_path):
        with io.open(full_path) as stream:
            try:
                file_data = yaml.safe_load(stream)
                print("data:", file_data)
                if file_data.get("service"):
                    file_data["service"]["full_path"] = path.dirname(path.abspath(full_path))
                    return UpdatedYamlData(**file_data["service"]) if not \
                        proxy else UpdatedParsedDataProxy(**file_data["service"])
                raise
            except Exception as e:
                print("Fucking what:", e)


def create_tasks():
    objects = []
    if environ.get("SERVICES_DIR"):
        dir = environ["SERVICES_DIR"]
    else:
        dir = "/Users/d.saschenko/PycharmProjects/diplomSiem/internal/Services"

    for module in filter(path.isdir, scandir(
            path.join(getcwd(), dir))):
        for file in scandir(path.join(getcwd(), dir, module.name)):
            if file.name.endswith(".yaml") or file.name.endswith(".yml"):
                objects.append(parse_yaml(path.join(getcwd(), dir, module.name, file.name)))
    if objects:
        messages = {}
        for obj in objects:
            messages[obj.service_name] = {"build_logs": "", "run_logs": ""}
            print("Path:", obj.full_path)
            message = build_docker_instance.send_with_options(
                kwargs=obj.__dict__,
                on_failure=print_error,
                on_success=print_result
            )
            messages[obj.service_name]["build_logs"] = message.message_id
            message = run_docker_instance.send_with_options(
                kwargs=obj.__dict__,
                on_failure=print_error,
                on_success=print_result
            )
            messages[obj.service_name]["run_logs"] = message.message_id
        return messages
    else:
        raise ValueError("Nothing found, please check rights or create files.")


def create_specific_task(service_dir: str):
    configs = []
    for file in scandir(service_dir):
        if file.name.endswith(".yml") or file.name.endswith(".yaml"):
            configs.append(parse_yaml(path.join(service_dir, file.name)))
    if configs:
        messages = {}
        for obj in configs:
            messages[obj.service_name] = {"build_logs": "", "run_logs": ""}
            message = build_docker_instance.send_with_options(
                kwargs=obj.__dict__,
                on_failure=print_error,
                on_success=print_result
            )
            messages[obj.service_name]["build_logs"] = message.message_id
            message = run_docker_instance.send_with_options(
                kwargs=obj.__dict__,
                on_failure=print_error,
                on_success=print_result
            )
            messages[obj.service_name]["run_logs"] = message.message_id
        return messages
    else:
        raise ValueError("Nothing found, please check rights or create files.")


if __name__ == '__main__':
    create_tasks()
