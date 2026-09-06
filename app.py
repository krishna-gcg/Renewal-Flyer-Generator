import io
from PIL import Image, ImageDraw, ImageFont, ImageOps
import requests
import streamlit as st

st.set_page_config(page_title="Renewal Flyer Generator", page_icon="🎨", layout="centered")

GOOGLE_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSfF6zDwkwcRYpuVVA8q6Ovtsv83qPTDeLRwwaKWGvldbLmstA/formResponse"


def record_submission(payload: dict) -> None:
    """Silently syncs submission to Google Sheet via Google Form."""
    try:
        form_data = {
            "entry.1969885965": payload.get("name", ""),
            "entry.649682310": payload.get("toastmaster_since", ""),
            "entry.606845149": payload.get("reason", ""),
            "entry.943728985": payload.get("flyer", ""),
        }
        requests.post(GOOGLE_FORM_URL, data=form_data, timeout=5)
    except Exception as e:
        print(f"Error syncing to Google Sheet: {e}")


st.title("Custom Renewal Flyer")
st.write("Customize your Toastmasters renewal flyer by picking a template, adding your photo, and entering your reason to continue.")
st.divider()

# 1. Flyer Selection
st.subheader("1. Choose Your Flyer")
col1, col2 = st.columns(2)
with col1:
    st.image("flyer_1.jpeg", caption="Flyer 1 (Maroon)", use_container_width=True)
with col2:
    st.image("flyer_2.jpeg", caption="Flyer 2 (Light)", use_container_width=True)

flyer_choice = st.radio(
    "Which flyer are you choosing?",
    options=["Flyer 1 (Maroon)", "Flyer 2 (Light)"],
    index=0,
    horizontal=True,
)

flyer_map = {
    "Flyer 1 (Maroon)": "flyer_1.jpeg",
    "Flyer 2 (Light)": "flyer_2.jpeg",
}
selected_flyer_path = flyer_map[flyer_choice]

st.divider()

# 2. Image Input
st.subheader("2. Upload Your Photo")
st.write("Please use [remove.bg](https://www.remove.bg/) on your image to remove the background and upload")

col_prev, _ = st.columns(2)
with col_prev:
    st.image("flyer_preview.jpeg", caption="Example: How to align your image", use_container_width=True)

uploaded_file = st.file_uploader(
    "Upload your photo to place in the flyer",
    type=["jpg", "jpeg", "png"],
    help="Upload a clear portrait or headshot photo.",
    max_upload_size=20,
)

st.divider()

# 3. Reason to Continue Input
st.subheader("3. Enter Your Reason to Continue")
reason_text = st.text_area(
    "My Reason to Continue",
    value="To build confidence, conquer stage fear, and inspire others through impactful leadership and authentic storytelling.",
    placeholder="Write your reason for renewing here...",
    help="What you write here will appear below 'MY REASON TO CONTINUE' on your flyer in Montserrat font.",
    height=50,
)

with st.expander("Text Formatting & Font Options (Optional)", expanded=False):
    font_size = st.slider("Font Size (px)", min_value=18, max_value=42, value=28, step=1)
    font_weight = st.selectbox("Font Weight", ["Medium", "SemiBold", "Bold", "Regular"], index=0)
    line_spacing = st.slider("Line Spacing", min_value=1.1, max_value=2.0, value=1.4, step=0.05)

st.divider()

# 4. Member Name Input
st.subheader("4. Enter Your Name")
member_name = st.text_input(
    "Your Name (as it should appear on the flyer)",
    value="Vinoth, DTM",
    placeholder="e.g. DTM Vinoth ",
    help="Enter your name. It will appear directly above 'TOASTMASTER SINCE' on your flyer in gold Montserrat font.",
)

st.divider()

# 5. Toastmaster Since Year Input
st.subheader("5. Enter the year from which you are a toastmaster")
since_year = st.text_input(
    "Toastmaster since (Year)",
    value="2024",
    max_chars=4,
    help="Enter the year you joined Toastmasters. It will appear next to 'TOASTMASTER SINCE'.",
)

