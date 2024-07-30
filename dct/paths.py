import os
from urllib.parse import urlparse, urlunparse, ParseResult
from pathlib import Path
from dct.config import Config
from dct.hash import hash_string


async def get_file_names(directory_path: str) -> list[str]:
    return [entry.name for entry in os.scandir(directory_path) if entry.is_file()]


async def get_parsed_url(url: str) -> ParseResult:
    return urlparse(url)


async def get_url_components(url: str) -> tuple[str, str, ParseResult]:
    parsed_url = await get_parsed_url(url)
    base_path, file_name = parsed_url.path.rsplit("/", 1)
    base_url = urlunparse((parsed_url.scheme, parsed_url.netloc, base_path, "", "", ""))
    return base_url, file_name, parsed_url


async def get_image_name(url: str) -> str:
    result = await get_parsed_url(url)
    return Path(result.path).name


async def get_images(config: Config) -> dict | dict[str, str]:
    if not os.path.exists(config.IMAGE_PATH):
        return {}
    image_names = await get_file_names(config.IMAGE_PATH)
    return {
        hash_string(os.path.join(config.IMAGE_FOLDER, image)): os.path.join(
            config.IMAGE_FOLDER, image
        )
        for image in image_names
    }


async def get_config(directory_path: str) -> list[str]:
    files = await get_file_names(directory_path)
    return [file for file in files if file.lower().endswith(".yaml")]
