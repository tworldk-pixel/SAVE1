import asyncio
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

import safety_quote as sq

app = FastAPI()

QUOTE_HTML = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>안전운임 조회 · 경평물류</title>
<style>  :root{
    --bg:#1B2027; --panel:#242A33; --panel-2:#2B323C; --line:#3A4250;
    --ink:#E8E4D9; --muted:#8B93A0; --muted-2:#5E6674;
    --route:#D97B33; --route-hover:#C06A28;
    --trailer:#5A8FC4; --trailer-dim:rgba(90,143,196,0.16);
    --cargo:#8FAE5A; --cargo-dim:rgba(143,174,90,0.16);
    --st-full:#B08A3E; --st-full-dim:rgba(176,138,62,0.16);
    --st-off:#C0433A; --st-off-dim:rgba(192,67,58,0.16);
  }
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Pretendard","Apple SD Gothic Neo","Malgun Gothic",sans-serif;background:var(--bg);min-height:100vh;color:var(--ink)}
header.top{padding:18px 24px 16px;border-bottom:2px solid var(--route);background:linear-gradient(180deg,var(--panel),var(--bg));display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin-bottom:0;border-radius:14px 14px 0 0}
.brand h1{font-size:20px;font-weight:800;letter-spacing:-0.01em}
.brand .eyebrow{font-size:10.5px;letter-spacing:0.12em;text-transform:uppercase;color:var(--route);font-weight:700;margin-bottom:3px}

