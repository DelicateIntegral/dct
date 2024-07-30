import io
import os
import pillow_avif
from PIL import Image
from dct.config import Config


async def save_images(
    image: bytearray, image_path: str, config: Config, original_extension: str
) -> None:
    if os.path.exists(image_path) and not config.OVERWRITE_IMAGES:
        return

    if os.path.exists(image_path):
        os.remove(image_path)

    original_format = original_extension.upper()
    if config.CONVERT_IMAGES:
        target_format = config.IMAGE_FORMAT.upper()
        image_quality = config.IMAGE_QUALITY
    else:
        target_format = original_format
        image_quality = 100

    if (
        config.CONVERT_IMAGES
        and original_format != target_format
        and original_format not in {"SVG", "GIF", "APNG", "WEBP", "AVIF"}
    ):
        image_data = Image.open(io.BytesIO(image))
        if image_data.mode in ("RGBA", "LA") or (
            image_data.mode == "P" and "transparency" in image_data.info
        ):
            image_data = Image.alpha_composite(
                Image.new("RGBA", image_data.size, (255, 255, 255)),
                image_data.convert("RGBA"),
            ).convert("RGB")
        else:
            image_data = image_data.convert("RGB")
        image_data.save(image_path, format=target_format, quality=image_quality)
    else:
        with open(image_path, "wb") as f:
            f.write(image)


async def open_images(image_path: str) -> tuple[io.BytesIO, str | None]:
    with Image.open(image_path) as image:
        image_data = io.BytesIO()
        image.save(image_data, format=image.format)
    return image_data, image.format
