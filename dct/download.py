import aiohttp
import asyncio
import os
import json
from pathlib import Path
from typing import Any
from dct.console import (
    console,
    create_progress_bar,
    create_group,
    create_panel_layout,
    create_live,
    Progress,
)
from dct.config import Config
from dct.paths import (
    get_image_name,
    get_url_components,
    get_parsed_url,
    ParseResult,
)
from dct.image import save_images
from dct.json import update_urls, get_remote_urls
from dct.semaphore import DynamicSemaphore


async def get_headers(parsed_url: ParseResult, mode: int = 0) -> dict[str, str]:
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8",
        "Accept-Encoding": "gzip,deflate,br,zstd",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Host": parsed_url.netloc,
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    }

    if mode == 1:
        headers["Sec-Fetch-Site"] = "cross-site"
    elif mode == 2:
        headers["Sec-Fetch-Site"] = "same-site"

    return headers


async def download_content(
    response: aiohttp.ClientResponse,
    download_progress: Progress,
    file_name: str,
    remove_task: bool = False,
) -> bytearray:
    total_size = int(response.headers.get("content-length", 0))
    task_id = download_progress.add_task(
        "Downloading", total=total_size or None, filename=file_name
    )
    data = bytearray()
    chunk_size = 1024
    async for chunk in response.content.iter_chunked(chunk_size):
        data.extend(chunk)
        download_progress.update(task_id, advance=len(chunk))
    if remove_task:
        download_progress.remove_task(task_id)
    return data


async def session_with_headers(
    session: aiohttp.ClientSession,
    url: str,
    download_progress: Progress,
    file_name: str,
    remove_task: bool,
) -> tuple[aiohttp.ClientResponse | str, bytearray]:

    retries = 0
    parsed_url = await get_parsed_url(url)

    while retries < 3:
        headers = await get_headers(parsed_url, retries)

        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await download_content(
                    response, download_progress, file_name, remove_task
                )
                return response, data
            elif response.status == 429:
                break
        retries += 1
    return response, bytearray()


async def session_without_headers(
    session: aiohttp.ClientSession,
    url: str,
    download_progress: Progress,
    file_name: str,
    remove_task: bool,
) -> tuple[aiohttp.ClientResponse, bytearray]:

    async with session.get(url) as response:
        if response.status == 200:
            data = await download_content(
                response, download_progress, file_name, remove_task
            )
            return response, data

    return response, bytearray()


async def download_remote_project(config: Config) -> dict | Any:
    console.print(
        f"[bold blue]Downloading remote project json from url: {config.PROJECT_URL}"
    )
    _, file_name, _ = await get_url_components(config.PROJECT_URL)
    try:
        async with aiohttp.ClientSession() as session:
            download_progress = create_progress_bar(1)
            live_panel = create_live(create_panel_layout(download_progress, 1))
            with live_panel:
                response, data = await session_with_headers(
                    session,
                    config.PROJECT_URL,
                    download_progress,
                    file_name,
                    False,
                )
                if response and response.status != 200:
                    response, data = await session_without_headers(
                        session, config.PROJECT_URL, download_progress, file_name, False
                    )
                    if response and response.status != 200:
                        config.LOGGER.debug(
                            f"Failed to download project file: {response.status}"
                        )
                        return {}
    except aiohttp.ClientError as e:
        config.LOGGER.debug(f"[bold red]Client error: {str(e)}")
    except Exception as e:
        config.LOGGER.debug(f"[bold red]Unexpected error: {str(e)}")
        return {}

    return json.loads(data.decode("utf-8")) if data else {}