/* ===== 콘텐츠 영역: 카드형 레이아웃(기존 다크 팔레트) ===== */
.q-wrap{max-width:none;margin:0;padding:18px 20px 40px}
.q-layout{display:block}
@media(min-width:1000px){
  .q-layout{display:grid;grid-template-columns:minmax(460px,560px) 1fr;gap:22px;align-items:start}
  .q-right{position:sticky;top:18px;max-height:calc(100vh - 36px);overflow-y:auto;padding-right:4px}
}
.full-copy-row{display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap}
.full-copy-row .btn{flex:1;min-width:150px}
.card{background:var(--panel);border-radius:14px;padding:20px 22px;box-shadow:0 4px 16px rgba(0,0,0,.2);margin-bottom:16px;color:var(--ink)}
.step-label{font-size:.72em;font-weight:800;color:var(--trailer);letter-spacing:.04em;margin-bottom:12px;text-transform:uppercase}
label{display:block;font-size:.82em;font-weight:700;color:var(--ink);margin-bottom:5px}
input,textarea,select{padding:9px 11px;border:2px solid var(--line);border-radius:8px;font-size:.92em;color:var(--ink);background:var(--panel-2);outline:none;transition:border .15s}
input:focus,textarea:focus,select:focus{border-color:var(--trailer);box-shadow:0 0 0 3px var(--trailer-dim)}
.hint{font-size:.78em;color:var(--muted);margin-top:5px;line-height:1.5}
.btn{padding:11px 18px;background:var(--route);color:#fff;border:none;border-radius:8px;font-size:.92em;font-weight:700;cursor:pointer;transition:filter .15s}
.btn:hover{filter:brightness(1.08)}
.btn:disabled{background:var(--muted-2);cursor:not-allowed}
.btn-ghost{background:var(--panel-2)!important;color:var(--ink)!important;border:1px solid var(--line)}
.addr-row{display:flex;gap:8px}
.addr-row input{flex:1}
.addr-cand{padding:10px 12px;border:1px solid var(--line);border-radius:8px;margin-top:6px;cursor:pointer;font-size:.85em;background:var(--panel-2)}
.addr-cand:hover{border-color:var(--trailer);background:var(--trailer-dim)}
.addr-cand.sel{border-color:var(--route);background:var(--st-full-dim)}
.addr-cand b{display:block;color:var(--ink)}

/* 할증 섹션 */
.sc-section{background:var(--st-full-dim);border:1px solid var(--st-full);padding:14px 16px;border-radius:14px;margin-bottom:16px}
.sc-section .step-label{color:var(--st-full)}
#surcharge-box{display:grid;grid-template-columns:repeat(auto-fill,minmax(215px,1fr));gap:9px;margin-top:4px;align-items:stretch}
#terminal-box{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:6px}
@media(max-width:700px){#surcharge-box{grid-template-columns:1fr 1fr}#terminal-box{grid-template-columns:1fr 1fr}}
@media(max-width:460px){#surcharge-box{grid-template-columns:1fr}}
.sc-item{display:flex;align-items:center;gap:7px;font-size:.83em;font-weight:600;color:var(--ink);background:var(--panel-2);border:1px solid var(--line);border-radius:8px;padding:9px 10px;cursor:pointer;transition:all .15s;word-break:keep-all}
.sc-item:has(input:checked){background:var(--st-full-dim);border-color:var(--st-full);color:var(--ink)}
.sc-item-danger{border-color:var(--st-off);background:var(--st-off-dim)}
.sc-item-danger:has(input:checked){background:var(--st-off-dim);border-color:var(--st-off)}
.sc-item-danger span{color:var(--st-off);font-weight:700}
.sc-item-danger .hint{color:var(--muted);font-weight:500}
.sc-item input[type=checkbox]{width:auto;flex-shrink:0;accent-color:var(--route);cursor:pointer}
.sc-item select,.sc-item input[type=number]{padding:4px 6px;font-size:.82em;border-width:1.5px;flex-shrink:0}
.sc-item .sc-label{flex:1;min-width:0;line-height:1.35}
.sc-item.sc-item-col{flex-direction:column;align-items:stretch;gap:6px}
.sc-item.sc-item-col .sc-label-row{display:flex;align-items:center;gap:7px;font-weight:700}
.sc-item.sc-item-col.sc-item-danger .sc-label-row{color:var(--st-full)}
.sc-item.sc-item-col select{width:100%}
#terminal-box .sc-item{background:var(--panel)}
#terminal-box .sc-item:has(input:checked){background:var(--trailer-dim);border-color:var(--trailer);color:var(--ink)}

.round-toggle{background:var(--panel-2);border:1px solid var(--line);color:var(--muted);font-size:.74em;font-weight:700;padding:6px 10px;border-radius:6px;cursor:pointer}
.round-toggle.active{background:var(--route);border-color:var(--route-hover);color:#fff}

/* 결과: 터미널 배지 색상(경평물류 참고 도구와 동일 계열) */
.t-badge{display:inline-block;padding:4px 11px;border-radius:7px;font-weight:800;font-size:.84em;border:1px solid transparent}
.t-bs{background:#bbf7d0;color:#15803d;border-color:#86efac}
.t-bb{background:#bfdbfe;color:#1d4ed8;border-color:#93c5fd}
.t-icns{background:#fde68a;color:#b45309;border-color:#fbbf24}
.t-icn{background:#fef08a;color:#a16207;border-color:#facc15}
.t-icnt{background:#fed7aa;color:#c2410c;border-color:#fdba74}
.t-gy{background:#e9d5ff;color:#6d28d9;border-color:#ddd6fe}
.t-pt{background:#bae6fd;color:#0369a1;border-color:#7dd3fc}
.t-uw{background:#fbcfe8;color:#be185d;border-color:#f9a8d4}
.t-usn{background:#99f6e4;color:#0f766e;border-color:#5eead4}
.t-usp{background:#a5f3fc;color:#0e7490;border-color:#67e8f9}
.t-ph{background:#fecdd3;color:#be123c;border-color:#fda4af}
.t-gs{background:#d9f99d;color:#4d7c0f;border-color:#bef264}
.t-ds{background:#c7d2fe;color:#4338ca;border-color:#a5b4fc}
.t-ms{background:#a7f3d0;color:#047857;border-color:#6ee7b7}
.t-def{background:#e2e8f0;color:#1e293b;border-color:#cbd5e1}

.addr-header{font-weight:800;font-size:1.05rem;color:var(--ink);margin-bottom:14px;border-bottom:2px solid var(--line);padding-bottom:8px;text-align:center}
.term-block{margin-bottom:16px;padding-bottom:14px;border-bottom:1px dashed var(--line)}
.term-block:last-child{margin-bottom:0;padding-bottom:0;border-bottom:none}
.term-block-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:8px}
.term-dist{font-size:.98em;color:var(--cargo);font-weight:700}

.fare-section{margin-bottom:8px;background:var(--panel-2);padding:10px;border-radius:8px;border:1px solid var(--line)}
.ft-badge{display:inline-block;padding:3px 9px;font-weight:700;font-size:.76em;border-radius:5px;background:var(--panel);color:var(--ink);border:1px solid var(--line)}
.fare-grid{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:6px;margin-top:8px}
@media(max-width:520px){.fare-grid{grid-template-columns:1fr 1fr}}
.fare-box{background:var(--panel);padding:8px 4px;border-radius:6px;text-align:center;border:1px solid var(--line)}
.fare-box.highlight{background:var(--cargo-dim);border-color:var(--cargo)}
.fare-label{font-size:.71em;color:var(--muted);font-weight:600;margin-bottom:3px}
.fare-val{font-size:.85em;font-weight:700;color:var(--ink)}
.fare-box.highlight .fare-val{color:var(--cargo);font-weight:800}
.fare-mini{font-size:.66em;color:var(--cargo);font-weight:700;margin-top:2px}

.quote-row{display:flex;justify-content:space-between;align-items:center;font-weight:700;font-size:.86em;color:var(--cargo)}
.copy-btn{width:100%;margin-top:8px;padding:9px;background:transparent;color:var(--trailer);border:1.5px solid var(--trailer);border-radius:8px;font-weight:700;font-size:.84em;cursor:pointer;transition:background .15s}
.copy-btn:hover{background:var(--trailer-dim)}
.copy-btn:hover{background:var(--bg)}
</style>
</head>
<body>
<header class="top">
  <div class="brand">
    <div class="eyebrow">경평물류(주) 인천사무소</div>
    <h1>📊 안전운임 조회</h1>
  </div>
</header>

<div class="q-wrap">
<div class="q-layout">
<div class="q-left">

<div class="card">
  <div class="step-label">📍 주소로 조회</div>
  <label>작업지·행선지 주소</label>
  <div class="addr-row">
    <input type="text" id="addr-input" placeholder="예: 경기도 안성시 공도읍" onkeydown="if(event.key==='Enter')searchAddr()">
    <button class="btn" onclick="searchAddr()">🔍 검색</button>
  </div>
  <div class="hint">국토부 화물자동차 안전운임 기준(forwarder.kr, 2026.2.1~ 운영지침 2026.4.12판). 주소 입력 후 검색하면 1순위 결과로 바로 조회되며, 다른 지역이면 아래 후보를 클릭해 바꿀 수 있습니다.</div>
  <div id="addr-list"></div>
</div>

<div class="sc-section">
  <div class="step-label">⚡ 할증 옵션 (체크한 항목만 반영)</div>
  <div class="hint" style="margin-bottom:8px">• 다수 할증 시 최고 요율 항목(100%)과 나머지(50%)를 합산하되 상위 3개 항목까지만 적용됩니다.</div>
  <div id="surcharge-box">불러오는 중...</div>
</div>

<div class="card">
  <div class="step-label">📊 화주 제출용 견적 설정</div>
  <div style="display:flex;align-items:center;gap:18px;flex-wrap:wrap">
    <div style="display:flex;align-items:center;gap:8px"><label style="margin:0">쉐어율(마진 양보)</label><input type="number" id="share-input" style="width:66px" value="0" onchange="onShareChange()">%</div>
    <button type="button" class="round-toggle" id="btn-round-fare" onclick="toggleRound('fare')">고시운임 사사오입 OFF</button>
    <button type="button" class="round-toggle" id="btn-round-quote" onclick="toggleRound('quote')">견적가 사사오입 OFF</button>
  </div>
  <div class="hint">쉐어율은 안전운송(청구)-안전위탁(하불) 마진 차액 중 몇 %를 고객에게 양보할지입니다. 0%=청구가 그대로 제시, 100%=하불가까지 전부 양보.</div>
  <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:10px">
    <label class="sc-item" style="max-width:220px">
      <input type="checkbox" id="carrier-as-quote" onchange="onCarrierAsQuoteChange()"> 운수사간 적용 (견적가=운수사간 금액)
    </label>
    <label class="sc-item" style="max-width:220px">
      <input type="checkbox" id="safety-consign-as-quote" onchange="onSafetyConsignAsQuoteChange()"> 안전위탁가 적용 (견적가=안전위탁 금액)
    </label>
  </div>
  <div class="hint">체크하면 쉐어율 계산 대신 운수사간 금액(또는 안전위탁 금액)을 그대로 견적가로 사용합니다. 두 옵션은 동시에 켤 수 없습니다.</div>
</div>

<div class="card">
  <div class="step-label">🎯 터미널 설정 — 필요한 기점만 선택해서 저장하면 이후 조회에서 계속 그 터미널만 표시됩니다</div>
  <div id="terminal-box" class="hint">불러오는 중...</div>
  <div id="terminal-km-box" style="display:none;margin-top:12px;padding:9px 12px;background:var(--cargo-dim);border:1.5px solid var(--cargo-dim);border-radius:8px">
    <label style="font-size:.85em;font-weight:700;color:var(--cargo)">📏 거리(KM)별 운임 조회용 실제 거리</label>
    <div style="display:flex;align-items:center;gap:6px;margin-top:5px">
      <input type="number" id="terminal-km-input" min="1" max="550" placeholder="예: 45" style="width:100px" onchange="onDistanceKmChange()">
      <span style="font-size:.88em;font-weight:600">km</span>
    </div>
    <div class="hint" style="margin-top:4px">거리(KM)별 운임/인천지역/평택지역 조회 시 입력한 km에 해당하는 요율로 조회합니다.</div>
  </div>
  <div style="display:flex;gap:8px;margin-top:12px;flex-wrap:wrap">
    <button class="btn" onclick="saveTerminals()">💾 선택저장</button>
    <button class="btn btn-ghost" onclick="selectAllTerminals()">전체선택</button>
    <button class="btn btn-ghost" onclick="deselectAllTerminals()">전체해제</button>
  </div>
  <div id="terminal-save-st" class="hint"></div>
</div>

</div><!-- /q-left -->
<div class="q-right">
<div id="result-list"><div class="card hint">주소를 검색하면 결과가 여기에 표시됩니다.</div></div>
</div><!-- /q-right -->
</div><!-- /q-layout -->
</div><!-- /q-wrap -->

<script>
const $=id=>document.getElementById(id);
const won=n=>(n==null?'-':Number(n).toLocaleString()+'원');
let _surchargeItems=[], _candidates=[], _lastQueries=[];
let _lastRawResults=[], _shareDiscount=0, _roundFare=false, _roundQuote=false, _flatRows=[], _useCarrierAsQuote=false, _useSafetyConsignAsQuote=false;

const TERM_CLASS = {
  '부산신항기점':'t-bs','부산북항기점':'t-bb','인천신항기점':'t-icns','인천항기점':'t-icn',
  '인천국제여객터미널기점':'t-icnt','광양항기점':'t-gy','평택항기점':'t-pt','의왕ICD기점':'t-uw',
  '울산신항기점':'t-usn','울산항기점':'t-usp','포항항기점':'t-ph','군산항기점':'t-gs',
  '대산항기점':'t-ds','마산항기점':'t-ms',
  '거리(KM)별-인천지역':'t-icn','거리(KM)별-평택지역':'t-pt',
  '부산신항기점(편도, 공컨테이너 장치장 : 의왕ICD)':'t-bs',
  '부산북항기점(편도, 공컨테이너 장치장 : 의왕ICD)':'t-bb',
  '광양항기점(편도, 공컨테이너 장치장 : 의왕ICD)':'t-gy'
};

async function init(){
  try{
    const r = await fetch('/api/quote/surcharge-items');
    const d = await r.json();
    _surchargeItems = d.items||[];
    renderSurchargeUI();
  }catch(e){ $('surcharge-box').innerHTML = '<div class="hint">불러오기 실패</div>'; }
  try{
    const r2 = await fetch('/api/quote/terminal-settings');
    const d2 = await r2.json();
    _allTerminals = d2.all||[];
    _selectedTerminals = new Set(d2.selected||d2.all||[]);
    _terminalLabels = d2.labels||{};
    _distanceWarnSet = new Set(d2.distance_warn||[]);
    _distanceWarnText = d2.distance_warn_text||'';
    renderTerminalBox();
  }catch(e){ $('terminal-box').innerHTML = '<div class="hint">불러오기 실패</div>'; }
}

let _allTerminals=[], _selectedTerminals=new Set(), _terminalLabels={}, _distanceWarnSet=new Set(), _distanceWarnText='';

function renderTerminalBox(){
  $('terminal-box').innerHTML = _allTerminals.map(name=>
    `<label class="sc-item"><input type="checkbox" data-term="${name}" onchange="onTerminalCheck(this)" ${_selectedTerminals.has(name)?'checked':''}>${_terminalLabels[name]||name}</label>`
  ).join('');
  updateDistanceKmVisibility();
}

function onTerminalCheck(el){
  if(el.checked && _distanceWarnSet.has(el.dataset.term) && _distanceWarnText){
    alert('⚠ ' + _distanceWarnText);
  }
  updateDistanceKmVisibility();
}

function updateDistanceKmVisibility(){
  const anyChecked = [..._distanceWarnSet].some(name=>{
    const el = document.querySelector(`#terminal-box input[data-term="${CSS.escape(name)}"]`);
    return el && el.checked;
  });
  $('terminal-km-box').style.display = anyChecked ? 'block' : 'none';
}

function onDistanceKmChange(){
  if(_lastQueries.length) refreshAll();
}

function collectDistanceKm(){
  const v = parseFloat($('terminal-km-input').value);
  return (v && v>0) ? v : null;
}

function selectAllTerminals(){
  document.querySelectorAll('#terminal-box input[type=checkbox]').forEach(el=>el.checked=true);
  updateDistanceKmVisibility();
}
function deselectAllTerminals(){
  document.querySelectorAll('#terminal-box input[type=checkbox]').forEach(el=>el.checked=false);
  updateDistanceKmVisibility();
}

async function saveTerminals(){
  const names = [...document.querySelectorAll('#terminal-box input[type=checkbox]:checked')].map(el=>el.dataset.term);
  const st = $('terminal-save-st');
  if(!names.length){ st.style.color='#dc2626'; st.textContent='⚠ 최소 1개 이상 선택하세요.'; return; }
  st.style.color='#64748b'; st.textContent='⏳ 저장 중...';
  try{
    const r = await fetch('/api/quote/terminal-settings', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({terminals: names})});
    const d = await r.json();
    _selectedTerminals = new Set(d.selected||names);
    st.style.color='#16a34a'; st.textContent=`✓ 저장됨 (${_selectedTerminals.size}개 터미널) — 이후 조회에 계속 반영됩니다.`;
    if(_lastQueries.length) await refreshAll();
  }catch(e){ st.style.color='#dc2626'; st.textContent='저장 오류: '+e; }
}

function renderSurchargeUI(){
  $('surcharge-box').innerHTML = _surchargeItems.map(it=>{
    if(it.key==='overweight'){
      const opts = it.options.map(o=>`<option value="${o.v}">${o.t}</option>`).join('');
      return `<label class="sc-item sc-item-danger sc-item-col" style="grid-column:1/-1">
        <span class="sc-label-row">⚠️ ${it.label} (직접선택)</span>
        <select data-key="overweight" onchange="onSurchargeChange()">${opts}</select>
        <span style="display:flex;align-items:center;gap:6px">또는 실제 무게<input type="number" id="weight-tons-input" step="0.1" style="width:64px" placeholder="0" onchange="onSurchargeChange()">톤</span>
        <span class="hint" style="margin:0">무게 입력 시 20FT(20톤 초과)·40FT(23톤 초과) 기준을 각각 자동 적용합니다(위 선택 무시).</span>
      </label>`;
    }
    if(it.kind==='check'){
      return `<label class="sc-item"><input type="checkbox" data-key="${it.key}" onchange="onSurchargeChange()"><span class="sc-label">${it.label}</span></label>`;
    }
    if(it.kind==='pct'){
      return `<label class="sc-item"><input type="checkbox" data-key="${it.key}" onchange="onSurchargeChange()"><span class="sc-label">${it.label}</span>
        <input type="number" data-pct="${it.key}" value="${it.default_pct}" style="width:56px" onchange="onSurchargeChange()">%</label>`;
    }
    if(it.kind==='select'){
      const opts = it.options.map(o=>`<option value="${o.v}">${o.t}</option>`).join('');
      return `<label class="sc-item sc-item-col">
        <span class="sc-label-row">${it.label}</span>
        <select data-key="${it.key}" onchange="onSurchargeChange()">${opts}</select>
      </label>`;
    }
    return '';
  }).join('');
}

function collectWeightTons(){
  const el = $('weight-tons-input');
  const w = el ? parseFloat(el.value) : 0;
  return (w && w>0) ? w : 0;
}

function collectExtra(){
  const extra = {};
  const weightTons = collectWeightTons();
  _surchargeItems.forEach(it=>{
    if(it.key==='overweight' && weightTons>0) return;  // 무게 입력 시 백엔드가 20FT/40FT 각각 계산
    const el = document.querySelector(`[data-key="${it.key}"]`);
    if(!el) return;
    if(it.kind==='check'){
      if(el.checked) Object.assign(extra, it.params);
    }else if(it.kind==='pct'){
      if(el.checked){
        const pctEl = document.querySelector(`[data-pct="${it.key}"]`);
        const pct = parseFloat(pctEl && pctEl.value)||0;
        extra[it.param] = String(pct/100);
        extra[it.pct_param] = String(pct);
      }
    }else if(it.kind==='select'){
      if(el.value) extra[it.param] = el.value;
    }
  });
  return extra;
}

async function searchAddr(){
  const q = $('addr-input').value.trim();
  if(!q){ alert('주소를 입력하세요.'); return; }
  $('addr-list').innerHTML = '⏳ 검색 중...';
  try{
    const r = await fetch('/api/quote/address-search', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({q})});
    const d = await r.json();
    _candidates = d.candidates||[];
    if(!_candidates.length){ $('addr-list').innerHTML = '<div class="hint">검색 결과가 없습니다. 더 구체적으로 입력해 보세요.</div>'; return; }
    renderCandidates();
    await pickCandidate(0);
  }catch(e){ $('addr-list').innerHTML = '검색 오류: '+e; }
}

function renderCandidates(){
  $('addr-list').innerHTML = _candidates.slice(0,6).map((c,i)=>
    `<div class="addr-cand" onclick="pickCandidate(${i})"><b>${c.roadAddr}</b>${c.jibunAddr}</div>`
  ).join('') + `<div id="addr-reopen" class="hint" style="display:none;cursor:pointer;text-decoration:underline" onclick="showAllCandidates()">🔄 다른 주소 후보 다시 보기</div>`;
  const first = document.querySelector('.addr-cand'); if(first) first.classList.add('sel');
}

function showAllCandidates(){
  document.querySelectorAll('.addr-cand').forEach(el=>el.style.display='');
  const reopen = $('addr-reopen'); if(reopen) reopen.style.display='none';
}

async function pickCandidate(i){
  const c = _candidates[i]; if(!c) return;
  document.querySelectorAll('.addr-cand').forEach((el,idx)=>{
    el.classList.toggle('sel', idx===i);
    el.style.display = idx===i ? '' : 'none';
  });
  const reopen = $('addr-reopen'); if(reopen) reopen.style.display='block';
  const hdong = c.hdongs && c.hdongs[0];
  if(!hdong){ alert('행정동 정보를 가져올 수 없습니다.'); return; }
  try{
    const r = await fetch('/api/quote/resolve', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({si:c.si, sgg:c.sgg, hdong})});
    const d = await r.json();
    if(!d.ok){ alert('해당 주소의 안전운임 구간 정보를 찾지 못했습니다.'); return; }
    _lastQueries = [{...d.region, label: c.roadAddr}];
    await refreshAll();
  }catch(e){ alert('조회 오류: '+e); }
}

function onSurchargeChange(){ if(_lastQueries.length) refreshAll(); }
function onShareChange(){ _shareDiscount = parseFloat($('share-input').value)||0; renderAll(); }
function onCarrierAsQuoteChange(){
  _useCarrierAsQuote = $('carrier-as-quote').checked;
  if(_useCarrierAsQuote){ _useSafetyConsignAsQuote = false; $('safety-consign-as-quote').checked = false; }
  $('share-input').disabled = _useCarrierAsQuote || _useSafetyConsignAsQuote;
  renderAll();
}
function onSafetyConsignAsQuoteChange(){
  _useSafetyConsignAsQuote = $('safety-consign-as-quote').checked;
  if(_useSafetyConsignAsQuote){ _useCarrierAsQuote = false; $('carrier-as-quote').checked = false; }
  $('share-input').disabled = _useCarrierAsQuote || _useSafetyConsignAsQuote;
  renderAll();
}
function toggleRound(kind){
  if(kind==='fare'){
    _roundFare = !_roundFare;
    $('btn-round-fare').classList.toggle('active', _roundFare);
    $('btn-round-fare').textContent = _roundFare ? '고시운임 사사오입 ON' : '고시운임 사사오입 OFF';
  }else{
    _roundQuote = !_roundQuote;
    $('btn-round-quote').classList.toggle('active', _roundQuote);
    $('btn-round-quote').textContent = _roundQuote ? '견적가 사사오입 ON' : '견적가 사사오입 OFF';
  }
  renderAll();
}
function round1000(v){ return Math.round(v/1000)*1000; }
function fmtWon(v){ return v==null ? '-' : Math.round(v).toLocaleString()+'원'; }

function renderAll(){
  if(!_lastRawResults.length){ $('result-list').innerHTML=''; return; }
  _flatRows = [];
  $('result-list').innerHTML = _lastRawResults.map(({label, data})=>renderOneAddress(label, data)).join('');
}

function renderOneAddress(label, data){
  if(data.error){
    return `<div class="card"><div class="addr-header">📍 ${label}</div><div class="hint">오류: ${data.error}</div></div>`;
  }
  const byTerm = {};
  ['안전운송운임','안전위탁운임','운수사업자간운임'].forEach(t=>{
    (data[t]||[]).forEach(row=>{
      if(!byTerm[row.terminal]) byTerm[row.terminal] = {terminal: row.terminal};
      byTerm[row.terminal][t] = row;
    });
  });
  const terms = Object.values(byTerm);
  if(!terms.length) return `<div class="card"><div class="addr-header">📍 ${label}</div><div class="hint">조회된 요율이 없습니다.</div></div>`;
  const startIdx = _flatRows.length;
  const blocks = terms.map(t=>renderTermBlock(label, t)).join('');
  const idxRange = [];
  for(let i=startIdx;i<_flatRows.length;i++){ if(Object.keys(_flatRows[i].sizes).length) idxRange.push(i); }
  const idxJson = JSON.stringify(idxRange);
  const fullCopyHtml = idxRange.length ? `<div class="full-copy-row">
      <button class="btn" onclick='copyFullQuote(${idxJson}, this)'>📋 전체구간 견적서</button>
    </div>` : '';
  return `<div class="card"><div class="addr-header">📍 ${label}</div>${fullCopyHtml}${blocks}</div>`;
}

function copyFullQuote(idxArr, btn){
  const rows = idxArr.map(i=>_flatRows[i]).filter(Boolean);
  if(!rows.length) return;
  const label = rows[0].label;
  let text = `[ 운임 견적 안내 - 전체 터미널 ]\n■ 목적지: ${label}\n`;
  rows.forEach(r=>{
    const order = r.isCombine ? [{key:'combine', label:'COMBINE'}] : [{key:'40FT', label:'40FT'}, {key:'20FT', label:'20FT'}];
    const lines = [];
    order.forEach(o=>{
      const s = r.sizes[o.key]; if(!s) return;
      const pctNote = s.pct!=null ? ` (할증 ${s.pct}%)` : '';
      lines.push(`   - ${o.label}: ${Math.round(s.quote).toLocaleString()}원${pctNote}`);
    });
    if(!lines.length) return;
    text += `\n▶ ${r.terminal} (${r.distance}km)\n` + lines.join('\n') + '\n';
  });
  text += `\n(부가세 별도 / 왕복 기준)`;
  navigator.clipboard.writeText(text).then(()=>{
    const orig = btn.textContent; btn.textContent = '✅ 복사 완료!';
    setTimeout(()=>{ btn.textContent = orig; }, 1500);
  });
}

function renderTermBlock(label, t){
  const s = t['안전운송운임'], tk = t['안전위탁운임'], b = t['운수사업자간운임'];
  const ref = [s, tk, b].find(x=>x);
  const cls = TERM_CLASS[t.terminal] || 't-def';
  if(!ref || !(s&&s.ok) && !(tk&&tk.ok) && !(b&&b.ok)){
    const errMsg = (ref&&ref.error) || '조회 실패';
    return `<div class="term-block"><div class="term-block-head"><span class="t-badge ${cls}">${t.terminal}</span></div><div class="hint">${errMsg}</div></div>`;
  }
  const isCombine = !!((s&&s.combine)||(tk&&tk.combine)||(b&&b.combine));
  const dist = (ref||{}).distance_km || '-';
  const sizes = isCombine ? [{key:'combine', label:'COMBINE'}] : [{key:'40FT', label:'40FT'}, {key:'20FT', label:'20FT'}];

  const disp = p => {
    if(!p || p.final==null) return '-';
    return fmtWon(_roundFare ? round1000(p.final) : p.final);
  };

  const rowIdx = _flatRows.length;
  const rowData = {label, terminal: t.terminal, distance: dist, isCombine, sizes: {}};

  let sectionsHtml = '';
  sizes.forEach(sz=>{
    const sVal = s && s.ok && s[sz.key], tVal = tk && tk.ok && tk[sz.key], bVal = b && b.ok && b[sz.key];
    let pct = null;
    if(sVal && sVal.base!=null && sVal.base>0 && sVal.final!=null){
      pct = Math.round((sVal.final/sVal.base - 1) * 100);
    }
    let shareBox = `<div class="fare-box"><div class="fare-label">견적가</div><div class="fare-val">-</div></div>`;
    if(sVal && tVal && sVal.final!=null && tVal.final!=null){
      let quote;
      if(_useCarrierAsQuote && bVal && bVal.final!=null){
        quote = bVal.final;
      }else if(_useSafetyConsignAsQuote){
        quote = tVal.final;
      }else{
        const marginRaw = sVal.final - tVal.final;
        quote = sVal.final - marginRaw * (_shareDiscount/100);
      }
      quote = _roundQuote ? round1000(quote) : Math.round(quote);
      const profit = quote - tVal.final;
      const marginRate = quote>0 ? (profit/quote*100).toFixed(1) : '0.0';
      rowData.sizes[sz.key] = {quote, profit, marginRate, pct};
      shareBox = `<div class="fare-box highlight"><div class="fare-label">견적가</div><div class="fare-val">${fmtWon(quote)}</div><div class="fare-mini">+${fmtWon(profit)} (${marginRate}%)</div></div>`;
    }
    sectionsHtml += `<div class="fare-section">
      <span class="ft-badge">${sz.label} 고시운임${pct!=null ? ` · 할증 ${pct}%` : ''}</span>
      <div class="fare-grid">
        <div class="fare-box"><div class="fare-label">안전운송(청구)</div><div class="fare-val">${disp(sVal)}</div></div>
        <div class="fare-box"><div class="fare-label">운수사간</div><div class="fare-val">${disp(bVal)}</div></div>
        ${shareBox}
        <div class="fare-box"><div class="fare-label">안전위탁(하불)</div><div class="fare-val">${disp(tVal)}</div></div>
      </div>
    </div>`;
  });
  _flatRows.push(rowData);

  const activeSizes = sizes.filter(sz=>rowData.sizes[sz.key]);
  let pctDisplay = '0%';
  if(isCombine){
    const p = activeSizes.length ? rowData.sizes[activeSizes[0].key].pct : null;
    pctDisplay = `${p!=null ? p : 0}%`;
  }else{
    const p40 = rowData.sizes['40FT'] ? rowData.sizes['40FT'].pct : null;
    const p20 = rowData.sizes['20FT'] ? rowData.sizes['20FT'].pct : null;
    if(p40!=null && p20!=null && p40!==p20) pctDisplay = `40FT ${p40}% · 20FT ${p20}%`;
    else pctDisplay = `${p40!=null ? p40 : (p20!=null ? p20 : 0)}%`;
  }
  const modeText = _useCarrierAsQuote ? '운수사간 적용' : (_useSafetyConsignAsQuote ? '안전위탁가 적용' : `쉐어율 ${_shareDiscount}%`);
  const shareHeaderHtml = activeSizes.length ? `<div class="quote-row" style="margin-bottom:8px"><span>📊 화주 제출용 견적 (${modeText}, 할증률 ${pctDisplay})</span></div>` : '';
  const copyBtnHtml = activeSizes.length ? `<button class="copy-btn" onclick="copyQuote(${rowIdx}, this)">📋 ${t.terminal} 견적서</button>` : '';

  return `<div class="term-block">
    <div class="term-block-head"><span class="t-badge ${cls}">${t.terminal}</span><span class="term-dist">${dist}km</span></div>
    ${shareHeaderHtml}
    ${sectionsHtml}
    ${copyBtnHtml}
  </div>`;
}

function copyQuote(idx, btn){
  const r = _flatRows[idx]; if(!r) return;
  const order = r.isCombine ? [{key:'combine', label:'COMBINE'}] : [{key:'40FT', label:'40FT'}, {key:'20FT', label:'20FT'}];
  let text = `[ 운임 견적 안내 ]\n■ 출발기점: ${r.terminal}\n■ 목적지: ${r.label}\n`;
  order.forEach(o=>{
    const s = r.sizes[o.key]; if(!s) return;
    const pctNote = s.pct!=null ? ` (할증 ${s.pct}%)` : '';
    text += `\n■ ${o.label} 운임: ${Math.round(s.quote).toLocaleString()} 원${pctNote}`;
  });
  text += `\n\n(부가세 별도 / 왕복 기준)`;
  navigator.clipboard.writeText(text).then(()=>{
    const orig = btn.textContent; btn.textContent = '✅ 복사 완료!';
    setTimeout(()=>{ btn.textContent = orig; }, 1500);
  });
}

async function refreshAll(){
  if(!_lastQueries.length) return;
  $('result-list').innerHTML = _lastQueries.map(q=>`<div class="card"><div class="addr-header">📍 ${q.label}</div><div class="hint">⏳ 터미널별 요율 조회 중... (최대 10초)</div></div>`).join('');
  const extra = collectExtra();
  const results = await Promise.all(_lastQueries.map(async q=>{
    try{
      const rr = await fetch('/api/quote/rates', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({r1:q.r1, r2:q.r2, r3:q.r3, extra, weight_tons: collectWeightTons(), distance_km: collectDistanceKm()})});
      const rates = await rr.json();
      return {label: q.label, data: rates};
    }catch(e){ return {label: q.label, data: {error: String(e)}}; }
  }));
  _lastRawResults = results;
  renderAll();
}

init();
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def quote_page():
    return QUOTE_HTML


@app.get("/api/quote/surcharge-items")
async def quote_surcharge_items():
    return JSONResponse({"items": sq.SURCHARGE_ITEMS})


@app.post("/api/quote/address-search")
async def quote_address_search(request: Request):
    body = await request.json()
    q = (body.get("q") or "").strip()
    if not q:
        return JSONResponse({"candidates": []})
    try:
        candidates = sq.search_address(q)
    except Exception as ex:
        return JSONResponse({"error": f"주소 검색 오류: {ex}"}, status_code=500)
    return JSONResponse({"candidates": candidates})


@app.post("/api/quote/resolve")
async def quote_resolve(request: Request):
    body = await request.json()
    si, sgg, hdong = body.get("si", ""), body.get("sgg", ""), body.get("hdong", "")
    if not (si and sgg and hdong):
        return JSONResponse({"ok": False})
    try:
        region = sq.resolve_region(si, sgg, hdong)
    except Exception as ex:
        return JSONResponse({"error": f"지역 조회 오류: {ex}"}, status_code=500)
    if not region:
        return JSONResponse({"ok": False})
    return JSONResponse({"ok": True, "region": region})


@app.post("/api/quote/rates")
async def quote_rates(request: Request):
    body = await request.json()
    r1, r2, r3 = body.get("r1", ""), body.get("r2", ""), body.get("r3", "")
    extra = body.get("extra") or {}
    weight_tons = body.get("weight_tons") or None
    try:
        weight_tons = float(weight_tons) if weight_tons else None
    except (TypeError, ValueError):
        weight_tons = None
    distance_km = body.get("distance_km") or None
    try:
        distance_km = float(distance_km) if distance_km else None
    except (TypeError, ValueError):
        distance_km = None
    if not r1:
        return JSONResponse({"error": "지역 정보가 없습니다."}, status_code=400)
    try:
        terminals = sq.get_selected_terminals()
        rates = await asyncio.get_event_loop().run_in_executor(
            None, lambda: sq.get_rates(sq.TYPES, r1, r2, r3, extra, terminals=terminals,
                                        weight_tons=weight_tons, distance_km=distance_km))
    except Exception as ex:
        return JSONResponse({"error": f"요율 조회 오류: {ex}"}, status_code=500)
    return JSONResponse(rates)


@app.get("/api/quote/terminal-settings")
async def quote_terminal_settings_get():
    return JSONResponse({
        "all": sq.TERMINALS, "selected": sq.get_selected_terminals(),
        "labels": sq.TERMINAL_LABELS,
        "distance_warn": sq.DISTANCE_WARN_TERMINALS, "distance_warn_text": sq.DISTANCE_WARN_TEXT,
    })


@app.post("/api/quote/terminal-settings")
async def quote_terminal_settings_post(request: Request):
    body = await request.json()
    terminals = body.get("terminals") or []
    saved = sq.save_selected_terminals(terminals)
    return JSONResponse({"ok": True, "selected": saved})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8010)))
