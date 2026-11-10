"""Build the standalone XMB NRO using installed devkitPro libraries, without xmake.

python scripts/build_cards_local.py --json-include PATH_TO_DIRECTORY_CONTAINING_nlohmann
Requires Switch SDL2/ttf/mixer, curl, webp, zlib and their devkitPro packages.
The pinned audout SDL archive must already be extracted to build/sdl2-audout.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse, hashlib, os, shutil, subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--json-include', required=True, type=Path)
parser.add_argument('--jobs', type=int, default=min(6, os.cpu_count() or 2))
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
os.chdir(root)
dkp = Path(os.environ.get('DEVKITPRO', 'C:/devkitPro' if os.name == 'nt' else '/opt/devkitpro'))
if os.name == 'nt' and not dkp.exists() and Path('C:/devkitPro').exists():
    dkp = Path('C:/devkitPro')
os.environ['DEVKITPRO'] = dkp.as_posix()
suffix = '.exe' if os.name == 'nt' else ''
cxx = dkp / 'devkitA64/bin' / ('aarch64-none-elf-g++' + suffix)
tools = dkp / 'tools/bin'
port = dkp / 'portlibs/switch'
build = root / 'build/local-cards'
build.mkdir(parents=True, exist_ok=True)
romfs = build / 'romfs'
for directory in ['fonts', 'icons', 'certs', 'shaders', 'icons/hx']:
    (romfs / directory).mkdir(parents=True, exist_ok=True)
for directory, pattern in [('fonts','*.ttf'), ('icons','*.png'), ('certs','*.pem')]:
    for source in (root / 'projects/cards/romfs' / directory).glob(pattern):
        shutil.copy2(source, romfs / directory / source.name)
shutil.copy2(root / 'projects/cards/romfs/lang.tsv', romfs / 'lang.tsv')
for name in ['news', 'eshop', 'controller', 'mii_editor', 'friends', 'settings']:
    shutil.copy2(root / 'romfs/icons' / (name + '.png'), romfs / 'icons/hx' / (name + '.png'))
index = root / 'build/cards-romfs/gametdb.tsv'
if index.exists(): shutil.copy2(index, romfs / index.name)
for shader in sorted((root / 'shaders').glob('*.glsl')):
    target = romfs / 'shaders' / (shader.stem + '.dksh')
    if not target.exists() or target.stat().st_mtime < shader.stat().st_mtime:
        stage = 'vert' if shader.stem.endswith('_vsh') else 'frag'
        subprocess.run([str(tools / ('uam'+suffix)), '-s', stage, '-o', str(target), str(shader)], check=True)

core = root / 'lib/nxui/src/core'
sources = [core / (name + '.cpp') for name in ['Application','Animation','I18n','Input','Theme','Font','GpuDevice','Renderer','Texture']]
sources += sorted((root / 'lib/nxui/src/widgets').glob('*.cpp'))
sources += sorted((root / 'lib/nxui/src/focus').glob('*.cpp'))
sources += sorted((root / 'projects/cards/src').glob('*.cpp'))
sources += [root / 'projects/menu/src/homebrew/HomebrewStore.cpp', root / 'projects/updater/src/Catalog.cpp']
audout = root / 'build/sdl2-audout'
archive = audout / 'switch-sdl2-2.28.5-3-any.pkg.tar.zst'
if not archive.exists() or hashlib.sha256(archive.read_bytes()).hexdigest() != 'b554bde32201f32f93a5be1a6561cf2abb9fd7755e00ebbce8a692b89cf0646e':
    raise SystemExit('Missing or incorrect pinned SDL audout package')
if not (audout / 'lib/libSDL2.a').exists(): raise SystemExit('Extract the pinned SDL package first')
includes = [audout/'include', audout/'include/SDL2', dkp/'libnx/include', port/'include', port/'include/SDL2',
            root/'lib/nxui/include', root/'lib/nxui/include/nxui/third_party/stb',
            root/'projects/common/include', root/'projects/menu/src', root/'projects/cards/src', args.json_include.resolve()]
flags = ['-std=c++20','-O3','-ffast-math','-march=armv8-a+crc+crypto','-mtune=cortex-a57','-mtp=soft',
         '-fPIE','-ffunction-sections','-fdata-sections','-frtti','-fexceptions','-D__SWITCH__','-DNXUI_BACKEND_DEKO3D',
         '-DCURL_STATICLIB','-DSWITCHU_VERSION="1.2.0"','-DHOMENX_BUILD="local XMB smooth-2"']
flags += ['-I'+str(p) for p in includes]

def compile(source):
    obj = build / (str(source.relative_to(root)).replace('\\','_').replace('/','_') + '.o')
    command = [str(cxx), *flags, '-c', str(source), '-o', str(obj)]
    # Recompile on source/header changes; the digest includes all headers below.
    stamp = obj.with_suffix('.stamp')
    key = hashlib.sha256((' '.join(command)+header_digest+hashlib.sha256(source.read_bytes()).hexdigest()).encode()).hexdigest()
    if obj.exists() and stamp.exists() and stamp.read_text() == key: return obj
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(str(source.relative_to(root))+'\n'+result.stdout+result.stderr)
    stamp.write_text(key)
    print('Compiled', source.relative_to(root), flush=True)
    return obj

headers = []
for parent in ['lib/nxui/include','projects/cards/src','projects/common/include','projects/menu/src']:
    headers += sorted((root/parent).rglob('*.hpp'))
header_digest = hashlib.sha256(b''.join(p.read_bytes() for p in headers)).hexdigest()
with ThreadPoolExecutor(max_workers=args.jobs) as pool:
    objects = list(pool.map(compile, sources))
elf = build / 'CardsNX.elf'
libs = ['SDL2_ttf','harfbuzz-subset','harfbuzz','freetype','png16','bz2','z',
        'SDL2_mixer','FLAC++','FLAC','vorbisidec','ogg','modplug','mpg123','opusurl','opusfile','opus',
        'SDL2','EGL','glapi','drm_nouveau','deko3d','curl','minizip','webp','webpdemux','nx','m']
command = [str(cxx), '-specs='+str(dkp/'libnx/switch.specs'), '-march=armv8-a+crc+crypto', '-mtune=cortex-a57',
           '-mtp=soft','-fPIE','-Wl,--gc-sections','-Wl,-Map='+str(build/'CardsNX.map'),'-o',str(elf)]
command += [str(obj) for obj in objects]
command += ['-L'+str(p) for p in [audout/'lib', port/'lib', dkp/'libnx/lib']]
command += ['-Wl,--start-group'] + ['-l'+name for name in libs] + ['-Wl,--end-group']
print('Linking CardsNX.elf', flush=True)
subprocess.run(command, check=True)
nacp = build / 'CardsNX.nacp'
subprocess.run([str(tools/('nacptool'+suffix)), '--create', 'HomeNX XMB', 'HomeNX contributors', '1.2.0-xmb2', str(nacp)],check=True)
nro = build / 'CardsNX.nro'
subprocess.run([str(tools/('elf2nro'+suffix)),str(elf),str(nro),'--nacp='+str(nacp),
                '--icon='+str(root/'projects/cards/icon.jpg'),'--romfsdir='+str(romfs)], check=True)
print('Built', nro, 'SHA256', hashlib.sha256(nro.read_bytes()).hexdigest(), flush=True)
