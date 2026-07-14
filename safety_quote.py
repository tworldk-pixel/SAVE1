"""forwarder.kr 안전운임 계산기 연동 — 주소 기반 실시간 안전운임 견적 조회.
비회원 상태로도 조회 가능한 공개 페이지라 로그인 없이 바로 요청한다.
"""
import json, math, re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

CONFIG_PATH = Path(__file__).parent / "config.json"
BASE_URL = "https://www.forwarder.kr"
QUARTER = "2026_1"   # 2026.2.1~ 시행, 운영지침 2026.4.12 재수정판

TERMINALS = [
    "부산신항기점", "부산북항기점", "인천신항기점", "인천항기점", "인천국제여객터미널기점",
    "광양항기점", "평택항기점", "울산신항기점", "울산항기점", "포항항기점",
    "군산항기점", "대산항기점", "마산항기점", "의왕ICD기점",
    "거리(KM)별 운임", "거리(KM)별-인천지역", "거리(KM)별-평택지역",
    "부산신항기점(편도, 공컨테이너 장치장 : 의왕ICD)",
    "부산북항기점(편도, 공컨테이너 장치장 : 의왕ICD)",
    "광양항기점(편도, 공컨테이너 장치장 : 의왕ICD)",
]
TYPES = ["안전운송운임", "안전위탁운임", "운수사업자간운임"]

# forwarder.kr stitle 원값은 짧아서 화면엔 forwarder.kr 표시문구(왕복 표기 포함)로 보여준다.
TERMINAL_LABELS = {
    "거리(KM)별 운임": "거리(KM)별 운임(왕복)",
    "거리(KM)별-인천지역": "거리(KM)별-인천지역(왕복)",
    "거리(KM)별-평택지역": "거리(KM)별-평택지역(왕복)",
}
# 이 기점들을 선택하면 화면에서 경고 팝업을 띄운다(부대조항 23조 카,타).
DISTANCE_WARN_TERMINALS = ["거리(KM)별 운임", "거리(KM)별-인천지역", "거리(KM)별-평택지역"]
DISTANCE_WARN_TEXT = ("거리별 인천/평택 기점 운임은 구간별 운임표에 기재되지 않은 구간에 한해 "
                      "참고하시기 바랍니다.(부대조항 23조 카,타)")

# TMS 실적통합관리의 IN_PLC_NM/OUT_PLC_NM(실제 CY·야드 명칭 원문)을 위 14개 표준 기점명 중
# 하나로 추정 매칭할 때 쓰는 키워드 표. 위에서부터 먼저 매칭되는 규칙이 우선(더 구체적인
# 규칙을 위에 둔다). 매칭 실패 시 None — 억지로 끼워맞추지 않는다(과거 실적 예상 쉐어율·
# 할증률 역산용, AI 견적 "과거 실적 이력" 기능).
_TERMINAL_KEYWORDS = [
    (("국제여객", "IFPCC", "여객터미널"), "인천국제여객터미널기점"),
    (("부산신항",), "부산신항기점"),
    (("부산북항",), "부산북항기점"),
    (("광양",), "광양항기점"),
    (("평택",), "평택항기점"),
    (("울산신항",), "울산신항기점"),
    (("울산항",), "울산항기점"),
    (("포항",), "포항항기점"),
    (("군산",), "군산항기점"),
    (("대산",), "대산항기점"),
    (("마산",), "마산항기점"),
    (("의왕",), "의왕ICD기점"),
    (("SNCT", "선광신컨", "선광신항", "HJIT", "한진인천컨테이너"), "인천신항기점"),
    (("인천신항",), "인천신항기점"),
    (("인천항", "인천컨테이너", "ICTPC", "동방인천"), "인천항기점"),
]


def guess_terminal(*names) -> str:
    """CY/야드 명칭 원문(들)에서 표준 기점명을 최선으로 추정. 못 찾으면 None."""
    hay = " ".join((n or "") for n in names).upper()
    for keywords, terminal in _TERMINAL_KEYWORDS:
        if any(kw.upper() in hay for kw in keywords):
            return terminal
    return None

