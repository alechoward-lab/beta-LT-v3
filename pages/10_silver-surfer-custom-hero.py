"""Silver Surfer custom hero files and card previews."""

import json
import re
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from components.nav_banner import render_footer, render_nav_banner, render_page_header


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = PROJECT_ROOT / "static"
SOURCE_JSON = STATIC_DIR / "Silver Surfer v9 Public.json"
FRONTS_PDF = STATIC_DIR / "Silver_Surfer_Fronts.pdf"
BACKS_PDF = STATIC_DIR / "Silver_Surfer_Backs.pdf"


def numbered_pngs(folder_name: str) -> list[Path]:
    """Return PNGs ordered by the first number in each filename."""
    folder = STATIC_DIR / folder_name
    return sorted(
        folder.glob("*.png"),
        key=lambda path: (
            (0, int(match.group()), path.name.casefold())
            if (match := re.search(r"\d+", path.stem))
            else (1, 0, path.name.casefold())
        ),
    )


def build_viewer_images() -> list[tuple[str, Path]]:
    """Order alter ego, hero, card 1, planets, then cards 2–23."""
    folder = STATIC_DIR / "view_silver_surfer"
    images: list[tuple[str, Path]] = []

    for filename, label in (("0 alter-ego.png", "Alter Ego"), ("0 hero.png", "Hero")):
        image_path = folder / filename
        if image_path.is_file():
            images.append((label, image_path))

    cards = [
        path for path in folder.glob("*.png")
        if re.match(r"\d+ ", path.name) and not path.name.startswith("0 ")
    ]
    cards.sort(key=lambda path: (int(re.match(r"\d+", path.name).group()), path.name.casefold()))

    first_card = [path for path in cards if path.name.startswith("1 ")]
    images.extend(("Card 1", path) for path in first_card)

    planets = sorted(
        folder.glob("Planet *.png"),
        key=lambda path: int(re.match(r"Planet (\d+)", path.stem).group(1)),
    )
    for index, path in enumerate(planets, start=1):
        images.append((f"Planet {index}", path))

    remaining_cards = [path for path in cards if not path.name.startswith("1 ")]
    images.extend(
        (f"Card {path.name.split(' ', 1)[0]}", path)
        for path in remaining_cards
    )

    # Keep a file to a single viewer entry even if it is added by more than
    # one category in the future. Preserve the first occurrence and its order.
    unique_images: list[tuple[str, Path]] = []
    seen_paths: set[str] = set()
    for label, image_path in images:
        normalized_path = str(image_path.resolve()).casefold()
        if normalized_path not in seen_paths:
            seen_paths.add(normalized_path)
            unique_images.append((label, image_path))
    return unique_images


VIEWER_IMAGES = build_viewer_images()


def advance_viewer(step: int) -> None:
    """Move to the adjacent image, wrapping at either end of the gallery."""
    current_index = st.session_state.get("silver_surfer_viewer_index", 0)
    if VIEWER_IMAGES:
        st.session_state.silver_surfer_viewer_index = (
            current_index + step
        ) % len(VIEWER_IMAGES)


