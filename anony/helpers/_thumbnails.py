import os
import aiohttp
import textwrap
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

class Thumbnail:
    def __init__(self):
        # Load Fonts - Adjusted sizes for the new layout
        self.font_title = ImageFont.truetype("anony/helpers/Raleway-Bold.ttf", 45)
        self.font_artist = ImageFont.truetype("anony/helpers/Inter-Light.ttf", 30)
        self.font_time = ImageFont.truetype("anony/helpers/Inter-Light.ttf", 25)

    async def save_thumb(self, output_path: str, url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                with open(output_path, "wb") as f:
                    f.write(await resp.read())
            return output_path

    def draw_rounded_rect(self, draw, coords, radius, fill):
        """Draws a rounded rectangle for the player UI"""
        draw.rounded_rectangle(coords, radius=radius, fill=fill)

    async def generate(self, song, size=(1280, 720)) -> str:
        try:
            temp = f"cache/temp_{song.id}.jpg"
            output = f"cache/{song.id}.png"
            if os.path.exists(output):
                return output

            await self.save_thumb(temp, song.thumbnail)

            # 1. Background (Blurred and Darkened)
            original = Image.open(temp).convert("RGBA")
            background = original.resize(size, Image.Resampling.LANCZOS)
            background = background.filter(ImageFilter.GaussianBlur(20))
            enhancer = ImageEnhance.Brightness(background)
            background = enhancer.enhance(0.4)
            
            draw = ImageDraw.Draw(background)

            # 2. Main Player Container (The dark grey box)
            rect_width, rect_height = 800, 450
            px = (size[0] - rect_width) // 2
            py = (size[1] - rect_height) // 2
            self.draw_rounded_rect(draw, [px, py, px + rect_width, py + rect_height], radius=40, fill=(50, 50, 50, 220))

            # 3. Album Art (Inside the box)
            art_size = 200
            art_x, art_y = px + 40, py + (rect_height - art_size) // 2 - 40
            album_art = ImageOps.fit(original, (art_size, art_size), method=Image.LANCZOS)
            
            # Rounded corners for album art
            mask = Image.new("L", (art_size, art_size), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.rounded_rectangle([0, 0, art_size, art_size], radius=20, fill=255)
            album_art.putalpha(mask)
            background.paste(album_art, (art_x, art_y), album_art)

            # 4. Text (Title & Artist)
            text_start_x = art_x + art_size + 40
            # Truncate title if too long
            title = song.title[:25] + "..." if len(song.title) > 25 else song.title
            draw.text((text_start_x, art_y + 20), title, font=self.font_title, fill="white")
            draw.text((text_start_x, art_y + 80), "Gulzaar Chhaniwala", font=self.font_artist, fill=(200, 200, 200))

            # 5. Progress Bar
            bar_x_start = text_start_x
            bar_x_end = px + rect_width - 60
            bar_y = art_y + 150
            bar_height = 8
            # Background bar
            draw.rounded_rectangle([bar_x_start, bar_y, bar_x_end, bar_y + bar_height], radius=4, fill=(100, 100, 100))
            # Filled bar (static 40% for visual)
            progress_width = (bar_x_end - bar_x_start) * 0.4
            draw.rounded_rectangle([bar_x_start, bar_y, bar_x_start + progress_width, bar_y + bar_height], radius=4, fill="white")

            # Time Labels
            draw.text((bar_x_start, bar_y + 20), "00:00", font=self.font_time, fill="white")
            draw.text((bar_x_end - 60, bar_y + 20), song.duration, font=self.font_time, fill="white")

            # 6. Playback Controls (Play Button & Arrows)
            cx, cy = px + (rect_width // 2) + 100, py + rect_height - 100
            
            # Rewind
            draw.polygon([(cx - 80, cy), (cx - 50, cy - 20), (cx - 50, cy + 20)], fill="white")
            draw.polygon([(cx - 110, cy), (cx - 80, cy - 20), (cx - 80, cy + 20)], fill="white")
            
            # Play Button (Triangle)
            draw.polygon([(cx - 10, cy - 30), (cx + 30, cy), (cx - 10, cy + 30)], fill="white")
            
            # Fast Forward
            draw.polygon([(cx + 60, cy - 20), (cx + 90, cy), (cx + 60, cy + 20)], fill="white")
            draw.polygon([(cx + 90, cy - 20), (cx + 120, cy), (cx + 90, cy + 20)], fill="white")

            background.save(output)
            os.remove(temp)
            return output
        except Exception as e:
            print(f"Error generating thumbnail: {e}")
            return "default_thumb.png"
