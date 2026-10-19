import subprocess, pathlib, json, re, hashlib
W=pathlib.Path(__file__).resolve().parent; E=W/'output'; E.mkdir(exist_ok=True); records=[]
def run(cmd,stem):
 p=subprocess.run(list(map(str,cmd)),capture_output=True,timeout=180)
 (E/(stem+'.log')).write_bytes(p.stdout+p.stderr)
 return p
src=E/'frames.y4m'
p=run(['ffmpeg','-y','-v','error','-f','lavfi','-i','testsrc2=size=320x240:rate=24','-frames:v','24','-pix_fmt','yuv420p',src],'fixture'); assert p.returncode==0
for order in ['tff','bff']:
 fields=E/(order+'.y4m')
 assert run(['ffmpeg','-y','-v','error','-i',src,'-vf',f'setfield={order},separatefields',fields],order+'-fixture').returncode==0
 for preset,adapt,bframes in [('ultrafast',0,0),('veryfast',0,2),('medium',1,2),('medium',2,2)]:
  for typ in [3,4,5]:
   pair=[]
   for split in [True,False]:
    name=f'{order}-{preset}-adapt{adapt}-b{bframes}-type{typ}-'+('split' if split else 'fields'); out=E/(name+'.hevc')
    opts=['--preset',preset,'--b-adapt',str(adapt),'--bframes',str(bframes),'--interlace',order,'--frame-packing',str(typ),'--no-info','--pools','2','--frame-threads','1','--keyint','12','--min-keyint','12','--no-scenecut','--no-aud','--no-repeat-headers','--single-sei']
    cmd=[W/'build-combined/x265',*opts,'--input',src if split else fields,*(['--field'] if split else []),'-o',out]
    p=run(cmd,name); assert p.returncode==0 and out.stat().st_size>0,(name,p.stderr)
    p=run(['ffmpeg','-v','info','-threads','1','-i',out,'-vf','showinfo','-f','null','-'],name+'-decode'); assert p.returncode==0
    log=(p.stdout+p.stderr).decode(); count=len(re.findall(r'\bn:\s*\d+\s+pts:',log)); assert count==48,(name,count)
    sides=re.findall(r'Stereo 3D: type - ([^,]+), view - (\w+)',log)
    assert len(sides)==48,(name,sides)
    if typ==5: assert ''.join(v[0].upper() for _,v in sides)=='LLRR'*12,(name,sides)
    else: assert all(t=={3:'side by side',4:'top and bottom'}[typ] for t,_ in sides)
    p=run(['python3',W/'fpa_dump.py',out],name+'-parser'); assert p.returncode==0
    assert f'type={typ} ' in p.stdout.decode()
    p=run(['ffmpeg','-v','info','-i',out,'-c:v','copy','-bsf:v','trace_headers','-f','null','-'],name+'-headers'); assert p.returncode==0
    log=(p.stdout+p.stderr).decode(); assert 'Invalid SEI' not in log and 'payload_size too large' not in log
    parity=list(map(int,re.findall(r'pic_struct\s+[01]+\s+=\s+(\d+)',log)))
    assert parity.count(1)==parity.count(2)==24,(name,parity)
    sha=hashlib.sha256(out.read_bytes()).hexdigest(); pair.append(sha)
    records.append(dict(name=name,command=list(map(str,cmd)),pictures=count,parity_counts={1:parity.count(1),2:parity.count(2)},sha256=sha))
   assert pair[0]==pair[1],(name,'split vs presplit bytes differ',pair)
# The pre-999 baseline must reject the exact newly enabled combination.
p=run([W/'build-baseline/x265','--preset','ultrafast','--interlace','tff','--field','--frame-packing','5','--input',src,'-o',E/'baseline-rejected.hevc'],'baseline-rejected')
assert b'Adaptive B-frame decision method should be closed' in p.stderr
assert (E/'baseline-rejected.hevc').stat().st_size==0
(E/'results.json').write_text(json.dumps(records,indent=2)+'\n'); print('PASS: 48 encodes, 24 split/presplit byte comparisons, before-control rejected, 48 decoder and header/parser checks')
