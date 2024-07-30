import asyncio
import aiohttp
from dct.json import get_urls, update_urls
from dct.download import process_images
from dct.console import (
    console,
    create_progress_bar,
    create_panel_layout,
    create_live,
    Progress,
)
from dct.config import Config
from dct.semaphore import DynamicSemaphore


async def refresh_url(session: aiohttp.ClientSession, url: str, config: Config) -> dict:
    api_url = "https://discord.com/api/v9/attachments/refresh-urls"
    payload = {"attachment_urls": [url]}
    headers = {"Authorization": f"Bot {config.TOKEN}"}

    try:
        async with session.post(api_url, json=payload, headers=headers) as response:
            if response.status == 200:
                refreshed_urls = await response.json()
                return {
                    "status": response.status,
                    "new_url": refreshed_urls["refreshed_urls"][0]["refreshed"],
                }
            elif response.status == 429:
                return {"status": response.status, "headers": response.headers}
            else:
                return {"status": response.status}
    except (aiohttp.ClientError, Exception) as e:
        return {"status": "error", "error": str(e)}


async def try_refresh(
    session: aiohttp.ClientSession,
    url: str,
    key: str,
    config: Config,
    semaphore: DynamicSemaphore,
) -> tuple[dict, bool]:
    max_retries = 5
    retries = 1
    exp_limit = semaphore._max_count
    exp_time = 1
    new_limit = exp_limit

    while retries <= max_retries:
        async with semaphore:
            status_info = await refresh_url(session, url, config)
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
                    f"Failed to refresh url for {key} with status: {error}, url: {url}"
                )
                return {key: url}, False

        retries += 1

    config.LOGGER.debug(f"Max retries exceeded for {key}, url: {url}")
    return {key: url}, False


async def process_refresh(urls: dict, config: Config) -> dict:
    semaphore = DynamicSemaphore(config.RATE_LIMIT)
    refresh_progress = create_progress_bar()
    try:
        async with aiohttp.ClientSession() as session:
            tasks = [
                try_refresh(session, url, key, config, semaphore)
                for key, url in urls.items()
            ]
            task = refresh_progress.add_task("Refreshing URLs", total=len(tasks))
            live_panel = create_live(create_panel_layout(refresh_progress, 1))

            with live_panel:
                results = []
                for coro in asyncio.as_completed(tasks):
                    result, status = await coro
                    results.append(result)
                    if status:
                        refresh_progress.update(task, advance=1)

    except aiohttp.ClientError as e:
        config.LOGGER.debug(f"Client error: {str(e)}")
    except Exception as e:
        config.LOGGER.debug(f"Unexpected error: {str(e)}")

    new_urls = {k: v for r in results for k, v in r.items()}
    return new_urls


async def process_discord(data, config: Config):
    urls = await get_urls(data, True)

    if not urls:
        console.print("[bold red]No discord links found...")
        return data

    new_urls = await process_refresh(urls, config)

    if config.DOWNLOAD_IMAGES:
        new_urls = await process_images(new_urls, config)

    return await update_urls(data, new_urls)
