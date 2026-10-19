import sys
def nals(d):
    i=0; n=len(d); starts=[]
    while True:
        j=d.find(b'\x00\x00\x01',i)
        if j<0: break
        starts.append(j+3); i=j+3
    for k,s in enumerate(starts):
        e=starts[k+1]-3 if k+1<len(starts) else n
        while e>s and d[e-1]==0: e-=1
        yield d[s:e]
def unescape(b):
    out=bytearray(); z=0
    for c in b:
        if z>=2 and c==3: z=0; continue
        out.append(c); z=z+1 if c==0 else 0
    return bytes(out)
class BR:
    def __init__(s,b): s.b=b; s.p=0
    def u(s,n):
        v=0
        for _ in range(n):
            v=(v<<1)|((s.b[s.p>>3]>>(7-(s.p&7)))&1); s.p+=1
        return v
    def ue(s):
        z=0
        while s.u(1)==0: z+=1
        return (1<<z)-1+(s.u(z) if z else 0)
def fpa(b):
    r=BR(b); f={}
    f['id']=r.ue(); f['cancel']=r.u(1)
    f['type']=r.u(7); q=r.u(1); f['quincunx']=q
    f['content']=r.u(6); f['spatial_flip']=r.u(1); f['f0_flipped']=r.u(1)
    f['field_views']=r.u(1); f['is_frame0']=r.u(1); r.u(2)
    if not q and f['type']!=5: r.u(16)
    r.u(8); f['persist']=r.u(1); f['upsampled']=r.u(1)
    return f
d=open(sys.argv[1],'rb').read()
pend={}; au={}; rows=[]
for nal in nals(d):
    h=(nal[0]<<8)|nal[1]; t=(h>>9)&0x3f; lid=(h>>3)&0x3f
    body=unescape(nal[2:])
    if t in (39,40):
        p=0
        while p<len(body)-1:
            pt=0
            while body[p]==255: pt+=255; p+=1
            pt+=body[p]; p+=1
            ps=0
            while body[p]==255: ps+=255; p+=1
            ps+=body[p]; p+=1
            if pt==45: pend[lid]=fpa(body[p:p+ps])
            p+=ps
            if p<len(body) and body[p]==0x80 and p==len(body)-1: break
    elif t<32:
        if body[0]&0x80:
            au[lid]=au.get(lid,-1)+1
            rows.append((au[lid],lid,t,pend.pop(lid,None)))
        else: pend.pop(lid,None) if False else None
print("pic layer nal_type  FPA(type frame0 view persist content)")
vm={}
for a,l,t,f in rows:
    if f is None: s='-'
    else: s="type=%d frame0=%d view=%s persist=%d content=%d"%(f['type'],f['is_frame0'],'L' if f['is_frame0'] else 'R',f['persist'],f['content']) if f['type']==5 else "type=%d persist=%d content=%d (L left/R right per type)"%(f['type'],f['persist'],f['content'])
    print("%3d %5d %8d  %s"%(a,l,t,s))
seq=''.join(('L' if f['is_frame0'] else 'R') for a,l,t,f in rows if f and f['type']==5 and l==0)
if seq: print("type5 view sequence (layer 0): "+' '.join(seq))
