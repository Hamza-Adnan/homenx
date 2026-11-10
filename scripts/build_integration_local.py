"""Build NXToggle and the three-style HOME frontend with installed devkitPro libraries.
Requires the espeak-ng submodule plus json/fmt/curlpp sources under --deps.
A matching upstream distribution supplies the unchanged daemon and runtime assets.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse, hashlib, os, re, shutil, subprocess
ap=argparse.ArgumentParser();ap.add_argument('--deps',type=Path,required=True);ap.add_argument('--jobs',type=int,default=6)
a=ap.parse_args();root=Path(__file__).resolve().parents[1];os.chdir(root);deps=a.deps.resolve()
dkp=Path(os.environ.get('DEVKITPRO','C:/devkitPro'))
if os.name=='nt' and not dkp.exists():dkp=Path('C:/devkitPro')
os.environ['DEVKITPRO']=dkp.as_posix();ext='.exe' if os.name=='nt' else ''
cxx=dkp/'devkitA64/bin'/('aarch64-none-elf-g++'+ext);cc=dkp/'devkitA64/bin'/('aarch64-none-elf-gcc'+ext)
tools=dkp/'tools/bin';port=dkp/'portlibs/switch';build=root/'build/local-integration';build.mkdir(parents=True,exist_ok=True)
audout=root/'build/sdl2-audout';assert (audout/'lib/libSDL2.a').exists()
shader_dir=build/'shaders';shader_dir.mkdir(exist_ok=True)
for source in sorted((root/'shaders').glob('*.glsl')):
 target=shader_dir/(source.stem+'.dksh')
 if not target.exists() or target.stat().st_mtime<source.stat().st_mtime:
  subprocess.run([str(tools/('uam'+ext)),'-s','vert' if source.stem.endswith('_vsh') else 'frag','-o',str(target),str(source)],check=True)

incs=[audout/'include',audout/'include/SDL2',dkp/'libnx/include',port/'include',port/'include/SDL2',deps,deps/'fmt/include',deps/'curlpp/include',root/'lib/nxui/include',root/'lib/nxui/include/nxui/third_party/stb',root/'projects/common/include',root/'projects/menu/src',root/'projects/manager/src',root/'projects/cards/src',root/'lib/espeak-ng/src/include']
base=['-O3','-ffast-math','-march=armv8-a+crc+crypto','-mtune=cortex-a57','-mtp=soft','-fPIE','-ffunction-sections','-fdata-sections','-D__SWITCH__','-DNXUI_BACKEND_DEKO3D','-DCURL_STATICLIB','-DFMT_HEADER_ONLY','-DSWITCHU_VERSION="1.2.0"','-DHOMENX_BUILD="local XMB integrated-3"']+['-I'+str(p) for p in incs]
headers=list((root/'projects').rglob('*.hpp'))+list((root/'lib/nxui/include').rglob('*.hpp'))
header_hash=hashlib.sha256(b''.join(p.read_bytes() for p in sorted(headers))).hexdigest()
def compile(job):
 source,kind=job
 name=hashlib.sha256((str(source)+kind).encode()).hexdigest()[:12]+'_'+source.stem+'.o';obj=build/name
 flags=base+(['-std=gnu11','-fwrapv','-fvisibility=hidden','-I'+str(root/'projects/menu/src/core/espeak_config'),'-I'+str(root/'lib/espeak-ng/src/libespeak-ng'),'-I'+str(root/'lib/espeak-ng/src/ucd-tools/src/include'),'-DLIBESPEAK_NG_EXPORT=1','-D_GNU_SOURCE','-DPATH_ESPEAK_DATA="romfs:/espeak-ng-data"'] if kind=='espeak' else ['-std=c++20','-frtti','-fexceptions'])
 if kind=='menu':flags+=['-DSWITCHU_MENU','-DHOMENX_UPDATER_SHARED_NETWORK','-D_GNU_SOURCE']
 if source.suffix=='.c' and kind!='espeak':flags=[x for x in flags if x not in ['-std=c++20','-frtti','-fexceptions']]+['-std=gnu11']
 command=[str(cc if source.suffix=='.c' else cxx),*flags,'-c',str(source),'-o',str(obj)]
 digest=hashlib.sha256((' '.join(command)+header_hash).encode()+source.read_bytes()).hexdigest();stamp=obj.with_suffix('.stamp')
 if obj.exists() and stamp.exists() and stamp.read_text()==digest:return obj
 result=subprocess.run(command,capture_output=True,text=True)
 if result.returncode:raise RuntimeError(str(source)+'\n'+result.stdout+result.stderr)
 stamp.write_text(digest);print('Compiled',kind,source.name,flush=True);return obj
core=root/'lib/nxui/src/core'
nx=[core/(n+'.cpp') for n in ['Application','Animation','I18n','Input','Theme','Font','GpuDevice','Renderer','Texture']]+sorted((root/'lib/nxui/src/widgets').glob('*.cpp'))+sorted((root/'lib/nxui/src/focus').glob('*.cpp'))
common=[(p,'common') for p in nx]
manager=[(p,'manager') for p in sorted((root/'projects/manager/src').glob('*.cpp'))]+[(root/'projects/menu/src/widgets'/(n+'.cpp'),'manager') for n in ['ActionButton','OverlayDialog','SelectionCursor']]
menu=[(p,'menu') for p in sorted((root/'projects/menu/src').rglob('*.cpp'))]+[(root/'projects/menu/src/third_party/yyjson.c','menu'),(root/'projects/manager/src/ReleaseUpdater.cpp','menu')]+[(root/'projects/cards/src'/(n+'.cpp'),'menu') for n in ['Audio','CardsActivity','Library','Mtp','Spotify']]+[(root/'projects/updater/src/Catalog.cpp','menu')]
lua=(root/'xmake.lua').read_text();espeak_paths=re.findall(r'add_files\("(lib/espeak-ng/[^"\n]+\.c)"\)',lua)
espeak=[(root/p,'espeak') for p in espeak_paths]
curlpp=[(p,'curlpp') for p in sorted((deps/'curlpp/src/curlpp').rglob('*.cpp'))]
libs=['SDL2_ttf','harfbuzz-subset','harfbuzz','freetype','png16','bz2','z','SDL2_mixer','FLAC++','FLAC','vorbisidec','ogg','modplug','mpg123','opusurl','opusfile','opus','SDL2','EGL','glapi','drm_nouveau','deko3d','curl','minizip','webp','webpdemux','mbedtls','mbedx509','mbedcrypto','nx','m']
def link(name,objects):
 elf=build/(name+'.elf');command=[str(cxx),'-specs='+str(dkp/'libnx/switch.specs'),'-march=armv8-a+crc+crypto','-mtune=cortex-a57','-mtp=soft','-fPIE','-Wl,--gc-sections','-Wl,-Map='+str(build/(name+'.map')),'-o',str(elf),*[str(x) for x in objects]]
 command+=['-L'+str(p) for p in [audout/'lib',port/'lib',dkp/'libnx/lib']]+['-Wl,--start-group']+['-l'+n for n in libs]+['-Wl,--end-group']
 print('Linking',name,flush=True);subprocess.run(command,check=True);return elf
with ThreadPoolExecutor(max_workers=a.jobs) as pool:
 common_obj=list(pool.map(compile,common));manager_obj=list(pool.map(compile,manager))
 elf=link('NXToggle',common_obj+manager_obj)
 romfs=build/'manager-romfs';(romfs/'fonts').mkdir(parents=True,exist_ok=True);(romfs/'i18n').mkdir(exist_ok=True)
 shutil.copy2(root/'romfs/fonts/DejaVuSans.ttf',romfs/'fonts/DejaVuSans.ttf');shutil.copy2(root/'projects/manager/icon.jpg',romfs/'icon.jpg')
 for p in (root/'projects/manager/romfs/i18n').glob('*.json'):shutil.copy2(p,romfs/'i18n'/p.name)
 (romfs/'shaders').mkdir(exist_ok=True)
 for p in shader_dir.glob('*.dksh'):shutil.copy2(p,romfs/'shaders'/p.name)
 nacp=build/'NXToggle.nacp';subprocess.run([str(tools/('nacptool'+ext)),'--create','NXToggle','HomeNX contributors','1.2.0-xmb3',str(nacp)],check=True)
 subprocess.run([str(tools/('elf2nro'+ext)),str(elf),str(build/'NXToggle.nro'),'--nacp='+str(nacp),'--icon='+str(root/'projects/manager/icon.jpg'),'--romfsdir='+str(romfs)],check=True)
 print('Built NXToggle.nro',flush=True)
 menu_obj=list(pool.map(compile,menu));espeak_obj=list(pool.map(compile,espeak));curl_obj=list(pool.map(compile,curlpp))
 elf=link('switchu-menu',common_obj+menu_obj+espeak_obj+curl_obj)
 exefs=build/'menu';exefs.mkdir(exist_ok=True)
 subprocess.run([str(tools/('elf2nso'+ext)),str(elf),str(exefs/'main')],check=True)
 subprocess.run([str(tools/('npdmtool'+ext)),str(root/'projects/menu/menu.json'),str(exefs/'main.npdm')],check=True)
 print('Built HOME frontend',flush=True)
