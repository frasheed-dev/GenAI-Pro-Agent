import json
from typing import List, Dict, Tuple

# Animation presets
PRESETS = {
    'pop': {
        'start_scale': 50,
        'peak_scale': 115,
        'end_scale': 100,
        'grow_ms': 100,
        'shrink_ms': 100,
        'word_overlap_ms': 50
    },
    'grow': {
        'start_scale': 80,
        'peak_scale': 120,
        'end_scale': 100,
        'grow_ms': 150,
        'shrink_ms': 150,
        'word_overlap_ms': 0
    }
}

# Platform presets
PLATFORMS = {
    'tiktok': {
        'font_name': 'Arial Black',
        'font_size': 72,
        'animation_speed': 0.8,
        'max_words': 5
    }
}

def format_time_ass(seconds: float) -> str:
    """Convert seconds to ASS timestamp (H:MM:SS.cc)"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def generate_grow_effect(word: str, preset: dict) -> str:
    """Generate grow animation tags"""
    s = preset.get('start_scale', 100)
    p = preset['peak_scale']
    e = preset['end_scale']
    g = preset['grow_ms']
    sh = preset['shrink_ms']
    return f"{{\\fscx{s}\\fscy{s}\\t(0,{g},\\fscx{p}\\fscy{p})\\t({g},{g+sh},\\fscx{e}\\fscy{e})}}{word}"

def generate_pop_effect(word: str, preset: dict) -> str:
    """Generate pop animation tags"""
    s = preset['start_scale']
    p = preset['peak_scale']
    e = preset['end_scale']
    g = preset['grow_ms']
    sh = preset['shrink_ms']
    return f"{{\\fscx{s}\\fscy{s}\\t(0,{g},\\fscx{p}\\fscy{p})\\t({g},{g+sh},\\fscx{e}\\fscy{e})}}{word}"

def create_ass_header(platform: str = 'tiktok') -> str:
    """Create ASS file header with styles"""
    plat = PLATFORMS.get(platform, PLATFORMS['tiktok'])
    # Base Style: White text, thin black outline, slight drop shadow, Center aligned (Alignment=5)
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1350
WrapStyle: 1

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: KineticKaraoke,{plat['font_name']},{plat['font_size']},&H00FFFFFF,&H0000FFFF,&H80000000,&H80000000,1,0,0,0,100,100,0,0,1,4,2,5,30,30,120,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

def generate_kinetic_captions(json_data: dict, output_path: str, style: str = 'karaoke', platform: str = 'tiktok'):
    """Generate kinetic ASS captions (Sentence chunks with active word highlighting)"""
    header = create_ass_header(platform)
    events = []

    # Extract all words
    all_words = []
    for segment in json_data.get('segments', []):
        all_words.extend(segment.get('words', []))

    # Group words into small chunks of 3 to prevent line wrapping / jumping
    chunk_size = 3
    for i in range(0, len(all_words), chunk_size):
        chunk = all_words[i:i+chunk_size]
        if not chunk: continue
        
        # Create one Dialogue line per active word in the chunk
        for j, active_word_data in enumerate(chunk):
            start = active_word_data['start']
            end = active_word_data['end']
            
            # Hold the last word on screen slightly longer to prevent flickering
            if j == len(chunk) - 1:
                end += 0.2
                
            line_text = ""
            for k, word_data in enumerate(chunk):
                word = word_data['word'].strip()
                if k == j:
                    # HIGHLIGHTED WORD: Dark Blue Text, Thick Yellow Outline
                    # Reduced bord16 to bord8 and fscx115 to fscx105 so the text width doesn't balloon and cause line jumping
                    highlight = r"{\c&H331100&\3c&H00FFFF&\bord8\fscx105\fscy105}"
                    reset = r"{\r}"
                    line_text += f"{highlight}{word}{reset} "
                else:
                    # NORMAL WORD: Base style (White text, thin black outline)
                    line_text += f"{word} "
                    
            line_text = line_text.strip()
            events.append(
                f"Dialogue: 0,{format_time_ass(start)},{format_time_ass(end)},KineticKaraoke,,0,0,0,,{line_text}"
            )

    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write('\n'.join(events))

    print(f"[Kinetic Engine] Created {output_path} with {len(events)} ASS caption events (Sentence Karaoke style)")
