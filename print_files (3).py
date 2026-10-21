"""Create printable 3x3 Marvel Champions card sheets from PNG folders.

Install once in the VS Code terminal:
    py -m pip install pillow reportlab

Run:
    py print_files.py

The script prints every PNG in the main fronts folder plus every PNG in the
Aspect Cards folder to front sheets. It prints every PNG in the backs folder
to separate back sheets. It does not try to infer card types or match fronts
and backs one-to-one.
"""
print("[START] print_files.py is running:", __file__, flush=True)

from pathlib import Path
import re
import sys
import traceback
from PIL import Image, ImageDraw
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch


def log(*args, **kwargs):
    """Print progress immediately and also append it to a log file when possible."""
    kwargs.pop("flush", None)
    message = " ".join(str(arg) for arg in args)
    print(message, flush=True, **kwargs)
    try:
        with (Path(__file__).resolve().parent / "print_files_run.log").open("a", encoding="utf-8") as f:
            f.write(message + "\n")
    except Exception:
        pass


log("[START] print_files.py is running:", Path(__file__).resolve())
log("[INFO] Loaded script file:", Path(__file__).resolve())
log("[INFO] Python executable:", sys.executable)

PROJECT_DIR = Path(r"C:\Users\alech\Desktop\Custom MC designs\Silver Surfer Public\cards")
FRONTS_DIR = PROJECT_DIR / "absolute order png fronts"
ASPECTS_DIR = PROJECT_DIR / "Aspect Cards" / "_OUTPUT_V4_3" / "png_all"
BACKS_DIR_CANDIDATES = [
    PROJECT_DIR / "absolute order png backs",
    PROJECT_DIR / "absolute order psd backs",
]
OUTPUT_DIR = PROJECT_DIR / "Silver Surfer Print Files"

# US Letter at 300 DPI, 3 columns x 3 rows.
PAGE_W, PAGE_H = 2550, 3300
CARD_W, CARD_H = 720, 1039
X_POSITIONS = [98, 915, 1732]
Y_POSITIONS = [46, 1130, 2215]
DPI = 300

CUT_LINES = [
    ((0, 46), (93, 46)), ((823, 46), (910, 46)), ((1640, 46), (1727, 46)), ((2457, 46), (2550, 46)),
    ((0, 1085), (93, 1085)), ((823, 1085), (910, 1085)), ((1640, 1085), (1727, 1085)), ((2457, 1085), (2550, 1085)),
    ((0, 1130), (93, 1130)), ((823, 1130), (910, 1130)), ((1640, 1130), (1727, 1130)), ((2457, 1130), (2550, 1130)),
    ((0, 2169), (93, 2169)), ((823, 2169), (910, 2169)), ((1640, 2169), (1727, 2169)), ((2457, 2169), (2550, 2169)),
    ((0, 2215), (93, 2215)), ((823, 2215), (910, 2215)), ((1640, 2215), (1727, 2215)), ((2457, 2215), (2550, 2215)),
    ((0, 3254), (93, 3254)), ((823, 3254), (910, 3254)), ((1640, 3254), (1727, 3254)), ((2457, 3254), (2550, 3254)),
    ((98, 0), (98, 41)), ((98, 1090), (98, 1125)), ((98, 2174), (98, 2210)), ((98, 3259), (98, 3300)),
    ((818, 0), (818, 41)), ((818, 1090), (818, 1125)), ((818, 2174), (818, 2210)), ((818, 3259), (818, 3300)),
    ((915, 0), (915, 41)), ((915, 1090), (915, 1125)), ((915, 2174), (915, 2210)), ((915, 3259), (915, 3300)),
    ((1635, 0), (1635, 41)), ((1635, 1090), (1635, 1125)), ((1635, 2174), (1635, 2210)), ((1635, 3259), (1635, 3300)),
    ((1732, 0), (1732, 41)), ((1732, 1090), (1732, 1125)), ((1732, 2174), (1732, 2210)), ((1732, 3259), (1732, 3300)),
    ((2452, 0), (2452, 41)), ((2452, 1090), (2452, 1125)), ((2452, 2174), (2452, 2210)), ((2452, 3259), (2452, 3300)),
]


def natural_key(path: Path):
    """Sort names naturally, e.g. 2 before 10; keep stable filename ordering."""
    parts = re.split(r"(\d+)", path.name.lower())
    return [int(part) if part.isdigit() else part for part in parts]


def get_pngs(folder: Path, required=True):
    if not folder.is_dir():
        if required:
            raise FileNotFoundError(f"Required folder was not found:\n{folder}")
        return []
    return sorted((p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == ".png"), key=natural_key)


def choose_back_folder():
    for folder in BACKS_DIR_CANDIDATES:
        if folder.is_dir():
            return folder
    raise FileNotFoundError(
        "Could not find the backs folder. Tried:\n" + "\n".join(str(p) for p in BACKS_DIR_CANDIDATES)
    )


def choose_player_back(back_images):
    """Choose a blue player-card back image, not the orange encounter back or face card."""
    candidates = [
        path for path in back_images
        if "hero_back" in path.stem.lower() and not path.stem.lower().startswith("f ")
    ]
    if not candidates:
        candidates = [path for path in back_images if "hero_back" in path.stem.lower()]
    if not candidates:
        raise FileNotFoundError(
            "Could not find a player-card back. Expected a PNG with 'Hero_Back' in its filename."
        )
    return candidates[0]


