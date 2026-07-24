"""
Editeur automatique de video TikTok/Reels pour EquiLab.

Prend une video "brute" de Melodie qui parle face camera + un script minute
(le meme format que celui produit par le prompt ChatGPT dedie, voir
scripts/editing-video/PROMPT.md) et incruste automatiquement des visuels de
contexte (bateau, ecole, enfant qui joue, etc.) trouves sur internet
(Pexels, puis Pixabay en secours) pendant quelques passages seulement,
sous forme de bandeau de 1/4 d'ecran qui glisse depuis le haut ou le bas.

Usage:
    python editor-video.py video.mp4 script.txt -o video_finale.mp4

Cle API (au moins une des deux, gratuites):
    PEXELS_API_KEY   -> https://www.pexels.com/api/        (recommande)
    PIXABAY_API_KEY  -> https://pixabay.com/api/docs/       (secours)
Mettre les cles dans un fichier .env a cote de ce script, ou en variables
d'environnement.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import random
import re
import sys
from dataclasses import dataclass

import requests
from dotenv import load_dotenv
from moviepy import (
    CompositeVideoClip,
    ImageClip,
    VideoFileClip,
)

load_dotenv()

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "618inEvkQslBdQZqp9K20xnAx9onckekwx5jKZlTPLKgSdsos5ysmsnp")
PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY", "56842827-e3be449362cbf3a0baed33ce0")

CACHE_DIR = os.path.join(os.path.dirname(__file__), "media_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

MAX_OVERLAYS = 7          # jamais plus de X incrustations sur une video
MIN_OVERLAYS = 5          # on essaie d'en avoir au moins ca si assez de sujets
OVERLAY_DURATION = 3.2    # duree d'affichage du visuel (secondes), pas oblige de coller au minutage
SLIDE_DURATION = 0.35     # duree de l'animation d'entree/sortie du bandeau
BAND_RATIO = 0.25         # 1/4 de l'ecran


# ---------------------------------------------------------------------------
# 1. Parsing du script minute
# ---------------------------------------------------------------------------

@dataclass
class Segment:
    start: float
    end: float
    action: str
    image_query: str | None  # None si "pas d'image"
    text: str

NO_IMAGE_MARKERS = {"", "pas d'image", "pas d image", "aucune", "aucun", "none", "-"}

# Matche : [0-2s] (jeu/ton...) image : description "dialogue..."
# Les parentheses et le texte entre guillemets sont optionnels pour rester tolerant.
SEGMENT_RE = re.compile(
    r"\[\s*(?P<start>\d+(?:[.,]\d+)?)\s*-\s*(?P<end>\d+(?:[.,]\d+)?)\s*s\s*\]"
    r"\s*(?:\((?P<action>[^)]*)\))?"
    r"\s*(?:image\s*:\s*(?P<image>[^\"\n]*))?"
    r"\s*(?:\"(?P<text>[^\"]*)\")?",
    re.IGNORECASE,
)


def parse_script(raw_text: str) -> list[Segment]:
    segments: list[Segment] = []
    for match in SEGMENT_RE.finditer(raw_text):
        start = float(match.group("start").replace(",", "."))
        end = float(match.group("end").replace(",", "."))
        action = (match.group("action") or "").strip()
        image_raw = (match.group("image") or "").strip()
        text = (match.group("text") or "").strip()

        image_query = None
        if image_raw.lower() not in NO_IMAGE_MARKERS:
            image_query = image_raw

        segments.append(Segment(start, end, action, image_query, text))
    return segments


# ---------------------------------------------------------------------------
# 2. Selection des passages a illustrer (5 a 7 max, repartis dans la video)
# ---------------------------------------------------------------------------

def pick_segments(segments: list[Segment]) -> list[Segment]:
    candidates = [s for s in segments if s.image_query]
    if len(candidates) <= MAX_OVERLAYS:
        return candidates

    # Repartition uniforme dans le temps plutot que les X premiers trouves,
    # pour eviter que les visuels soient tous groupes au debut.
    step = len(candidates) / MAX_OVERLAYS
    picked, seen = [], set()
    for i in range(MAX_OVERLAYS):
        idx = min(int(i * step), len(candidates) - 1)
        if idx not in seen:
            seen.add(idx)
            picked.append(candidates[idx])
    return picked


# ---------------------------------------------------------------------------
# 3. Recherche + telechargement d'un visuel (Pexels puis Pixabay)
# ---------------------------------------------------------------------------

def translate_fr_to_en(query: str) -> str:
    try:
        from deep_translator import GoogleTranslator
        return GoogleTranslator(source="fr", target="en").translate(query)
    except Exception:
        return query  # si la traduction echoue, on tente la requete telle quelle


def _cache_path(query: str, ext: str) -> str:
    key = hashlib.sha1(query.encode("utf-8")).hexdigest()[:16]
    return os.path.join(CACHE_DIR, f"{key}.{ext}")


def _download(url: str, path: str) -> str:
    resp = requests.get(url, stream=True, timeout=30)
    resp.raise_for_status()
    with open(path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1 << 16):
            f.write(chunk)
    return path


def fetch_pexels(query: str) -> str | None:
    if not PEXELS_API_KEY:
        return None
    headers = {"Authorization": PEXELS_API_KEY}

    # 1) on tente une video verticale
    try:
        r = requests.get(
            "https://api.pexels.com/videos/search",
            headers=headers,
            params={"query": query, "orientation": "portrait", "per_page": 5},
            timeout=15,
        )
        r.raise_for_status()
        videos = r.json().get("videos", [])
        if videos:
            video = random.choice(videos)
            files = sorted(video["video_files"], key=lambda f: f.get("width", 0))
            best = next((f for f in files if f.get("width", 0) >= 480), files[-1])
            path = _cache_path(query + "_v", "mp4")
            if not os.path.exists(path):
                _download(best["link"], path)
            return path
    except Exception:
        pass

    # 2) sinon une photo
    try:
        r = requests.get(
            "https://api.pexels.com/v1/search",
            headers=headers,
            params={"query": query, "orientation": "portrait", "per_page": 5},
            timeout=15,
        )
        r.raise_for_status()
        photos = r.json().get("photos", [])
        if photos:
            photo = random.choice(photos)
            url = photo["src"]["large"]
            path = _cache_path(query + "_p", "jpg")
            if not os.path.exists(path):
                _download(url, path)
            return path
    except Exception:
        pass

    return None


def fetch_pixabay(query: str) -> str | None:
    if not PIXABAY_API_KEY:
        return None
    try:
        r = requests.get(
            "https://pixabay.com/api/videos/",
            params={"key": PIXABAY_API_KEY, "q": query, "per_page": 5},
            timeout=15,
        )
        r.raise_for_status()
        hits = r.json().get("hits", [])
        if hits:
            hit = random.choice(hits)
            url = hit["videos"]["medium"]["url"]
            path = _cache_path(query + "_pxv", "mp4")
            if not os.path.exists(path):
                _download(url, path)
            return path
    except Exception:
        pass

    try:
        r = requests.get(
            "https://pixabay.com/api/",
            params={"key": PIXABAY_API_KEY, "q": query, "per_page": 5, "image_type": "photo"},
            timeout=15,
        )
        r.raise_for_status()
        hits = r.json().get("hits", [])
        if hits:
            hit = random.choice(hits)
            url = hit["largeImageURL"]
            path = _cache_path(query + "_pxp", "jpg")
            if not os.path.exists(path):
                _download(url, path)
            return path
    except Exception:
        pass

    return None


def fetch_media(query_fr: str) -> str | None:
    query_en = translate_fr_to_en(query_fr)
    return fetch_pexels(query_en) or fetch_pixabay(query_en)


# ---------------------------------------------------------------------------
# 4. Construction du bandeau qui glisse (overlay clip)
# ---------------------------------------------------------------------------

def build_band_clip(media_path: str, video_w: int, video_h: int, duration: float, from_top: bool):
    band_h = int(video_h * BAND_RATIO)

    if media_path.lower().endswith((".mp4", ".mov", ".webm")):
        clip = VideoFileClip(media_path)
        duration = min(duration, clip.duration)
        clip = clip.subclipped(0, duration)
        clip = clip.without_audio()
    else:
        clip = ImageClip(media_path).with_duration(duration)

    # on remplit toute la largeur, on recadre la hauteur a band_h (center-crop)
    scale = video_w / clip.w
    clip = clip.resized(scale)
    if clip.h > band_h:
        y_off = (clip.h - band_h) / 2
        clip = clip.cropped(y1=y_off, y2=y_off + band_h)
    clip = clip.resized(width=video_w)

    hidden_y = -band_h if from_top else video_h
    shown_y = 0 if from_top else video_h - band_h

    def pos(t):
        if t < SLIDE_DURATION:
            progress = t / SLIDE_DURATION
            y = hidden_y + (shown_y - hidden_y) * progress
        elif t > duration - SLIDE_DURATION:
            progress = (t - (duration - SLIDE_DURATION)) / SLIDE_DURATION
            y = shown_y + (hidden_y - shown_y) * progress
        else:
            y = shown_y
        return ("center", y)

    return clip.with_position(pos)


# ---------------------------------------------------------------------------
# 5. Assemblage final
# ---------------------------------------------------------------------------

def build_video(video_path: str, script_path: str, output_path: str) -> None:
    with open(script_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    segments = parse_script(raw_text)
    if not segments:
        sys.exit("Aucun segment reconnu dans le script. Verifie le format [0-2s] ... image : ... \"...\"")

    chosen = pick_segments(segments)
    print(f"{len(segments)} segments trouves, {len(chosen)} illustres.")

    main_clip = VideoFileClip(video_path)
    overlays = []
    from_top = True  # on alterne a chaque incrustation

    for seg in chosen:
        print(f"  -> [{seg.start}-{seg.end}s] recherche visuel pour: {seg.image_query!r}")
        media_path = fetch_media(seg.image_query)
        if not media_path:
            print("     aucun visuel trouve, segment ignore.")
            continue

        duration = min(OVERLAY_DURATION, max(seg.end - seg.start, 1.5))
        start_at = max(0.0, min(seg.start, main_clip.duration - duration))

        band = build_band_clip(media_path, main_clip.w, main_clip.h, duration, from_top)
        band = band.with_start(start_at)
        overlays.append(band)
        from_top = not from_top

    final = CompositeVideoClip([main_clip, *overlays])
    final = final.with_duration(main_clip.duration)
    final.write_videofile(output_path, fps=main_clip.fps or 30, codec="libx264", audio_codec="aac")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", help="Video source de Melodie (mp4)")
    parser.add_argument("script", help="Fichier texte du script minute")
    parser.add_argument("-o", "--output", default="video_finale.mp4", help="Fichier de sortie")
    args = parser.parse_args()

    build_video(args.video, args.script, args.output)
    print(f"Termine -> {args.output}")


if __name__ == "__main__":
    main()
