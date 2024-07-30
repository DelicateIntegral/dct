import json
from typing import Any, Callable
from dct.console import console
from dct.config import Config
from dct.hash import hash_string
from dct.paths import get_url_components


def read_json(file_path: str) -> Any:
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(config: Config, json_data: Any) -> None:
    with open(config.OUTPUT_PATH, "w", encoding="utf-8") as f:
        indent = None if config.MINIFY else 2
        separators = (",", ":") if config.MINIFY else None
        if config.MINIFY:
            console.print("[blue]Minifying JSON...")
        console.print("[blue]Writing Output JSON...")
        json.dump(json_data, f, indent=indent, separators=separators, sort_keys=True)


async def traverse_json(
    data: Any, processing_function: Callable, *args: tuple, **kwargs: dict[str, Any]
) -> Any:
    if isinstance(data, dict):
        await processing_function(data, *args, **kwargs)
        for value in data.values():
            if isinstance(value, (dict, list)):
                await traverse_json(value, processing_function, *args, **kwargs)
    elif isinstance(data, list):
        for item in data:
            await traverse_json(item, processing_function, *args, **kwargs)


async def get_urls(json_data: Any, DISCORD_MODE: bool = False):
    urls = {}

    async def url_get_function(data: dict) -> None:
        image = data.get("image", "").strip()
        if image.startswith("http") and not image.startswith("data:image"):
            hash_key = hash_string(image)
            if DISCORD_MODE and "discordapp" in image:
                urls[hash_key] = image
            elif not DISCORD_MODE and "discordapp" not in image:
                urls[hash_key] = image

    await traverse_json(json_data, url_get_function)
    return urls


async def get_remote_urls(data: Any, config: Config) -> dict:
    urls = {}

    async def url_get_function(data: dict, project_url: str) -> None:
        image = data.get("image", "").strip()
        if not image.startswith(("data:image", "http")) and image:
            hash_key = hash_string(image)
            base_url, _, _ = await get_url_components(project_url)
            urls[hash_key] = f"{base_url}/{image}"

    await traverse_json(data, url_get_function, config.PROJECT_URL)
    return urls


async def get_base64_strings(json_data: Any) -> dict:
    base64_strings = {}

    async def base64_string_function(data: dict) -> None:
        image = data.get("image", "").strip()
        if image.startswith("data:image"):
            hash_key = hash_string(image)
            base64_strings[hash_key] = image

    await traverse_json(json_data, base64_string_function)
    return base64_strings


async def update_urls(json_data: Any, url_map: dict) -> Any:
    async def url_update_function(data: dict) -> None:
        image = data.get("image", "").strip()
        hash_key = hash_string(image)
        if hash_key in url_map:
            data["image"] = url_map[hash_key].strip()

    await traverse_json(json_data, url_update_function)
    return json_data


async def update_prefixes(data: Any, config: Config) -> Any:
    console.print("[blue] Updating Prefixes...")

    async def prefix_update_function(data: dict) -> None:
        image = data.get("image", "")
        if image.startswith(config.OLD_PREFIX):
            data["image"] = config.NEW_PREFIX + image[len(config.OLD_PREFIX) :]

    await traverse_json(data, prefix_update_function)
    return data


async def disable_images(json_data: Any) -> Any:
    console.print("[bold red]Disabling...")

    async def disable_image_function(data: dict) -> None:
        if "image" in data:
            data["image"] = ""

    await traverse_json(json_data, disable_image_function)
    return json_data
