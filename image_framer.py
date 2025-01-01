from PIL import Image, ImageDraw, ImageFont, ExifTags
import piexif


def annotate_image(
    image_path,
    output_path,
    border_width=100,  # Width of the frame
    frame_color="white",
    text_color="black",
    second_line_color="#7a7a7a",
    font_path="./fonts/Roboto-Regular.ttf",
    bold_font_path="./fonts/Roboto-Bold.ttf",
    font_size=132,
    line_spacing=72,  # Spacing between the first and second lines
    text_padding=150,  # Spacing between the image and the text
    long_edge_size=2000,  # Resize long edge to this dimension
):
    img = Image.open(image_path)

    # if the image is not jpeg or jpg, do not annotate
    if img.format != "JPEG" and img.format != "JPG":
        print("ERROR: Image is not JPEG or JPG")
        return

    # Handle rotations when needed
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == "Orientation":
                break
        exif_data = img._getexif()
        if exif_data and orientation in exif_data:
            orientation_value = exif_data[orientation]
            if orientation_value == 3:
                img = img.rotate(180, expand=True)
            elif orientation_value == 6:
                img = img.rotate(270, expand=True)
            elif orientation_value == 8:
                img = img.rotate(90, expand=True)
    except Exception as e:
        print(f"Error handling EXIF orientation: {e}")

    # Extract metadata
    exif_data = piexif.load(img.info["exif"])
    model = exif_data["0th"][piexif.ImageIFD.Model].decode("utf-8")
    iso = exif_data["Exif"][piexif.ExifIFD.ISOSpeedRatings]
    shutter_speed = exif_data["Exif"][piexif.ExifIFD.ExposureTime]
    focal_length = exif_data["Exif"][piexif.ExifIFD.FocalLength]
    aperture = exif_data["Exif"][piexif.ExifIFD.FNumber]

    # Frame math
    new_width = img.width + 2 * border_width
    framed_height = img.height + 2 * border_width + text_padding
    framed_image = Image.new("RGB", (new_width, framed_height), frame_color)
    framed_image.paste(img, (border_width, border_width))

    regular_font = ImageFont.truetype(font_path, size=font_size)
    bold_font = ImageFont.truetype(bold_font_path, size=font_size)

    line1_part1 = "Shot on "
    line1_part2 = model  # Bold part
    line2 = f"{(focal_length[0] // focal_length[1])}mm   f/{aperture[0]/aperture[1]:.1f}   {shutter_speed[0]}/{shutter_speed[1]}s   ISO{iso}"

    # Calculate dimensions
    draw = ImageDraw.Draw(framed_image)
    line1_part1_width = draw.textbbox((0, 0), line1_part1, font=regular_font)[2]
    line1_part2_width = draw.textbbox((0, 0), line1_part2, font=bold_font)[2]
    line2_width = draw.textbbox((0, 0), line2, font=regular_font)[2]

    total_text_height = (
        draw.textbbox((0, 0), line1_part1, font=regular_font)[3]
        + draw.textbbox((0, 0), line2, font=regular_font)[3]
        + line_spacing
    )

    # Height of the frame calculations
    new_height = framed_height + total_text_height + text_padding
    framed_image_with_text = Image.new("RGB", (new_width, new_height), frame_color)
    framed_image_with_text.paste(framed_image, (0, 0))

    draw = ImageDraw.Draw(framed_image_with_text)

    # Makes sure the text is centered bellow the image
    text_start_y = img.height + border_width + text_padding

    # Draw the first line
    line1_x = (new_width - (line1_part1_width + line1_part2_width)) // 2
    draw.text((line1_x, text_start_y), line1_part1, fill=text_color, font=regular_font)
    draw.text(
        (line1_x + line1_part1_width, text_start_y),
        line1_part2,
        fill=text_color,
        font=bold_font,
    )
    text_start_y += (
        draw.textbbox((0, 0), line1_part1, font=regular_font)[3] + line_spacing
    )

    # Draw the second line
    line2_x = (new_width - line2_width) // 2
    draw.text((line2_x, text_start_y), line2, fill=second_line_color, font=regular_font)

    # Resize long edge
    long_edge = max(framed_image_with_text.width, framed_image_with_text.height)
    scale_ratio = long_edge_size / long_edge
    new_size = (
        int(framed_image_with_text.width * scale_ratio),
        int(framed_image_with_text.height * scale_ratio),
    )
    resized_image = framed_image_with_text.resize(new_size, Image.Resampling.LANCZOS)

    resized_image.save(output_path)
    print(f"Framed image saved to {output_path}")


if __name__ == "__main__":
    annotate_image(
        image_path="./t1.jpg",
        output_path="./output.jpg",
    )
