from enum import Enum


class StatusCodes(bytes, Enum):
    def __new__(cls, status, message):
        bytes_object = bytes.__new__(cls, status)
        bytes_object._value_ = status
        bytes_object.message = message
        return bytes_object

    OK = (200, "request to {endpoint} is successful")
    REDIRECT = (302, "redirecting to: {endpoint}")
    ACCESS = (401, "you have no access to: {endpoint}, try to use [authorization] header")
    NOT_FOUND = (404, "{endpoint} not found. Try to read docs first: /docs")
    SERVER_ERROR = (500, "Server can't handle your request. Error trace: {trace}")


if __name__ == '__main__':
    print(StatusCodes(200).value)