# 프론트엔드 체크박스/셀렉트 항목 정의 — key는 화면용, params는 forwarder.kr 폼 필드명 그대로 통과.
SURCHARGE_ITEMS = [
    {"key": "combine", "label": "COMBINE 운송 (동일화주·동일장소 상하차, 180%)", "kind": "check",
     "params": {"combine": "Y"}},
    {"key": "flexi_liquid", "label": "플렉시백 컨테이너 - 액체 (20%)", "kind": "check",
     "params": {"extra1": "0.2", "flexi_type": "liquid"}},
    {"key": "flexi_powder", "label": "플렉시백 컨테이너 - 분말 (10%)", "kind": "check",
     "params": {"extra1": "0.1", "flexi_type": "powder"}},
    {"key": "tank", "label": "TANK 컨테이너(비위험물) 30%", "kind": "check", "params": {"extra2": "0.3"}},
    {"key": "reefer", "label": "냉동냉장 컨테이너 30% (편도 미적용)", "kind": "check", "params": {"extra3": "0.3"}},
    {"key": "dump", "label": "덤프 컨테이너 25%", "kind": "check", "params": {"extra11": "0.25"}},
    {"key": "restricted", "label": "통행제한지역 30%", "kind": "check", "params": {"extra8": "0.3"}},
    {"key": "xray", "label": "검색대(X-RAY) 통과비용 100,000원", "kind": "check", "params": {"xray": "100000"}},
    {"key": "incheon_return", "label": "인천터미널 공컨 반납비(편도) 40,000원", "kind": "check",
     "params": {"incheon_return": "40000"}},
    {"key": "remote", "label": "험로 및 오지", "kind": "pct", "param": "extra4", "pct_param": "extra4_pct",
     "default_pct": 20},
    {"key": "holiday", "label": "일요일·공휴일", "kind": "pct", "param": "extra6", "pct_param": "extra6_pct",
     "default_pct": 20},
    {"key": "night", "label": "심야 (22:00~06:00)", "kind": "pct", "param": "extra7", "pct_param": "extra7_pct",
     "default_pct": 20},
    {"key": "hazmat", "label": "위험물질", "kind": "select", "param": "extra5", "options": [
        {"v": "", "t": "없음"}, {"v": "0.3", "t": "위험물·유독물·유해화학물질 30%"},
        {"v": "1", "t": "화약류 100%"}, {"v": "2", "t": "방사성물질 200%"}]},
    {"key": "oversize", "label": "활대품 (폭/길이/높이 초과)", "kind": "select", "param": "extra10",
     "options": [{"v": "", "t": "없음"}] + [{"v": f"0.{i}", "t": f"{i*10}cm 초과 {i*10}%"} for i in range(1, 6)]},
    {"key": "overweight", "label": "중량물 초과", "kind": "select", "param": "extra9",
     "options": [{"v": "", "t": "없음"}] + [{"v": f"0.{i}", "t": f"{i}톤 초과 {i*10}%"} for i in range(1, 10)]},
]

_ALLOWED_EXTRA_KEYS = {
    "combine", "extra1", "flexi_type", "extra2", "extra3", "extra11", "extra8",
    "xray", "incheon_return", "extra4", "extra4_pct", "extra6", "extra6_pct",
    "extra7", "extra7_pct", "extra5", "extra10", "extra9",
}

_session = requests.Session()
_session.headers.update({"User-Agent": "Mozilla/5.0"})


def _load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
        except Exception:
            pass
    return {}


def _save_config(data: dict):
    cfg = _load_config()
    cfg.update(data)
    CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def get_selected_terminals() -> list:
    """설정에서 저장한 터미널 목록. 저장된 값이 없거나 비어 있으면 전체 반환(기존 동작 유지)."""
    cfg = _load_config()
    saved = cfg.get("quote_terminals") or []
    selected = [t for t in TERMINALS if t in saved]
    return selected or list(TERMINALS)


def save_selected_terminals(names: list):
    valid = [t for t in (names or []) if t in TERMINALS]
    _save_config({"quote_terminals": valid})
    return valid


def _get(params: dict) -> str:
    r = _session.get(f"{BASE_URL}/tariff/", params=params, timeout=15)
    return r.text


def search_address(query: str) -> list:
    """자유 텍스트 주소 → 후보 목록 [{roadAddr, jibunAddr, si, sgg, hdongs:[...]}]."""
    query = (query or "").strip()
    if not query:
        return []
    r = _session.get(f"{BASE_URL}/tariff/", params={"ajax": "1", "q": query}, timeout=10)
    try:
        data = r.json()
    except Exception:
        return []
    return data.get("rows", []) if data.get("ok") else []