@st.dialog("Silver Surfer Card Viewer", width="large")
def show_card_viewer() -> None:
    """Show one ordered card at a time in a viewport-sized dialog."""
    if not VIEWER_IMAGES:
        st.error("No card images were found in static/view_silver_surfer.")
        return

    image_index = st.session_state.get("silver_surfer_viewer_index", 0)
    image_index = max(0, min(image_index, len(VIEWER_IMAGES) - 1))
    label, image_path = VIEWER_IMAGES[image_index]

    st.markdown(
        """<style>
div[data-testid="stDialog"] > div {
    width: 96vw !important;
    max-width: 1600px !important;
}
div[data-testid="stDialog"] [data-testid="stImage"] img {
    max-height: 78vh;
    object-fit: contain;
}
</style>""",
        unsafe_allow_html=True,
    )
    st.image(str(image_path), width="stretch")
    st.caption(
        f"{label} · {image_index + 1} of {len(VIEWER_IMAGES)} "
        "(use ← / → arrow keys to browse)"
    )

    components.html(
        """<script>
(function () {
    const parentDocument = window.parent.document;
    const previousHandler = parentDocument.__silverSurferViewerKeyHandler;
    if (previousHandler) {
        parentDocument.removeEventListener("keydown", previousHandler);
    }

    const keyHandler = function (event) {
        if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
        if (event.target.closest("input, textarea, select, [contenteditable='true']")) return;

        let buttonText = null;
        if (event.key === "ArrowLeft") buttonText = "← Previous";
        if (event.key === "ArrowRight") buttonText = "Next →";
        if (!buttonText) return;

        const dialog = parentDocument.querySelector('[data-testid="stDialog"]');
        if (!dialog) return;
        const button = Array.from(dialog.querySelectorAll("button"))
            .find((candidate) => candidate.innerText.trim() === buttonText);
        if (button && !button.disabled) {
            event.preventDefault();
            button.click();
        }
    };

    parentDocument.addEventListener("keydown", keyHandler);
    parentDocument.__silverSurferViewerKeyHandler = keyHandler;
})();
</script>""",
        height=0,
        width=0,
    )

    previous_col, next_col = st.columns(2)
    with previous_col:
        st.button(
            "← Previous",
            width="stretch",
            on_click=advance_viewer,
            args=(-1,),
        )
    with next_col:
        st.button(
            "Next →",
            width="stretch",
            on_click=advance_viewer,
            args=(1,),
        )


st.set_page_config(page_title="Silver Surfer Custom Hero", page_icon="🃏", layout="wide")
render_nav_banner("silver-surfer-custom-hero")
render_page_header(
    "Silver Surfer Custom Hero",
)

st.markdown(
    """
I created a custom Silver Surfer hero for Marvel Champions because he is one of my favorite characters. His main mechanic is to travel to and from planets. You begin the game with your trusty surfboard and Zenn-La, his home world, in play and a planet deck. Your alter-ego ability allows you to use the surfboard to bring the top card of the planet deck into play. Once a planet is in play, you can use your surfboard to arrive at the planet, and your hero ability to depart the planet and return to fighting the villain. Each planet has a unique bonus for arriving and departing, and since the planet deck is shuffled during set up, every game will play out differently! Key to mastering Silver Surfer is to be thoughtful about when and where you travel to.

Click the buttons below to download print files and the tabletop simulator object. If you have any feedback feel free to join my discord and post a message with your thoughts! I playtested Silver Surfer a lot with my friends, but there's always room to make improvements. I plan on eventually taking people's feedback into account to make some improvements and keep the files up to date. There are also a bunch of aspect cards I made. They are less tested and in a more alpha state. The justice cards are fairly refined as that is the precon I envisioned him with. To make his precon deck just put all the justice cards with the however many of the basic cards you want. The precon is already assembled in Tabletop Simulator, so you can just load it up and play.
### Some rules clarifications:

- During setup, start with Zenn-La and your Cosmic Surfboard in play. Shuffle the planet deck and set it aside facedown. Set the linked Ego The Living Planet ally aside. The rest of setup is just like normal Marvel Champions.
- Player Environments are a card type I made up to represent the planets.
- I took some liberties with the wording since it isn't official content. If you see a card that says "I" or "me" it is referring to the card itself. I find this more clear, more compact, and more fun. For example, his signature ally Nova Frankie Raye can also travel to planets, so her ability says "I" arrive then depart, indicating that it is the Frankie Raye ally that is doing it.
- Characters at planets cannot attack or defend and lose guard / patrol. There are a few ways to send enemies to planets and it can be very beneficial. Enemies do not gain the arrive and depart bonuses to planets.
- Ego is in the planet deck and when he is revealed he engages Silver Surfer and functions as a normal minion. When he is defeated, the Ego the Living Planet ally enters play under your control.
    """
)

download_columns = st.columns(3)

