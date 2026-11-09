from jinja2 import Environment, PackageLoader, select_autoescape
from random import randrange, choice
from playwright.sync_api import sync_playwright, Browser
from PIL.Image import Image, new, open as img_open
from PIL.ImageDraw import ImageDraw

env = Environment(
    loader=PackageLoader("genmenu"),
    autoescape=select_autoescape()
)

item_types = ["sandwich", "burger", "wrap", "taco", "tapa", "pepper", "fish dish", "hot dish", "soup", "stew", "phō"]
adjectives = ["beef", "soupy", "pork", "chicken", "turkey", "mutton", "lamb", "fishy", "hot", "drip", "gagging", "dirt", "crass"]
verbs = ["cooked", "brothed", "beequeethed", "eaten", "made", "smashed", "worn", "grilled", "fried", "boiled", "shot", "shat"]
adverbs = ["beefily", "soupily", "porkly", "chickenly", "turkely", "muttonly", "lambly", "fishily", "hotly", "drippingly", "gaggingly", "dirtily", "crassly"]

def random_single_item(no_variants: bool):
    what_is_it = choice(item_types)
    type = randrange(0, 4)
    name = ""
    if type == 0:
        name = f"{choice(adverbs)} {choice(verbs)} {choice(adjectives)} {what_is_it}"
    if type == 1:
        name = f"{choice(verbs)} {choice(adjectives)} {choice(item_types)} {what_is_it}"
    if type == 2:
        name =  f"{choice(adjectives)} {choice(item_types)} {what_is_it}"
    else:
        name = f"{choice(verbs)} {choice(item_types)} {what_is_it}"
    
    desc = f"{choice(adverbs)} {choice(verbs)} {what_is_it}. It's {choice(adjectives)}, {choice(adjectives)}, {choice(adjectives)}, and most importantly, {choice(adjectives)}."
    has_variants = randrange(0, 1) == 0
    if has_variants and not no_variants:
        variants = [random_single_item(True) for i in range(4)]
        return {
            "name": name,
            "desc": desc,
            "variants": variants,
        }
    else:
        return {
            "name": name,
            "desc": desc,
            "price": randrange(0, 100),
        }

menu = {
    "title": "Borg Cáfe",
    "subtitle": "Eat your shorts.",
    "items": [ random_single_item(False) for i in range(10)]
}

def render_page(html: str, path: str, b: Browser):
    page = b.new_page()
    page.set_content(html)
    # pyrefly: ignore[unsupported-operation]
    overlay = new("RGBA", (page.viewport_size["width"], page.viewport_size["height"]), (255, 255, 255, 0))
    draw = ImageDraw(overlay)
    for i in page.locator("css=.desc").all():
        bbox = i.bounding_box()
        print(f"\"{i.text_content()}\" -> {bbox}")
        # pyrefly: ignore[unsupported-operation]
        draw.rectangle((bbox["x"], bbox["y"], bbox["x"]+bbox["width"], bbox["y"]+bbox["height"]), fill=(255, 0, 64, 128))
    page.screenshot(path=path)
    rendered_image = img_open(path).convert("RGBA")
    rendered_image.alpha_composite(overlay)
    rendered_image.save(path)


def main() -> None:
    with sync_playwright() as w:
        b = w.chromium.launch()
        for i in range(1, 4):
            template = env.get_template(f"menu-layout-{i}.html.jinja")
            out = template.render(menu)
            render_page(out, f"out/out{i}.png", b)
            out_seg = template.render(menu, segmented = True)
            render_page(out_seg, f"out/out{i}-seg.png", b)
            with open(f"out/out{i}.html", 'w') as out_html:
                out_html.write(out)
            with open(f"out/out{i}-seg.html", 'w') as out_html:
                out_html.write(out_seg)
        
