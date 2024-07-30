import asyncio
import os
import base64
import io
from dct.console import (
    console,
    create_progress_bar,
    create_panel_layout,
    create_live,
)
from dct.image import save_images, open_images
from dct.json import get_base64_strings
from dct.config import Config
from dct.paths import get_images


def decode_base64(base64_string: str) -> bytes:
    return base64.b64decode(base64_string.split(",")[1])


def encode_base64(image_bytes: io.BytesIO) -> str:
    return base64.b64encode(image_bytes.getvalue()).decode("utf-8")


async def image_to_base64(config: Config) -> dict | None:
    image_paths = await get_images(config)

    if len(image_paths) == 0:
        console.print(f"[bold red]No images found in path: {config.IMAGE_PATH}")
        return

    base64_map = {}

    convert_progress = create_progress_bar()
    task = convert_progress.add_task(
        "Converting Images to Base64", total=len(image_paths)
    )
    live_panel = create_live(create_panel_layout(convert_progress, 1))

    with live_panel:
        for hash_key, image_path in image_paths.items():
            image_data, image_ext = await open_images(image_path)
            base64_encoded_string = encode_base64(image_data)
            base64_map[hash_key] = (
                f"data:image/{image_ext};base64," + base64_encoded_string
            )
            convert_progress.update(task, advance=1)

    return base64_map


async def base64_to_image(
    image_string: str, key: str, config: Config, semaphore: asyncio.Semaphore
) -> dict[str, str]:
    async with semaphore:
        original_extension = image_string.split(";")[0].split("/")[1].upper()
        if original_extension.lower() == "svg+xml":
            original_extension = "svg"
        if not config.CONVERT_IMAGES or original_extension == "svg":
            image_format = original_extension
        else:
            image_format = config.IMAGE_FORMAT

        image_data = decode_base64(image_string)
        image_name = f"image_{key}.{image_format.lower()}"
        image_path = os.path.join(config.IMAGE_PATH, image_name)
        await save_images(image_data, image_path, config, original_extension)

    url = os.path.join(config.IMAGE_FOLDER, image_name)
    return {key: url}


async def process_base64(json_data, config: Config) -> dict:
    base64_strings = await get_base64_strings(json_data)

    if len(base64_strings) == 0:
        console.print("[bold red]No base64 embeds found...")
        return {}

    base64_progress = create_progress_bar()

    task = base64_progress.add_task(
        "Converting Base64 Images", total=len(base64_strings)
    )
    live_panel = create_live(create_panel_layout(base64_progress, 1))

    base64_rate_limit = 15
    semaphore = asyncio.Semaphore(base64_rate_limit)

    with live_panel:
        results = []
        for key, image_string in base64_strings.items():
            result = await base64_to_image(image_string, key, config, semaphore)
            results.append(result)
            base64_progress.update(task, advance=1)

    new_urls = {k: v for r in results for k, v in r.items()}
    return new_urls