def resolve_region(si: str, sgg: str, hdong: str) -> dict:
    """시도/시군구/행정동 → 요율표상 실제 Send_region1/2/3 값 {r1,r2,r3}."""
    r = _session.get(f"{BASE_URL}/tariff/", params={"match": "1", "si": si, "sgg": sgg, "hdong": hdong}, timeout=10)
    try:
        data = r.json()
    except Exception:
        return {}
    if data.get("ok") and data.get("matched"):
        return data.get("data", {})
    return {}


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
# 거리(KM)별 왕복기점 보조 조회용 기준좌표(각 항구 대표 위치)
INCHEON_COORD = (37.4547888, 126.5976971)
PYEONGTAEK_COORD = (36.9700991, 126.8474051)


def geocode_osm(query: str) -> dict:
    """forwarder.kr 자체 주소검색/행정구역 매칭이 실패했을 때 쓰는 보조 지오코딩(OpenStreetMap
    Nominatim, 가입 불필요·공개 API). si/sgg/hdong 추정치와 좌표(lat/lon)를 반환, 실패 시 {}."""
    query = (query or "").strip()
    if not query:
        return {}
    try:
        r = requests.get(NOMINATIM_URL, params={
            "q": query, "format": "jsonv2", "addressdetails": 1, "countrycodes": "kr", "limit": 1,
        }, headers={"User-Agent": "kp-logis-quote-tool/1.0"}, timeout=10)
        rows = r.json()
    except Exception:
        return {}
    if not rows:
        return {}
    row = rows[0]
    addr = row.get("address", {})
    si = addr.get("province") or addr.get("state") or ""
    sgg = addr.get("city") or addr.get("county") or addr.get("city_district") or ""
    hdong = addr.get("town") or addr.get("suburb") or addr.get("village") or addr.get("quarter") or ""
    try:
        lat, lon = float(row.get("lat")), float(row.get("lon"))
    except (TypeError, ValueError):
        return {}
    return {"lat": lat, "lon": lon, "si": si, "sgg": sgg, "hdong": hdong,
            "display_name": row.get("display_name", query)}


def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return r * 2 * math.atan2(a ** 0.5, (1 - a) ** 0.5)


def distance_terminal_for(lat: float, lon: float, selected_terminals: list) -> dict:
    """선택된 터미널 중 거리(KM)별-인천지역/평택지역이 있으면 기준좌표까지 직선거리(km)를
    계산해 {terminal, distance_km} 반환(둘 다 선택돼 있으면 더 가까운 쪽). 없으면 {}."""
    candidates = []
    if "거리(KM)별-인천지역" in (selected_terminals or []):
        candidates.append(("거리(KM)별-인천지역", _haversine_km(lat, lon, *INCHEON_COORD)))
    if "거리(KM)별-평택지역" in (selected_terminals or []):
        candidates.append(("거리(KM)별-평택지역", _haversine_km(lat, lon, *PYEONGTAEK_COORD)))
    if not candidates:
        return {}
    terminal, km = min(candidates, key=lambda x: x[1])
    return {"terminal": terminal, "distance_km": round(km, 1)}


_PRICE_RE = re.compile(r"[\d,]+")


def _parse_price_cell(text: str) -> dict:
    nums = [int(n.replace(",", "")) for n in _PRICE_RE.findall(text or "") if n.replace(",", "").isdigit()]
    if not nums:
        return {"base": None, "final": None}
    if len(nums) == 1:
        return {"base": nums[0], "final": nums[0]}
    return {"base": nums[0], "final": nums[1]}


def _one_terminal(chg_type: str, terminal: str, r1: str, r2: str, r3: str, extra: dict,
                   distance_km: float = None) -> dict:
    params = {"quarter": QUARTER, "chg_type": chg_type, "stitle": terminal,
              "Send_region1": r1, "Send_region2": r2, "Send_region3": r3}
    params.update(extra or {})
    try:
        html = _get(params)
    except Exception as ex:
        return {"terminal": terminal, "ok": False, "error": str(ex)}
    soup = BeautifulSoup(html, "html.parser")
    table = soup.select_one("table.t_table")
    if not table:
        return {"terminal": terminal, "ok": False}
    trs = table.find_all("tr")
    if len(trs) < 2:
        return {"terminal": terminal, "ok": False}
    header = [th.get_text(strip=True) for th in trs[0].find_all(["th", "td"])]
    row_idx = 1
    if terminal in DISTANCE_WARN_TERMINALS:
        # 이 기점들은 거리 매칭 대신 km=1~550 전체 요율표를 반환하므로,
        # 사용자가 입력한 km에 해당하는 행(row_idx=km, 1-based)을 직접 골라야 한다.
        if not distance_km:
            return {"terminal": terminal, "ok": False, "error": "km 입력이 필요합니다."}
        row_idx = max(1, min(int(round(distance_km)), len(trs) - 1))
    cells = [td.get_text(" ", strip=True) for td in trs[row_idx].find_all(["td", "th"])]
    is_combine = "COMBINE" in header
    if is_combine:
        if len(cells) < 7:
            return {"terminal": terminal, "ok": False}
        distance, combine = cells[-2], cells[-1]
        return {"terminal": terminal, "ok": True, "distance_km": distance,
                "combine": _parse_price_cell(combine)}
    if len(cells) < 8:
        return {"terminal": terminal, "ok": False}
    distance, c20, c40 = cells[-3], cells[-2], cells[-1]
    return {"terminal": terminal, "ok": True, "distance_km": distance,
            "20FT": _parse_price_cell(c20), "40FT": _parse_price_cell(c40)}