st.divider()

with st.expander("Photo Adjustment Options", expanded=False):
    photo_shape = st.radio("Photo Style", ["Cutout (Transparent)", "Circle", "Square"], index=0, horizontal=True)
    photo_size = st.slider("Photo Size (px)", min_value=150, max_value=450, value=260, step=5)
    pos_x = st.slider("Horizontal Position (X)", min_value=50, max_value=500, value=205, step=5)
    pos_y = st.slider("Vertical Position (Y)", min_value=150, max_value=600, value=400, step=5)

def prepare_photo(img: Image.Image, size: int, style: str) -> Image.Image:
    img = ImageOps.exif_transpose(img).convert("RGBA")

    # If Cutout style, preserve aspect ratio of the transparent subject
    if style == "Cutout (Transparent)":
        w, h = img.size
        scale = size / max(w, h)
        new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
        return img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Square center-crop for Circle / Square
    w, h = img.size
    min_dim = min(w, h)
    left = (w - min_dim) // 2
    top = (h - min_dim) // 2
    cropped = img.crop((left, top, left + min_dim, top + min_dim))
    resized = cropped.resize((size, size), Image.Resampling.LANCZOS)

    if style == "Circle":
        scale = 4
        mask = Image.new("L", (size * scale, size * scale), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, size * scale - 1, size * scale - 1), fill=255)
        mask = mask.resize((size, size), Image.Resampling.LANCZOS)

        output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        output.paste(resized, (0, 0), mask=mask)
        return output
    else:  # Square
        return resized


def draw_reason_text(
    flyer_img: Image.Image,
    text: str,
    start_x: int = 65,
    start_y: int = 655,
    max_width: int = 700,
    font_size: int = 28,
    font_weight: str = "Medium",
    line_spacing: float = 1.4,
) -> Image.Image:
    if not text or not text.strip():
        return flyer_img

    draw = ImageDraw.Draw(flyer_img)
    font_filename = f"Montserrat-{font_weight}.ttf"
    try:
        font = ImageFont.truetype(font_filename, font_size)
    except Exception:
        font = ImageFont.load_default()

    # Wrap each paragraph by pixel width
    paragraphs = text.split("\n")
    lines = []
    for para in paragraphs:
        if not para.strip():
            lines.append("")
            continue
        words = para.split()
        current_line = []
        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            w = bbox[2] - bbox[0]
            if w <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
                    current_line = []
        if current_line:
            lines.append(" ".join(current_line))

    # Render lines with proper vertical spacing
    y = start_y
    for line in lines:
        if line:
            draw.text((start_x, y), line, font=font, fill=(255, 255, 255))
            bbox = draw.textbbox((0, 0), line, font=font)
            line_h = bbox[3] - bbox[1]
            y += int(line_h * line_spacing)
        else:
            y += int(font_size * line_spacing * 0.7)

    return flyer_img