def load_card(path: Path):
    with Image.open(path) as source:
        image = source.convert("RGB")
    # Fit the full card inside the card area without stretching its aspect ratio.
    image.thumbnail((CARD_W, CARD_H), Image.Resampling.LANCZOS)
    card = Image.new("RGB", (CARD_W, CARD_H), "white")
    x = (CARD_W - image.width) // 2
    y = (CARD_H - image.height) // 2
    card.paste(image, (x, y))
    return card


def add_cut_marks(page):
    draw = ImageDraw.Draw(page)
    for start, end in CUT_LINES:
        draw.line((start, end), fill=(255, 0, 0), width=2)


def create_sheets(image_paths, prefix):
    sheet_paths = []
    if not image_paths:
        log(f"WARNING: No images found for {prefix}; no sheets created.")
        return sheet_paths

    total_pages = (len(image_paths) + 8) // 9
    log(f"\nCreating {prefix} sheets from {len(image_paths)} PNG files ({total_pages} page(s))...")
    for page_number, start in enumerate(range(0, len(image_paths), 9), start=1):
        page = Image.new("RGB", (PAGE_W, PAGE_H), "white")
        batch = image_paths[start:start + 9]
        for slot, image_path in enumerate(batch):
            row, col = divmod(slot, 3)
            try:
                card = load_card(image_path)
            except Exception as exc:
                raise RuntimeError(f"Could not read image:\n{image_path}\nReason: {exc}") from exc
            page.paste(card, (X_POSITIONS[col], Y_POSITIONS[row]))
        add_cut_marks(page)
        out_path = OUTPUT_DIR / f"{prefix}_sheet_{page_number:02d}.png"
        page.save(out_path, dpi=(DPI, DPI), optimize=True)
        sheet_paths.append(out_path)
        log(f"  [{page_number}/{total_pages}] Saved: {out_path}")
    return sheet_paths


def write_pdf(pdf_path: Path, page_paths):
    if not page_paths:
        log(f"WARNING: Skipping PDF because there are no pages: {pdf_path.name}")
        return False
    log(f"Writing PDF: {pdf_path}")
    pdf = canvas.Canvas(str(pdf_path), pagesize=(8.5 * inch, 11 * inch), pageCompression=1)
    for page_path in page_paths:
        pdf.drawImage(str(page_path), 0, 0, width=8.5 * inch, height=11 * inch)
        pdf.showPage()
    pdf.save()
    log(f"SUCCESS: Created PDF ({len(page_paths)} pages): {pdf_path}")
    return True


def main():
    log("=" * 68)
    log("Marvel Champions — Silver Surfer Print Sheet Generator")
    log("=" * 68)
    log(f"Project folder: {PROJECT_DIR}")
    log(f"Output folder:  {OUTPUT_DIR}")

    fronts = get_pngs(FRONTS_DIR)
    aspects = get_pngs(ASPECTS_DIR)
    backs_dir = choose_back_folder()
    available_back_images = get_pngs(backs_dir)

    if not fronts:
        raise RuntimeError(f"No PNG front images found in: {FRONTS_DIR}")
    if not available_back_images:
        raise RuntimeError(f"No PNG back images found in: {backs_dir}")

    all_fronts = fronts + aspects
    player_back = choose_player_back(available_back_images)

    # Keep every supplied back image in its original natural filename order.
    # Aspect cards use the player-card back, so append one copy per aspect card
    # instead of replacing all original Silver Surfer backs with a blue back.
    backs = list(available_back_images) + [player_back] * len(aspects)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    log("\nINPUT SUMMARY")
    log(f"  Main card fronts: {len(fronts)}  |  {FRONTS_DIR}")
    log(f"  Aspect card fronts: {len(aspects)}  |  {ASPECTS_DIR}")
    log(f"  Total front images: {len(all_fronts)}")
    log(f"  Available back-image files: {len(available_back_images)}  |  {backs_dir}")
    log(f"  Player-card back template: {player_back.name}")
    log(f"  Original ordered back images retained: {len(available_back_images)}")
    log(f"  Player backs added for aspect cards: {len(aspects)}")
    log(f"  Total back images: {len(backs)}")
    log("\nFront order: numbered main cards first, then aspect cards in natural filename order.")
    log("Back order: all supplied back PNGs in natural filename order, followed by player-card backs for aspect cards.")
    log("Each sheet holds up to 9 images. Front and back page counts may differ if supplied main-card backs do not match the main-front count.")

    front_sheets = create_sheets(all_fronts, "front")
    back_sheets = create_sheets(backs, "back")
    write_pdf(OUTPUT_DIR / "Silver_Surfer_Fronts.pdf", front_sheets)
    write_pdf(OUTPUT_DIR / "Silver_Surfer_Backs.pdf", back_sheets)

    log("\n" + "=" * 68)
    log("SUCCESS — print files generated")
    log(f"Output folder: {OUTPUT_DIR}")
    log(f"Front PDF: {OUTPUT_DIR / 'Silver_Surfer_Fronts.pdf'}")
    log(f"Back PDF:  {OUTPUT_DIR / 'Silver_Surfer_Backs.pdf'}")
    log(f"PNG sheet previews: {OUTPUT_DIR}")
    log("Print at Actual Size / 100% on US Letter paper. Inspect a test page first.")
    log("=" * 68)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        log("\nFAILED TO CREATE PRINT FILES")
        log(f"{type(error).__name__}: {error}")
        log("\nFull traceback:")
        traceback.print_exc()
        sys.exit(1)
