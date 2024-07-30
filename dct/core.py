import os
import asyncio
import yaml
import argparse
from dct.json import (
    read_json,
    write_json,
    update_prefixes,
    get_urls,
    update_urls,
    disable_images,
)
from dct.download import process_images, process_project_url
from dct.discord import process_discord
from dct.console import console, prompt, int_prompt
from dct.base64 import process_base64, image_to_base64
from dct.config import Config
from dct.paths import get_config
from dct.logging import set_log


async def main():
    # current working directory
    CWD = os.getcwd()
    # parse argument
    parser = argparse.ArgumentParser(description="Image Processor for ICC JSONS")
    parser.add_argument(
        "--config", type=str, default="", help="Path to the configuration YAML file"
    )
    args = parser.parse_args()
    # set yaml path
    yaml_path = args.config
    if not yaml_path:
        console.print(
            "[bold red]Config parameter not provided, switching to manual selection mode..."
        )
        config_directory = prompt.ask(
            "[bold blue]Please enter the directory path where your yaml files are stored [yellow](leave blank and press enter to use current directory)",
            default=CWD,
        )
        yaml_files = await get_config(config_directory)

        console.print("[blue]Yaml files found in given directory:")
        for index, yaml_file in enumerate(yaml_files):
            console.print(f"[yellow]{index+1} ---> {yaml_file}")

        index = int_prompt.ask(
            "[bold blue]Please type the index of yaml file you want to use from the list above [yellow](leave blank and press enter to select first)",
            default=1,
        )
        yaml_path = os.path.join(config_directory, yaml_files[index - 1])
    # validate yaml
    if (
        not os.path.isfile(yaml_path)
        or os.path.splitext(yaml_path)[-1].lower() != ".yaml"
    ):
        console.print(f"[bold red]ERROR: {yaml_path} is not a valid YAML file")
        return
    # read yaml
    with open(yaml_path, "r") as yaml_file:
        yaml_config = yaml.safe_load(yaml_file)

    console.print(f"[blue]Reading {yaml_path}...")

    config = Config(**yaml_config)
    # show config
    if config.SHOW_CONFIG:
        console.print(config)
    # error when project file and output file are same in same directory
    if (
        config.PROJECT_FILE == config.OUTPUT_FILE
        and config.PROJECT_PATH == config.OUTPUT_PATH
    ):
        console.print(
            "[bold red]PROJECT_FILE and OUTPUT_FILE are the same and are in the same directory. Please provide different names or directories. Exiting..."
        )
        return
    # handle project url
    if config.PROJECT_URL.startswith("http"):
        data = await process_project_url(config)
    else:
        console.print("[blue]Reading JSON Data...")
        data = read_json(config.PROJECT_PATH)
    # error when json data is empty
    if not data:
        console.print("[bold red]Error: empty JSON data")
        return
    # validate output file name and remove it if its json
    if (
        os.path.isfile(config.OUTPUT_PATH)
        and os.path.splitext(config.OUTPUT_PATH)[-1].lower() == ".json"
    ):
        console.print("[bold red]Removing Existing Output JSON...")
        os.remove(config.OUTPUT_PATH)
    elif os.path.exists(config.OUTPUT_PATH):
        console.print(
            f"[bold red]ERROR: OUTPUT_FILE : {config.OUTPUT_FILE} is not a valid JSON file name"
        )
        return
    # disable images
    if config.DISABLE_IMAGES:
        console.print(
            "[bold red]DISABLE_IMAGES is set to True. All images in 'image' fields will be disabled, but backgrounds will remain unaffected."
        )
        console.print(
            "[bold red]Ensure that you don't delete the original project file, as recovering images is impossible."
        )
        data = disable_images(data)
        write_json(config, data)
        return
    # create image folder
    console.print("[blue]Checking/Creating Image Folder...")
    os.makedirs(config.IMAGE_PATH, exist_ok=True)
    # process discord url
    if config.PROCESS_DISCORD_LINKS:
        console.print("[blue]Processing Discord Links...")
        data = await process_discord(data, config)
    # base64 to images
    if config.BASE64_TO_IMAGE:
        new_urls = await process_base64(data, config)
        if new_urls:
            data = await update_urls(data, new_urls)
    # download images other than discord urls
    if config.DOWNLOAD_IMAGES:
        urls = await get_urls(data)
        if urls:
            new_urls = await process_images(urls, config)
            data = await update_urls(data, new_urls)
        else:
            console.print("[bold red]No other URLs found, skipping")
    # images to base64
    if config.IMAGE_TO_BASE64:
        if config.BASE64_TO_IMAGE:
            console.print(
                "[bold red]BASE64_TO_IMAGE and IMAGE_TO_BASE64 both cannot be true together. Skipping IMAGE_TO_BASE64..."
            )
        else:
            console.print("[blue]Converting images to base64 embeds...")
            base64_map = await image_to_base64(config)
            data = await update_urls(data, base64_map)
            write_json(config, data)
            return
    # update prefixes
    if config.UPDATE_PREFIXES:
        data = update_prefixes(data, config)
    # write output file
    write_json(config, data)


def run_main():
    try:
        asyncio.run(main())
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred: {e}")
    input("Press any key to exit...")


if __name__ == "__main__":
    run_main()
