const log=document.getElementById('log'),q=document.getElementById('q');
let state=null;
const el=(t,c,x)=>{const d=document.createElement(t);if(c)d.className=c;if(x!==undefined)d.textContent=x;return d};
const say=(t,c)=>{log.appendChild(el('div','m '+c,t));log.scrollTop=log.scrollHeight};
function card(r){
  const d=el('div','card '+r.chance);
  d.append(el('div','tag',r.chance+' chance'),el('h3','',r.college_name),
    el('div','meta','Code '+r.college_code+' | '+r.branch),
    el('div','meta',r.district+' | '+r.college_type));
  const n=el('div','nums');n.innerHTML='<div><b>'+r.historical_cutoff+'</b>'+r.year+' cutoff</div><div><b>'+r.student_cutoff+'</b>Your cutoff</div>';
  d.append(n,el('div','why',r.reason));
  const b=el('button','','View details');const det=el('div','detail');det.hidden=true;
  b.onclick=async()=>{if(!det.hidden){det.hidden=true;return}
    const j=await (await fetch('/api/college/'+encodeURIComponent(r.college_code)+'?community='+r.community)).json();
    det.textContent=j.error||('College code '+j.college_code+', '+j.district+', '+j.college_type+'\n'+
      (Array.isArray(j.branches)?j.branches.map(x=>x.branch+' ('+x.community+'): '+(x.cutoff??'data unavailable')+(x.year?' in '+x.year:'')).join('\n'):j.branches));
    det.style.whiteSpace='pre-wrap';det.hidden=false};
  d.append(b,det);return d}
async function send(text){
  if(!text.trim())return;say(text,'me');
  try{
    const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:text,state})});
    const j=await r.json();state=j.state;say(j.reply,'bot');
    if(j.results&&j.results.cards.length){const w=el('div','cards');j.results.cards.forEach(c=>w.append(card(c)));log.appendChild(w);log.scrollTop=log.scrollHeight}
  }catch(e){say('Could not reach the server. Check your connection and try again.','bot')}
}
document.getElementById('f').onsubmit=e=>{e.preventDefault();const v=q.value;q.value='';send(v)};
['Show colleges','Show more','Show safe','Show ambitious','Show government colleges','Reset'].forEach(t=>{
  const b=el('button','chip',t);b.type='button';b.onclick=()=>send(t);document.getElementById('chips').append(b)});
say("Vanakkam! I'll recommend engineering colleges from historical TNEA cutoffs. What is your Maths mark (0-100)? You can also say things like \"I got 90 in physics\".",'bot');
