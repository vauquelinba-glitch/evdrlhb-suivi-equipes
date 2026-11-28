"""Build the homepage youth snapshot from FFHandball HTML component data.
Usage: python scripts/update_youth.py /absolute/path/to/ffresearch
The research folder contains full season round responses; never infer missing results.
"""
from pathlib import Path
import json,sys,re,datetime
root=Path(sys.argv[1]);site=Path(__file__).resolve().parents[1]/'index.html'
configs=[('u15','u15','-15 garçons'),('u17a','u17a-198516','-17 A filles'),('u17b','u17b','-17 B filles'),('u13','u13','-13 garçons'),('u14','u14','-14 filles')]
result=[]
for key,fn,label in configs:
 obj=json.loads((root/(fn+'.json')).read_text());d=obj['data'];sel=d['competitions---poule-selector']['selected_poule'];base=obj['url'].split('/poule-')[0].rstrip('/')+'/poule-'+sel['ext_pouleId']+'/'
 league=d['competitions---mini-classement-or-ads']['classements'];ours=[x for x in league if 'VAL DE REUIL' in x['equipe_libelle']];assert len(ours)==1
 standings=[dict(id=x['equipeId'],name=x['equipe_libelle'],rank=int(x['place']),points=int(x['point']),played=int(x['joue']),won=int(x['gagne']),draw=int(x['nul']),lost=int(x['perdu']),gf=int(x['butPlus']),ga=int(x['butMoins']),diff=int(x['diff'])) for x in league]
 games={}
 rounds=json.loads(sel['journees'])
 for day in rounds:
  path=root/(key+'-j'+str(day['journee_numero'])+'.json');assert path.exists(),str(path)
  data=json.loads(path.read_text())['data'];assert data['competitions---poule-selector']['selected_poule']['ext_pouleId']==sel['ext_pouleId']
  for m in data['competitions---rencontre-list']['rencontres']:games[m['id']]=m
 stats={x['id']:dict(n=0,gf=0,ga=0,excluded=0) for x in standings};fixtures=[]
 for m in games.values():
  a,b=m['equipe1Id'],m['equipe2Id'];s,t=m['equipe1Score'],m['equipe2Score']
  if s is not None or t is not None:
   if s is None or t is None or not str(s).isdigit() or not str(t).isdigit():
    for x in (a,b):
     if x in stats:stats[x]['excluded']+=1
    continue
   for x,gf,ga in [(a,int(s),int(t)),(b,int(t),int(s))]:
    if x in stats:stats[x]['n']+=1;stats[x]['gf']+=gf;stats[x]['ga']+=ga
  elif ours[0]['equipeId'] in (a,b):
   fixtures.append(dict(id=m['ext_rencontreId'],home=a,away=b,date=m['date'],round=int(m['journeeNumero']),source=base+'rencontre-'+m['ext_rencontreId']+'/'))
 phase=next(x['libelle'] for x in d['competitions---poule-selector']['phases'] if x['id']==sel['phaseId'])
 result.append(dict(key=key,label=label,pool=sel['libelle'],phase=phase,source=base,ourId=ours[0]['equipeId'],standings=standings,stats=stats,fixtures=fixtures,sourceUpdated=sel['dateDernierUpdateEnfants'],corrected=key in ('u17a','u14')))
blob=json.dumps({'checkedAt':'2026-11-28','teams':result},ensure_ascii=False).replace('</','<\\/')
s=site.read_text();s=re.sub(r'<script type="application/json" id="youth-data">[\s\S]*?</script>','',s)
needle='<script id="youth-ui">';pos=s.find(needle)
if pos>=0:s=s[:pos]+s[s.find('</script>',pos)+9:]
s=s.replace('</body>','<script type="application/json" id="youth-data">'+blob+'</script>\n<script id="youth-ui">'+(site.parent/'scripts/youth-ui.js').read_text()+'</script></body>')
site.write_text(s)
for t in result:print(t['label'],next(x for x in t['standings'] if x['id']==t['ourId'])['rank'],'/',len(t['standings']),len(t['fixtures']),'fixtures')
