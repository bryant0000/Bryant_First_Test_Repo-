/* Same-origin room sessions. Game commands are checked and settled by the server. */
(function(){
'use strict';
const SESSION_KEY='cashflow-online-session-v1',BACKUP_KEY='cashflow-offline-backup-v1';
let session=null,room=null,inFlight=false,pollTimer=null,mode='offline',lastVersion=-1,creating=false,pendingJoin=null;
const supported=/^https?:$/.test(location.protocol);
const modeBar=document.createElement('div');modeBar.id='play-modes';modeBar.innerHTML='<button id="offline-mode" class="secondary">同屏游戏</button><button id="online-mode" class="secondary">联机房间</button>';$('setup').before(modeBar);
const panel=document.createElement('section');panel.id='online-panel';panel.className='panel hidden';panel.innerHTML=`<div id="room-browser"><h2>选择一个游戏房间</h2><p>创建房间，或从列表加入。所有玩家准备后，由房主开始游戏。</p><button id="show-room-create" class="room-list-item"><b>创建新房间</b><span>→</span></button><div id="room-create-form" class="room-create-form hidden"><input id="room-player-name" type="hidden" value="玩家"><label>房间名称<input id="room-name" maxlength="32" placeholder="输入房间名称"></label><label>人数<select id="room-capacity">${[1,2,3,4,5,6].map(n=>`<option value="${n}" ${n===1?'selected':''}>${n} 人</option>`).join('')}</select></label><label>房间密码（可留空）<input id="room-password" type="password" maxlength="128" autocomplete="off"></label><button id="create-room" class="primary">创建房间</button><button id="back-room-list" class="secondary">返回房间列表</button></div><div id="room-list-section"><div class="section-head"><h3>等待加入的房间</h3><button id="refresh-rooms" class="secondary">刷新列表</button></div><div id="room-list"></div></div></div><div id="room-waiting" class="hidden"></div><p id="room-status" role="status"></p>`;modeBar.after(panel);
const joinDialog=document.createElement('dialog');joinDialog.id='join-room-dialog';joinDialog.className='game-modal confirm-modal';joinDialog.innerHTML='<h2>加入私人房间</h2><label>房间密码<input id="join-room-password" type="password" maxlength="128" autocomplete="off"></label><div class="confirm-actions"><button id="cancel-room-join" class="secondary">取消</button><button id="confirm-room-join" class="primary">加入房间</button></div>';document.body.append(joinDialog);
const capacityPicker=document.createElement('div');capacityPicker.className='room-capacity-picker';capacityPicker.innerHTML=Array.from({length:6},(_,i)=>`<button type="button" data-room-capacity="${i+1}" aria-label="${i+1} 人"><svg viewBox="0 0 60 100" aria-hidden="true"><circle cx="30" cy="15" r="9" fill="currentColor"/><path d="M30 32V66 M30 34L15 60 M30 34L45 60 M30 66L20 91 M30 66L40 91" stroke="currentColor" stroke-width="8" stroke-linecap="round" fill="none"/></svg><span>${i+1}</span></button>`).join('');$('room-password').closest('label').after(capacityPicker);$('room-capacity').closest('label').classList.add('capacity-select-label');
function capacityChanged(){const n=Number($('room-capacity').value);capacityPicker.querySelectorAll('button').forEach((b,i)=>{b.style.color=E.REFERENCE_COLORS[i];b.classList.toggle('seat-included',i<n);b.setAttribute('aria-pressed',String(i+1===n))})}capacityChanged();capacityPicker.addEventListener('click',e=>{const b=e.target.closest('[data-room-capacity]');if(b){$('room-capacity').value=b.dataset.roomCapacity;capacityChanged()}});$('room-capacity').addEventListener('change',capacityChanged);
const playing=document.createElement('div');playing.id='online-playing-status';playing.className='hidden';panel.after(playing);
const connectionNotice=document.createElement('p');connectionNotice.id='online-connection-notice';connectionNotice.className='hidden';connectionNotice.setAttribute('role','status');playing.after(connectionNotice);
const original={perform:T.perform,end:T.end,chooseDream:T.chooseDream,prepareTurn:T.prepareTurn};
function active(){return !!session&&!!room?.game}
function isMyTurn(){return active()&&game?.active===room.seat}
function player(){return active()?game?.players[room.seat]:null}
function chrome(){
 document.body.classList.toggle('online-session',!!session);document.body.classList.toggle('online-observing',active()&&!isMyTurn());document.body.classList.toggle('online-pending',inFlight);
 modeBar.classList.toggle('hidden',!!game||!!session);$('offline-mode').classList.toggle('active',mode==='offline');$('online-mode').classList.toggle('active',mode==='online');
 panel.classList.toggle('hidden',mode!=='online'||active());if(mode==='online'&&!game)$('setup').classList.add('hidden');
 playing.classList.toggle('hidden',!active());if(active())playing.innerHTML=`<span>${esc(room.name)} · ${isMyTurn()?'轮到你行动':'等待 '+esc(game.players[game.active].name)} · 你是 ${esc(player().name)}</span><button data-room-leave class="secondary">退出房间</button>`;else playing.innerHTML='';
 $('room-create-form').classList.toggle('hidden',!creating);$('show-room-create').classList.toggle('hidden',creating);$('room-list-section').classList.toggle('hidden',creating);$('room-browser').querySelector('h2').textContent=creating?'设置你的房间':'选择一个游戏房间';$('create-room').disabled=inFlight||!$('room-name').value.trim();$('refresh-rooms').disabled=inFlight;
}
const beforeRender=render;render=function(){beforeRender();chrome()};
function status(message){$('room-status').textContent=message;connectionNotice.textContent=message;connectionNotice.classList.toggle('hidden',!message||!session)}
async function api(route,body,token=session?.token){
 const headers={};if(token)headers.Authorization='Bearer '+token;if(body!==undefined)headers['Content-Type']='application/json';
 const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),10000);let response;try{response=await fetch('/api/rooms'+route,{method:body===undefined?'GET':'POST',headers,body:body===undefined?undefined:JSON.stringify(body),cache:'no-store',signal:controller.signal})}catch(error){throw Error(error.name==='AbortError'?'连接超时，正在尝试恢复房间连接':'暂时无法连接房间服务，正在重试')}finally{clearTimeout(timeout)}
 let data;try{data=await response.json()}catch{throw Error('联机服务尚未启动，请使用服务器地址打开游戏')}
 if(!response.ok)throw Object.assign(new Error(data.error||'联机操作失败'),{status:response.status});return data;
}
function waiting(){
 $('room-browser').classList.toggle('hidden',!!session);$('room-waiting').classList.toggle('hidden',!session||active());if(!session||active()){$('room-waiting').innerHTML='';return;}
 if(!room){$('room-waiting').textContent='正在恢复房间连接…';return;}
 const present=room.players.filter(p=>!p.left&&!p.away),self=present.find(p=>p.seat===room.seat),ready=present.length===room.capacity&&present.every(p=>p.ready);
 $('room-waiting').innerHTML=`<h2>${esc(room.name)}</h2><label class="waiting-name-label">你的名字<input id="waiting-player-name" maxlength="8" value="${esc(self?.name||'玩家')}"></label><p>等待玩家加入并准备 · ${present.length}/${room.capacity} 人</p><div class="room-seats">${room.players.filter(p=>!p.left).map(p=>`<div><strong>${esc(p.name)}${p.seat===room.host?' · 房主':''}</strong><span>${p.away?'暂时离线':p.ready?'已准备':'尚未准备'}${p.seat===room.seat?' · 你':''}</span></div>`).join('')}</div><div class="event-buttons"><button id="room-ready" class="secondary">${self?.ready?'取消准备':'我已准备'}</button>${room.seat===room.host?`<button id="start-room" class="primary" ${ready?'':'disabled'}>开始游戏</button>`:''}<button data-room-leave class="secondary">退出房间</button></div>`;
}
function apply(view,{paint=true}={}){
 if(view.version<lastVersion)return;const keepObserverFinances=active()&&!isMyTurn()&&view.game?.active!==view.seat&&$('finance-dialog')?.open;lastVersion=view.version;room=view;mode='online';
 if(view.game){game=view.game;game.onlineRoomId=view.id;state=T.current(game);save();if(paint){if(!window.CashflowUI?.docked()&&$('finance-dialog')?.open)$('finance-dialog').close();render();if(keepObserverFinances&&!window.CashflowUI?.docked())switchTab('statement')}}else{game=null;state=null;save();if(paint)render()}
 waiting();chrome();
}
async function refreshRooms(){if(!supported)return;try{const data=await api('',undefined,null);$('room-list').innerHTML=data.rooms.length?data.rooms.map(r=>`<button class="room-list-item" data-room-join="${esc(r.id)}" data-room-private="${r.private?1:0}"><b>${esc(r.name)}</b><span>${r.players}/${r.capacity} 人${r.private?' · 需要密码':''}</span><span>加入 →</span></button>`).join(''):'<p>还没有等待中的房间，可以创建一个。</p>';status('')}catch(error){status(error.message)}}
function schedulePoll(){clearTimeout(pollTimer);if(session)pollTimer=setTimeout(poll,900)}
async function poll(){if(!session)return;if(inFlight||window.CashflowUI?.moving()){schedulePoll();return}const requestSession=session;try{const next=await api('/'+requestSession.id,undefined,requestSession.token);if(session!==requestSession)return;if(next.version!==lastVersion)apply(next);else if(next.chatRevision!==room?.chatRevision){room.chat=next.chat;room.chatRevision=next.chatRevision;window.ClassicLog?.refresh()}status('')}catch(error){if(session!==requestSession)return;status(error.message);if([401,404].includes(error.status)){await disconnect();return}}schedulePoll()}
function remember(view){if(!session)try{localStorage.setItem(BACKUP_KEY,JSON.stringify(game))}catch{}session={id:view.id,token:view.token};try{localStorage.setItem(SESSION_KEY,JSON.stringify(session))}catch{}lastVersion=-1;apply(view);schedulePoll()}
async function connect(joinId,password){if(inFlight||session)return;inFlight=true;chrome();try{const body={playerName:$('room-player-name').value,password:joinId?password||'':$('room-password').value};const next=joinId?await api('/'+joinId+'/join',body,null):await api('',{...body,name:$('room-name').value,capacity:Number($('room-capacity').value)},null);remember(next);creating=false;$('room-password').value='';$('join-room-password').value='';status('')}catch(error){status(error.message)}finally{inFlight=false;chrome()}}
async function command(operation,body={},paint=true){if(!session||inFlight)return false;inFlight=true;chrome();try{const next=await api('/'+session.id+'/'+operation,{...body,version:lastVersion});if(next.left){await disconnect();return true}if(operation==='chat'&&next.version===lastVersion){room.chat=next.chat;room.chatRevision=next.chatRevision;window.ClassicLog?.refresh()}else apply(next,{paint});status('');return true}catch(error){status(error.message);toast(error.message);try{apply(await api('/'+session.id))}catch{}return false}finally{inFlight=false;chrome();schedulePoll()}}
async function disconnect(){clearTimeout(pollTimer);session=null;room=null;lastVersion=-1;mode='online';try{localStorage.removeItem(SESSION_KEY);game=JSON.parse(localStorage.getItem(BACKUP_KEY)||'null');localStorage.removeItem(BACKUP_KEY)}catch{game=null}state=game?T.current(game):null;mode=game?'offline':'online';save();waiting();render();await refreshRooms()}
function sendAction(action,args=[]){return command('action',{action,args})}
T.perform=function(g,action,...args){return session?(active()?sendAction(action,args):false):original.perform(g,action,...args)};
T.end=function(g){return session?(active()?sendAction('end'):false):original.end(g)};
T.chooseDream=function(g,id){return session?(active()?sendAction('chooseDream',[id]):false):original.chooseDream(g,id)};
T.prepareTurn=function(g){if(!session)original.prepareTurn(g)};
window.OnlineGame={get active(){return active()},isMyTurn,player,get busy(){return inFlight},action:sendAction,get messages(){return room?.chat||[]},sendMessage:message=>command('chat',{message}),roll:count=>command('action',{action:'roll',args:[count]},false)};
$('offline-mode').addEventListener('click',()=>{mode='offline';render()});$('online-mode').addEventListener('click',()=>{mode='online';render();refreshRooms()});
$('show-room-create').addEventListener('click',()=>{creating=true;chrome()});$('back-room-list').addEventListener('click',()=>{creating=false;chrome();refreshRooms()});$('cancel-room-join').addEventListener('click',()=>joinDialog.close());$('confirm-room-join').addEventListener('click',()=>{joinDialog.close();connect(pendingJoin,$('join-room-password').value)});$('join-room-password').addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();$('confirm-room-join').click()}});
$('room-name').addEventListener('input',chrome);$('create-room').addEventListener('click',()=>connect());$('refresh-rooms').addEventListener('click',refreshRooms);
document.addEventListener('click',event=>{
 const join=event.target.closest('[data-room-join]');if(join){if(join.dataset.roomPrivate==='1'){pendingJoin=join.dataset.roomJoin;$('join-room-password').value='';joinDialog.showModal()}else connect(join.dataset.roomJoin);return}
 if(event.target.closest('[data-online-exit]')){gameConfirm('确定退出当前房间吗？其他玩家将继续游戏。').then(yes=>{if(yes)command('leave')});return}
 if(event.target.closest('[data-room-leave]')){command('leave');return}
 if(event.target.closest('#room-ready')){const self=room.players.find(p=>p.seat===room.seat);command('ready',{ready:!self.ready});return}
 if(event.target.closest('#start-room')){command('start');return}
 const gameCommand=event.target.closest('[data-turn-dice],[data-action],#begin-turn,#turn-borrow,#turn-repay,#end-turn,#roll,[data-ui],[data-repay],[data-debt-choice],[data-sell]');
 if(session&&gameCommand&&(inFlight||!isMyTurn())){event.preventDefault();event.stopImmediatePropagation()}
},true);
document.addEventListener('change',event=>{if(event.target.id==='waiting-player-name'&&session&&!active())command('rename',{name:event.target.value})});
document.addEventListener('keydown',event=>{if(session&&(inFlight||!isMyTurn())&&['r','e'].includes(event.key.toLowerCase())){event.preventDefault();event.stopImmediatePropagation()}},true);
if(!supported){$('online-mode').disabled=true;$('online-mode').title='联机模式需要通过服务器地址打开';chrome();return}
try{const saved=JSON.parse(localStorage.getItem(SESSION_KEY));if(saved?.id&&saved?.token){session=saved;mode='online';waiting();poll()}else if(!game){mode='online';refreshRooms()}}catch{}
chrome();
})();
