'use strict';
const $=id=>document.getElementById(id),esc=value=>String(value==null?'':value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let snapshot=null,filter='Tümü',lastCards=null;
const colors={'Müsait':'#16a34a','Görüşmede':'#dc2626','Çalıyor':'#f97316','Çevrimdışı':'#9aa6b6','Beklemede':'#dc2626','Bilinmiyor':'#8993a0'};
const telephone='<svg viewBox="0 0 36 34" aria-hidden="true"><path class="phone-base" d="M9 15h18l5 12a2 2 0 0 1-2 3H6a2 2 0 0 1-2-3Z"/><path class="receiver" d="M4 12V8C4 2 32 2 32 8v4h-7V9a22 22 0 0 0-14 0v3Z"/><circle class="dial-rim" cx="18" cy="22" r="6.5"/><circle class="status-dot" cx="18" cy="22" r="4.8"/></svg>';
function render(){
  if(!snapshot)return;
  const fresh=snapshot.connected,people=snapshot.extensions||[],calls=snapshot.calls||[],queues=snapshot.queues||[];
  $('connection').textContent=fresh?'● Canlı bağlantı · AMI / SSE':'● Bağlantı yok · veriler güncel değil';
  $('connection').style.background=fresh?'#dff2e9':'#fce2e2';
  $('warning').hidden=fresh;
  $('warning').textContent=snapshot.error||'Bağlantı kesildi. Son alınan veriler gösteriliyor.';
  $('lastUpdate').textContent=snapshot.updated?'Son veri: '+new Date(snapshot.updated*1000).toLocaleString('tr-TR',{timeZone:'Europe/Istanbul'}):'Henüz veri alınmadı';
  $('stats').innerHTML=[['Toplam dahili',people.length],['Müsait',people.filter(p=>p.status==='Müsait').length],['Aktif çağrı',calls.length],['Kuyrukta bekleyen',queues.reduce((n,q)=>n+q.waiting,0)],['Kayıtlı trunk',(snapshot.trunks||[]).filter(t=>t.registered).length],['Kayıtsız trunk',(snapshot.trunks||[]).filter(t=>!t.registered).length]].map(([label,n])=>`<div class="stat">${label}<strong>${fresh?n:'—'}</strong></div>`).join('');
  $('filters').innerHTML=['Tümü',...Object.keys(colors)].map(s=>`<button class="${s===filter?'active':''}" data-filter="${s}">${s} · ${s==='Tümü'?people.length:people.filter(p=>p.status===s).length}</button>`).join('');
  const query=$('search').value.toLocaleLowerCase('tr');
  const list=people.filter(p=>(filter==='Tümü'||p.status===filter)&&`${p.id} ${p.name}`.toLocaleLowerCase('tr').includes(query));
  $('empty').hidden=list.length>0;
  const cards=list.map(p=>{const status=fresh?p.status:'Güncel değil',talking=fresh&&['Görüşmede','Beklemede'].includes(p.status);return `<article class="card live-card" data-status="${esc(status)}" style="--color:${fresh?(colors[p.status]||'#8993a0'):'#8993a0'}"><h3 class="identity" title="${esc(p.id)} ${esc(p.name||'')}"><span class="number">${esc(p.id)}</span><span class="identity-divider" aria-hidden="true">│</span><span class="person-name">${esc(p.name&&p.name!==p.id?p.name:'Dahili')}</span></h3><span class="phone-icon ${talking?'off-hook':''}" aria-hidden="true">${telephone}</span><div class="dept">${esc(p.technology||'Dahili')}</div><div class="status">${esc(status)}</div></article>`}).join('');
  if(lastCards!==cards){$('cards').innerHTML=cards;lastCards=cards;}
  $('calls').innerHTML=calls.length?calls.map(c=>`<div class="call compact-call" data-state="${esc(c.state)}"><strong>${esc(c.from||'Gizli numara')} <span class="call-arrow">→</span> ${esc(c.to||'Hedef bekleniyor')}${c.to_name&&c.to_name!==c.to?' '+esc(c.to_name):''}</strong><span class="call-state">${fresh?esc(c.state):'Güncel değil'}</span><time>${Math.floor(c.seconds/60)}:${String(c.seconds%60).padStart(2,'0')}</time></div>`).join(''):'<p class="small">'+(fresh?'Aktif çağrı yok.':'Güncel çağrı verisi alınamıyor.')+'</p>';
  $('queueContent').innerHTML=queues.length?queues.map(q=>`<div class="queue"><div class="row"><b>${esc(q.id)}</b><span>${q.waiting} bekleyen</span></div><div class="bar"><i style="width:${q.members?Math.round(q.available/q.members*100):0}%"></i></div><span class="small">${q.available} müsait / ${q.members} temsilci</span></div>`).join(''):'<p class="small">'+(fresh?'Tanımlı kuyruk bulunamadı.':'Kuyruk verisi alınamıyor.')+'</p>';
  $('trunks').innerHTML=(snapshot.trunks||[]).length?snapshot.trunks.map(t=>`<div class="resource-tile trunk-tile"><div class="trunk-registration"><i class="trunk-led ${fresh?(t.registered?'registered':'unregistered'):'unknown'}"></i><b>${fresh?esc(t.registration_state):'Güncel değil'}</b></div><span class="icon">⇄</span><strong>${esc(t.technology)} / ${esc(t.id)}</strong><span>${esc(t.status)}</span></div>`).join(''):'<p class="small">Trunk kaydı bulunamadı.</p>';
}
let feed=null,lastSignal=Date.now(),transportOnline=false;
function markLive(online){transportOnline=online;const node=$('liveIndicator');node.classList.toggle('online',online);node.classList.toggle('offline',!online);$('liveLabel').textContent=online?'CANLI':'BAĞLANIYOR';}
function connect(){
  if(feed)feed.close();
  feed=new EventSource('index.php?events=1');
  feed.addEventListener('state',event=>{try{snapshot=JSON.parse(event.data);lastSignal=Date.now();markLive(snapshot.connected);render();}catch(error){markLive(false);}});
  feed.addEventListener('heartbeat',()=>{lastSignal=Date.now();markLive(Boolean(snapshot&&snapshot.connected));});
  feed.addEventListener('reconnect',()=>{feed.close();connect();});
  feed.onerror=()=>{markLive(false);if(snapshot){snapshot.connected=false;snapshot.error='Canlı bağlantı kesildi; yeniden bağlanılıyor.';render();}};
}
setInterval(()=>{if(Date.now()-lastSignal>25000){markLive(false);if(snapshot&&snapshot.connected){snapshot.connected=false;snapshot.error='Canlı bağlantıdan yanıt alınamıyor.';render();}}else if(snapshot&&transportOnline){document.querySelectorAll('.compact-call time').forEach((node,i)=>{const c=snapshot.calls[i];if(c){const elapsed=c.seconds+Math.max(0,Math.floor(Date.now()/1000-snapshot.updated));node.textContent=Math.floor(elapsed/60)+':'+String(elapsed%60).padStart(2,'0');}});}},1000);
$('search').oninput=render;$('filters').onclick=e=>{if(e.target.dataset.filter){filter=e.target.dataset.filter;render()}};
connect();