def _weight_tier(weight_tons: float, threshold: float) -> int:
    """중량물 할증 등급(1~9, 1톤당 10%). threshold=40FT23톤/20FT20톤 초과분 기준."""
    over = weight_tons - threshold
    if over <= 0:
        return 0
    return min(9, math.ceil(over))


def get_rates(chg_type_list: list, r1: str, r2: str, r3: str, extra: dict = None, terminals: list = None,
              weight_tons: float = None, distance_km: float = None) -> dict:
    """지정한 Type들 x 지정한 왕복기점(미지정 시 전체 TERMINALS)에 대해 병렬 조회.
    weight_tons(실제 무게)가 주어지면 40FT(23톤 초과)/20FT(20톤 초과) 기준을 각각 적용해
    두 번씩 조회 후 사이즈별로 합쳐 반환한다(두 사이즈의 할증률이 다를 수 있어 select 하나로는 정확히 반영 불가)."""
    extra = {k: v for k, v in (extra or {}).items() if k in _ALLOWED_EXTRA_KEYS}
    chg_type_list = [t for t in chg_type_list if t in TYPES] or TYPES
    terminals = [t for t in (terminals or []) if t in TERMINALS] or list(TERMINALS)
    jobs = [(t, term) for t in chg_type_list for term in terminals]
    result = {t: [] for t in chg_type_list}

    tier40 = _weight_tier(weight_tons, 23) if weight_tons else 0
    tier20 = _weight_tier(weight_tons, 20) if weight_tons else 0
    split_by_size = weight_tons and tier40 != tier20

    extra_40 = dict(extra)
    extra_20 = dict(extra)
    if weight_tons:
        for d, tier in ((extra_40, tier40), (extra_20, tier20)):
            if tier > 0:
                d["extra9"] = f"0.{tier}"
            else:
                d.pop("extra9", None)

    if not split_by_size:
        with ThreadPoolExecutor(max_workers=10) as ex:
            futs = {ex.submit(_one_terminal, t, term, r1, r2, r3, extra_40, distance_km): (t, term) for t, term in jobs}
            for fut in as_completed(futs):
                t, term = futs[fut]
                try:
                    row = fut.result()
                except Exception as ex2:
                    row = {"terminal": term, "ok": False, "error": str(ex2)}
                result[t].append(row)
    else:
        rows40, rows20 = {}, {}
        with ThreadPoolExecutor(max_workers=10) as ex:
            futs = {}
            for t, term in jobs:
                futs[ex.submit(_one_terminal, t, term, r1, r2, r3, extra_40, distance_km)] = (t, term, "40")
                futs[ex.submit(_one_terminal, t, term, r1, r2, r3, extra_20, distance_km)] = (t, term, "20")
            for fut in as_completed(futs):
                t, term, which = futs[fut]
                try:
                    row = fut.result()
                except Exception as ex2:
                    row = {"terminal": term, "ok": False, "error": str(ex2)}
                (rows40 if which == "40" else rows20)[(t, term)] = row
        for t, term in jobs:
            r40 = rows40.get((t, term), {"terminal": term, "ok": False})
            r20 = rows20.get((t, term), {"terminal": term, "ok": False})
            if "combine" in r40 or "combine" in r20:
                merged = r40 if r40.get("ok") else r20
            else:
                merged = {
                    "terminal": term,
                    "ok": bool(r40.get("ok")) or bool(r20.get("ok")),
                    "distance_km": r40.get("distance_km") or r20.get("distance_km"),
                    "40FT": r40.get("40FT") if r40.get("ok") else None,
                    "20FT": r20.get("20FT") if r20.get("ok") else None,
                }
            result[t].append(merged)

    order = {name: i for i, name in enumerate(TERMINALS)}
    for t in result:
        result[t].sort(key=lambda row: order.get(row["terminal"], 999))
    return result