try:
    save_data = json.loads(SOURCE_JSON.read_text(encoding="utf-8"))
    silver_surfer_bag = next(
        obj for obj in save_data["ObjectStates"]
        if obj.get("Name") == "Bag" and obj.get("Nickname") == "Silver Surfer v9 Public"
    )
    save_data["Grid"] = {
        "Type": 0,
        "Lines": False,
        "Color": {"r": 0.5, "g": 0.5, "b": 0.5},
        "Opacity": 0.75,
        "ThickLines": False,
        "Snapping": False,
        "Offset": False,
        "BothSnapping": False,
        "xSize": 2.0,
        "ySize": 2.0,
    }
    save_data["ObjectStates"] = [silver_surfer_bag]
    object_json = json.dumps(save_data, indent=2).encode("utf-8")
except (OSError, json.JSONDecodeError, KeyError, StopIteration) as exc:
    object_json = None
    object_error = str(exc)

with download_columns[0]:
    st.subheader("Tabletop Simulator")
    if object_json is None:
        st.error(f"The TTS object could not be prepared: {object_error}")
    else:
        st.download_button(
            "Download TTS Object (.json)",
            data=object_json,
            file_name="Silver Surfer v9 Public.json",
            mime="application/json",
            key="download_silver_surfer_tts_object",
            width="stretch",
        )

with download_columns[1]:
    st.subheader("Card Fronts")
    st.write("Printable PDF of the card fronts.")
    st.download_button(
        "Download Fronts PDF",
        data=lambda: FRONTS_PDF.read_bytes(),
        file_name=FRONTS_PDF.name,
        mime="application/pdf",
        key="download_silver_surfer_fronts_pdf",
        width="stretch",
    )

with download_columns[2]:
    st.subheader("Card Backs")
    st.write("Printable PDF of the card backs.")
    st.download_button(
        "Download Backs PDF",
        data=lambda: BACKS_PDF.read_bytes(),
        file_name=BACKS_PDF.name,
        mime="application/pdf",
        key="download_silver_surfer_backs_pdf",
        width="stretch",
    )

with st.expander("How to install and open the object in Tabletop Simulator"):
    st.markdown(
        """
1. Download **TTS Object (.json)** above.
2. Move the JSON file into Tabletop Simulator's **Saved Objects** folder:
   - **Windows:** `Documents\\My Games\\Tabletop Simulator\\Saves\\Saved Objects`
   - **macOS:** `~/Library/Tabletop Simulator/Saves/Saved Objects`
3. In Tabletop Simulator, choose **Objects** from the top toolbar, then **Saved Objects**, and select **Silver Surfer v9 Public**. The bag appears on the table; open it to access its contents.

Create the **Saved Objects** folder if it does not exist. Restart Tabletop Simulator if the object is not listed.
        """
    )

st.divider()
st.subheader("View the cards full screen")
if st.button("Open full-screen card viewer", type="primary"):
    st.session_state.silver_surfer_viewer_index = 0
    st.session_state.silver_surfer_viewer_open = True

if st.session_state.get("silver_surfer_viewer_open", False):
    show_card_viewer()

st.divider()
st.subheader("Card Fronts")
front_images = numbered_pngs("Silver_Surfer_Front")
if not front_images:
    st.warning("No card front PNGs were found.")
else:
    for start in range(0, len(front_images), 4):
        image_columns = st.columns(4)
        for column, image_path in zip(image_columns, front_images[start:start + 4]):
            page_number = re.search(r"\d+", image_path.stem)
            caption = f"Page {page_number.group()}" if page_number else image_path.stem
            with column:
                st.image(str(image_path), caption=caption, width="stretch")

st.subheader("Card Backs")
back_images = numbered_pngs("Silver_Surfer_Back")
if not back_images:
    st.warning("No card back PNGs were found.")
else:
    for start in range(0, len(back_images), 4):
        image_columns = st.columns(4)
        for column, image_path in zip(image_columns, back_images[start:start + 4]):
            page_number = re.search(r"\d+", image_path.stem)
            caption = f"Page {page_number.group()}" if page_number else image_path.stem
            with column:
                st.image(str(image_path), caption=caption, width="stretch")

render_footer(show_card_data_credit=False)