def draw_member_name(
    flyer_img: Image.Image,
    name_text: str,
    start_x: int = 66,
    start_y: int = 927,
    max_width: int = 530,
    base_font_size: int = 28,
) -> Image.Image:
    draw = ImageDraw.Draw(flyer_img)
    # Clear existing template placeholder name
    bg_color = (0, 86, 134)
    draw.rectangle([(64, 924), (540, 958)], fill=bg_color)

    clean_name = str(name_text).strip() if name_text else ""
    if not clean_name:
        return flyer_img

    font_size = base_font_size
    try:
        font = ImageFont.truetype("Montserrat-Bold.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), clean_name, font=font)
    text_w = bbox[2] - bbox[0]

    # Auto scale if name is long
    while text_w > max_width and font_size > 16:
        font_size -= 1
        try:
            font = ImageFont.truetype("Montserrat-Bold.ttf", font_size)
        except Exception:
            break
        bbox = draw.textbbox((0, 0), clean_name, font=font)
        text_w = bbox[2] - bbox[0]

    adjusted_y = start_y + (base_font_size - font_size) // 2
    name_color = (244, 224, 126)
    draw.text((start_x, adjusted_y), clean_name, font=font, fill=name_color)
    return flyer_img


def draw_toastmaster_since_year(
    flyer_img: Image.Image,
    year_text: str,
    start_x: int = 298,
    start_y: int = 963,
    font_size: int = 22,
) -> Image.Image:
    if not year_text or not str(year_text).strip():
        return flyer_img

    draw = ImageDraw.Draw(flyer_img)
    try:
        font = ImageFont.truetype("Montserrat-Medium.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()

    text_color = (255, 255, 255)
    draw.text((start_x, start_y), str(year_text).strip(), font=font, fill=text_color)
    return flyer_img


st.divider()

# 6. Preview and Save / Download
st.subheader("6. Flyer Preview & Save")

try:
    base_flyer = Image.open(selected_flyer_path).convert("RGBA")

    # If user uploaded photo, prepare and paste it
    if uploaded_file is not None:
        user_image = Image.open(uploaded_file)
        processed_photo = prepare_photo(
            user_image,
            size=photo_size,
            style=photo_shape,
        )

        # Paste onto flyer centered at (pos_x, pos_y)
        pw, ph = processed_photo.size
        top_left_x = pos_x - (pw // 2)
        top_left_y = pos_y - (ph // 2)
        base_flyer.paste(processed_photo, (top_left_x, top_left_y), processed_photo)

    # Render Reason text on flyer below 'MY REASON TO CONTINUE'
    base_flyer = draw_reason_text(
        base_flyer,
        text=reason_text,
        start_x=65,
        start_y=655,
        max_width=700,
        font_size=font_size,
        font_weight=font_weight,
        line_spacing=line_spacing,
    )

    # Render Member Name directly above 'TOASTMASTER SINCE'
    base_flyer = draw_member_name(
        base_flyer,
        name_text=member_name,
    )

    # Render Toastmaster since year next to 'TOASTMASTER SINCE'
    final_flyer = draw_toastmaster_since_year(
        base_flyer,
        year_text=since_year,
    ).convert("RGB")

    st.image(final_flyer, caption="Your Customized Flyer Preview", use_container_width=True)

    # Prepare download buffer
    buf = io.BytesIO()
    final_flyer.save(buf, format="JPEG", quality=95)
    byte_im = buf.getvalue()

    # Track current state of user inputs
    current_inputs = {
        "flyer": flyer_choice,
        "photo": (uploaded_file.name, uploaded_file.size) if uploaded_file else None,
        "reason": reason_text.strip(),
        "font_size": font_size,
        "font_weight": font_weight,
        "line_spacing": line_spacing,
        "name": member_name.strip(),
        "since_year": str(since_year).strip(),
        "photo_shape": photo_shape,
        "photo_size": photo_size,
        "pos_x": pos_x,
        "pos_y": pos_y,
    }

    if "submitted_inputs" not in st.session_state:
        st.session_state.submitted_inputs = None

    submit_clicked = st.button("Submit", type="primary", use_container_width=True)

    if submit_clicked:
        if not member_name or not member_name.strip():
            st.error("Please enter your name in Section 4.")
        elif not since_year or not str(since_year).strip():
            st.error("Please enter the year you joined Toastmasters in Section 5.")
        elif not reason_text or not reason_text.strip():
            st.error("Please enter your reason to continue in Section 3.")
        else:
            payload = {
                "flyer": flyer_choice,
                "name": member_name.strip(),
                "toastmaster_since": str(since_year).strip(),
                "reason": reason_text.strip(),
            }
            record_submission(payload)
            st.session_state.submitted_inputs = current_inputs

    # Download button is shown ONLY if the user has submitted the current configuration
    if (
        st.session_state.submitted_inputs is not None
        and st.session_state.submitted_inputs == current_inputs
    ):
        st.success("🎉 Your flyer is ready!")
        st.download_button(
            label="📥 Download Flyer",
            data=byte_im,
            file_name=f"custom_{selected_flyer_path}",
            mime="image/jpeg",
            use_container_width=True,
        )

except Exception as e:
    st.error(f"Error generating flyer: {e}")