async def download_image(
    session: aiohttp.ClientSession,
    url: str,
    key: str,
    config: Config,
    download_progress: Progress,
) -> dict:
    status_info = None
    try:
        original_name = await get_image_name(url)
        original_extension = Path(original_name).suffix.split(".")[-1]
        image_name = f"image_{key}.{config.IMAGE_FORMAT.lower() if config.CONVERT_IMAGES else original_extension}"
        image_path = os.path.join(config.IMAGE_PATH, image_name)
        parsed_url = await get_parsed_url(url)
        if "imgur" in parsed_url.netloc:
            status_info = {
                "status": "error",
                "error": "skipping, imgur url processing is in development",
            }
        elif not os.path.exists(image_path) or config.OVERWRITE_IMAGES:
            response, data = await session_with_headers(
                session, url, download_progress, key, True
            )
            if response and response.status == 200:
                await save_images(data, image_path, config, original_extension)
                url = os.path.join(config.IMAGE_FOLDER, image_name)
                status_info = {"status": response.status, "new_url": url}
            elif response and response.status == 429:
                status_info = {
                    "status": response.status,
                    "headers": response.headers,
                }
            else:
                response, data = await session_without_headers(
                    session, url, download_progress, key, True
                )
                if response and response.status == 200:
                    await save_images(data, image_path, config, original_extension)
                    url = os.path.join(config.IMAGE_FOLDER, image_name)
                    status_info = {"status": response.status, "new_url": url}
                elif response and response.status == 429:
                    status_info = {
                        "status": response.status,
                        "headers": response.headers,
                    }
                elif response:
                    status_info = {"status": response.status}
                else:
                    status_info = {"status": "error", "error": "No response received"}
        else:
            status_info = {"status": 200, "new_url": url}
    except aiohttp.ClientError as e:
        status_info = {"status": "error", "error": f"Client error: {str(e)}"}
    except Exception as e:
        status_info = {"status": "error", "error": f"Unexpected error: {str(e)}"}
    return status_info


async def try_download(
    session: aiohttp.ClientSession,
    url: str,
    key: str,
    config: Config,
    semaphore: DynamicSemaphore,
    progress: Progress,
) -> tuple[dict, dict]:
    max_retries = 5
    retries = 1
    exp_limit = semaphore._max_count
    exp_time = 1
    new_limit = exp_limit

    while retries <= max_retries:
        async with semaphore:
            status_info = await download_image(session, url, key, config, progress)
            status = status_info["status"]

            if status == 200:
                return {key: status_info["new_url"]}, True
            elif status == 429:
                headers = status_info["headers"]
                exp_limit = max(1, exp_limit // retries)
                exp_time = min(60, exp_time * retries)
                reset_after = float(headers.get("X-RateLimit-Reset-After", exp_time))
                new_limit = int(headers.get("X-RateLimit-Limit", exp_limit))
                await semaphore.update_max_count(new_limit)
                config.LOGGER.debug(
                    f"Rate limited for {key}, sleeping for {reset_after} seconds..."
                )
                await asyncio.sleep(reset_after)
            else:
                error = status if status != "error" else status_info["error"]
                config.LOGGER.debug(
                    f"Failed to download for {key} with status: {error}, url: {url}"
                )
                return {key: url}, False
        retries += 1

    config.LOGGER.debug(f"Max retries exceeded for {key}, url: {url}")
    return {key: url}, False


async def process_images(urls: dict, config: Config) -> dict:
    semaphore = DynamicSemaphore(config.DOWNLOAD_RATE_LIMIT)
    image_progress = create_progress_bar()
    download_progress = create_progress_bar(1)
    image_panel_group = create_group(image_progress, download_progress)
    timeout = aiohttp.ClientTimeout(total=config.SESSION_TIMEOUT)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            tasks = [
                try_download(session, url, key, config, semaphore, download_progress)
                for key, url in urls.items()
            ]
            task = image_progress.add_task("Downloading Images", total=len(tasks))
            live_panel = create_live(create_panel_layout(image_panel_group, 0))

            with live_panel:
                results = []
                for coro in asyncio.as_completed(tasks):
                    result, status = await coro
                    results.append(result)
                    if status:
                        image_progress.update(task, advance=1)
                live_panel.update(create_panel_layout(image_panel_group, 1))

    except aiohttp.ClientError as e:
        config.LOGGER.debug(f"Client error: {str(e)}")
        raise e
    except Exception as e:
        config.LOGGER.debug(f"Unexpected error: {str(e)}")
        raise e

    new_urls = {k: v for r in results for k, v in r.items()}
    return new_urls


async def process_project_url(config: Config) -> Any:
    data = await download_remote_project(config)

    if not data:
        return {}

    urls = await get_remote_urls(data, config)

    if not urls:
        console.print("[bold red]No remote image folder found...")
        return data

    return await update_urls(data, urls)
