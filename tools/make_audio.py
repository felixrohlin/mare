"""Generate natural voice clips for every app sentence with Piper (open-source, runs offline).
Writes audio/<lang>/<hash>.mp3 plus audio/<lang>/index.json. Only missing clips are generated."""
import hashlib, json, os, subprocess, sys, urllib.parse, urllib.request, wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PHRASES = json.loads((ROOT / 'tools' / 'phrases.json').read_text(encoding='utf-8'))
MODELS = ROOT / 'tools' / '.models'
SPEED = 1.12  # >1 = slower, calmer speech for small kids

# First candidate that downloads wins. Change the order to switch voice.
VOICES = {
    'en': [('en', 'en_GB', 'cori', 'high'), ('en', 'en_GB', 'jenny_dioco', 'medium'), ('en', 'en_GB', 'alba', 'medium')],
    'pt': [('pt', 'pt_PT', 'tugão', 'medium')],
    'sv': [('sv', 'sv_SE', 'lisa', 'medium'), ('sv', 'sv_SE', 'nst', 'medium')],
    'nl': [('nl', 'nl_NL', 'pim', 'medium'), ('nl', 'nl_NL', 'ronnie', 'medium'), ('nl', 'nl_BE', 'nathalie', 'medium')],
}
BASE = 'https://huggingface.co/rhasspy/piper-voices/resolve/main/'

def fetch_voice(lang):
    MODELS.mkdir(parents=True, exist_ok=True)
    for fam, code, name, q in VOICES[lang]:
        vid = f'{code}-{name}-{q}'
        onnx = MODELS / f'{vid}.onnx'
        try:
            if not onnx.exists():
                for ext in ('.onnx', '.onnx.json'):
                    url = BASE + urllib.parse.quote(f'{fam}/{code}/{name}/{q}/{vid}{ext}')
                    urllib.request.urlretrieve(url, MODELS / f'{vid}{ext}')
            return vid, onnx
        except Exception as e:
            print(f'  {vid} unavailable: {e}')
            for ext in ('.onnx', '.onnx.json'):
                (MODELS / f'{vid}{ext}').unlink(missing_ok=True)
    raise SystemExit(f'no voice could be downloaded for {lang}')

def synth(voice, text, wav_path):
    with wave.open(str(wav_path), 'wb') as w:
        if hasattr(voice, 'synthesize_wav'):  # piper-tts >= 1.3
            try:
                from piper import SynthesisConfig
                voice.synthesize_wav(text, w, syn_config=SynthesisConfig(length_scale=SPEED))
            except ImportError:
                voice.synthesize_wav(text, w)
        else:  # piper-tts 1.2
            voice.synthesize(text, w, length_scale=SPEED)

def main():
    from piper import PiperVoice
    for lang, texts in PHRASES.items():
        vid, onnx = fetch_voice(lang)
        print(f'{lang}: {vid}, {len(texts)} sentences')
        voice = PiperVoice.load(str(onnx))
        out = ROOT / 'audio' / lang
        out.mkdir(parents=True, exist_ok=True)
        clips = {}
        for t in texts:
            f = hashlib.sha1(f'{vid}|{SPEED}|{t}'.encode()).hexdigest()[:12] + '.mp3'
            clips[t] = f
            if (out / f).exists():
                continue
            wav = out / 'tmp.wav'
            synth(voice, t, wav)
            # mono mp3, leading/trailing silence trimmed so counting sounds snappy
            subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(wav), '-af',
                            'silenceremove=start_periods=1:start_threshold=-50dB,areverse,silenceremove=start_periods=1:start_threshold=-50dB,areverse',
                            '-ac', '1', '-b:a', '48k', str(out / f)], check=True)
            wav.unlink()
        for old in out.glob('*.mp3'):
            if old.name not in clips.values():
                old.unlink()
        (out / 'index.json').write_text(json.dumps({'voice': vid, 'clips': clips}, ensure_ascii=False, indent=0), encoding='utf-8')

if __name__ == '__main__':
    main()
