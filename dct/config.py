import os
from logging import Logger
from dataclasses import dataclass, field
from dct.logging import set_log


@dataclass(frozen=True)
class Config:
    INPUT_DIRECTORY: str = os.getcwd()
    OUTPUT_DIRECTORY: str = os.getcwd()
    PROCESS_DISCORD_LINKS: bool = False
    TOKEN: str = ""
    BASE64_TO_IMAGE: bool = False
    OLD_PREFIX: str = ""
    NEW_PREFIX: str = ""
    UPDATE_PREFIXES: bool = False
    DOWNLOAD_IMAGES: bool = False
    RATE_LIMIT: int = 2
    IMAGE_FOLDER: str = "images"
    IMAGE_QUALITY: int = 90
    OVERWRITE_IMAGES: bool = False
    PROJECT_FILE: str = "project.json"
    OUTPUT_FILE: str = "project_new.json"
    MINIFY: bool = False
    DISABLE_IMAGES: bool = False
    DOWNLOAD_RATE_LIMIT: int = 5
    IMAGE_FORMAT: str = "WEBP"
    CONVERT_IMAGES: bool = False
    IMAGE_TO_BASE64: bool = False
    SHOW_CONFIG: bool = False
    PROJECT_URL: str = ""
    SESSION_TIMEOUT: int = 600
    LOG_FILE: str = "dct_log"

    PROJECT_PATH: str = field(init=False)
    IMAGE_PATH: str = field(init=False)
    OUTPUT_PATH: str = field(init=False)
    LOGFILE_PATH: str = field(init=False)
    LOGGER: Logger = field(init=False)

    def __post_init__(self):
        object.__setattr__(
            self, "PROJECT_PATH", os.path.join(self.INPUT_DIRECTORY, self.PROJECT_FILE)
        )
        object.__setattr__(
            self, "IMAGE_PATH", os.path.join(self.OUTPUT_DIRECTORY, self.IMAGE_FOLDER)
        )
        object.__setattr__(
            self, "OUTPUT_PATH", os.path.join(self.OUTPUT_DIRECTORY, self.OUTPUT_FILE)
        )
        object.__setattr__(
            self,
            "LOGFILE_PATH",
            os.path.join(self.OUTPUT_DIRECTORY, f"{self.LOG_FILE}.txt"),
        )
        object.__setattr__(self, "LOGGER", set_log(self.LOGFILE_PATH))
