import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.utils.ffmpeg import probe_media_file

dirs = [
    'output/audit_verify_run',
    'output/audit_cli_transistor',
    'output/audit_cli_gpu_vert',
    'output/audit_cli_crispr'
]

for d in dirs:
    dp = Path(d)
    mp4 = dp / 'renders' / 'final.mp4'
    info = probe_media_file(mp4)
    print('=== ' + d + ' ===')
    print('MP4 Exists:', mp4.exists(), 'Size:', mp4.stat().st_size if mp4.exists() else 0)
    print('Video Stream:', info.get('has_video'), 'Codec:', info.get('video_codec'), 'Dim:', f"{info.get('width')}x{info.get('height')}", 'FPS:', info.get('fps'), 'Duration:', info.get('duration_seconds'))
    print('Audio Stream:', info.get('has_audio'), 'Codec:', info.get('audio_codec'), 'SampleRate:', info.get('sample_rate'))
    dossier = dp / 'research_dossier.json'
    ledger = dp / 'asset_ledger.json'
    summary = dp / 'pipeline_summary.json'
    print('Artifacts - Dossier:', dossier.exists(), 'Ledger:', ledger.exists(), 'Summary:', summary.exists())
    print()
