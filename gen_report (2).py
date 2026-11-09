#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""مولّد تقرير الصفقات (HTML عربي RTL) — v3"""
import json, os, datetime as dt, html

RIYADH = dt.timezone(dt.timedelta(hours=3))
BASE = os.path.dirname(os.path.abspath(__file__))
OUT_FILE = os.path.join(BASE, "index.html")

TAG_AR = {
    "swing": "تأرجح", "ema20": "EMA20·4س", "ema50": "EMA50·4س", "ema200": "EMA200·4س",
    "ema20d": "EMA20·يومي", "ema50d": "EMA50·يومي", "H_today": "قمة اليوم", "L_today": "قاع اليوم",
    "H_prev": "قمة الأمس", "L_prev": "قاع الأمس", "fib50": "فيبو 0.5", "fib618": "فيبو 0.618",
    "fib382": "فيبو 0.382",
    "ema9_4h": "EMA9·4س", "ema20_1h": "EMA20·1س", "ema50_1h": "EMA50·1س", "swing_1h": "تأرجح 1س",
    "ifib236": "فيبو موجة 0.236", "ifib382": "فيبو موجة 0.382", "ifib50": "فيبو موجة 0.50",
}

SEARCH_ANALYZER_JS = r"""
var TAG_AR_JS = {
  swing:"تأرجح", ema20:"EMA20·4س", ema50:"EMA50·4س", ema200:"EMA200·4س",
  ema20d:"EMA20·يومي", ema50d:"EMA50·يومي", H_today:"قمة اليوم", L_today:"قاع اليوم",
  H_prev:"قمة الأمس", L_prev:"قاع الأمس", fib50:"فيبو 0.5", fib618:"فيبو 0.618", fib382:"فيبو 0.382",
  ema9_4h:"EMA9·4س", ema20_1h:"EMA20·1س", ema50_1h:"EMA50·1س", swing_1h:"تأرجح 1س",
  ifib236:"فيبو موجة 0.236", ifib382:"فيبو موجة 0.382", ifib50:"فيبو موجة 0.50"
};

function normSymInput(raw) {
  var s = (raw || '').toUpperCase().replace(/\s+/g, '').replace(/^\$/, '');
  s = s.replace(/[-_/]?USDT$/, '').replace(/[-_/]?PERP$/, '');
  return s;
}

function fmtPx(x) {
  if (x === null || x === undefined || isNaN(x)) return '-';
  var ax = Math.abs(x), d = 4;
  if (ax >= 1000) d = 2;
  else if (ax >= 10) d = 2;
  else if (ax >= 1) d = 3;
  else if (ax >= 0.1) d = 4;
  else if (ax >= 0.01) d = 5;
  else if (ax >= 0.001) d = 6;
  else d = 7;
  return Number(x).toLocaleString('en-US', {minimumFractionDigits: d, maximumFractionDigits: d});
}

// ===================== الميزة 1: البحث الفوري داخل التقرير =====================
function onSearchCoin() {
  var raw = document.getElementById('coinSearchInp').value || '';
  var q = normSymInput(raw);
  var clrBtn = document.getElementById('clrSearchBtn');
  var sumBox = document.getElementById('searchSummary');
  clrBtn.style.display = q ? 'inline-flex' : 'none';

  var els = document.querySelectorAll('[data-sym]');
  if (!q) {
    for (var i = 0; i < els.length; i++) els[i].style.display = '';
    sumBox.style.display = 'none';
    sumBox.innerHTML = '';
    return;
  }

  for (var j = 0; j < els.length; j++) {
    var sym = (els[j].getAttribute('data-sym') || '').toUpperCase();
    var match = sym.indexOf(q) !== -1 || ('1000' + q) === sym;
    els[j].style.display = match ? '' : 'none';
  }

  var idx = window.REPORT_INDEX || {trades:[], exp:[], inv:[], bos:[], track:[]};
  var mTrades = idx.trades.filter(function(t){ return t.name.indexOf(q) !== -1 || t.name === '1000'+q; });
  var mExp = idx.exp.filter(function(e){ return e.name.indexOf(q) !== -1 || e.name === '1000'+q; });
  var mInv = (idx.inv || []).filter(function(m){ return m.name.indexOf(q) !== -1 || m.name === '1000'+q; });
  var mBos = (idx.bos || []).filter(function(b){ return b.name.indexOf(q) !== -1 || b.name === '1000'+q; });
  var mTrack = idx.track.filter(function(x){ return x.name.indexOf(q) !== -1 || x.name === '1000'+q; });

  var html = '<div style="font-weight:700;color:#93c5fd;margin-bottom:6px">🔎 نتيجة البحث الفوري في التقرير عن: <span style="color:#fff;direction:ltr;display:inline-block">' + q + '</span></div>';
  if (mTrades.length) {
    html += '<div>📋 <b>الصفقات المؤهلة (' + mTrades.length + '):</b> ' + mTrades.map(function(t){
      var col = t.side === 'LONG' ? '#4ade80' : '#f87171';
      return '<a href="#t-' + t.name + '" style="color:' + col + ';font-weight:700;text-decoration:underline;margin-left:8px">' + t.name + ' ' + t.side + ' (درجة ' + t.grade + ' · ' + t.score.toFixed(1) + ')</a>';
    }).join(' ') + '</div>';
  } else {
    html += '<div style="color:#9db1c8">📋 <b>الصفقات المؤهلة (4س):</b> غير موجودة ضمن صفقات المضاربة في هذا المسح.</div>';
  }

  if (mInv.length) {
    html += '<div>🧲 <b>العملات الاستثمارية (عصر وقاع):</b> ' + mInv.map(function(m){
      return '<a href="#inv-' + m.name + '" style="color:#c4b5fd;font-weight:700;text-decoration:underline;margin-left:8px">💎 ' + m.name + ' (' + m.badge + ')</a>';
    }).join(' ') + '</div>';
  }

  if (mBos.length) {
    html += '<div>🚀 <b>كسر الهيكل اليومي (3 إغلاقات):</b> ' + mBos.map(function(b){
      return '<a href="#bos-' + b.name + '" style="color:#38bdf8;font-weight:700;text-decoration:underline;margin-left:8px">🚀 ' + b.name + ' (سيولة ' + b.vol_x.toFixed(1) + 'x)</a>';
    }).join(' ') + '</div>';
  }

  if (mExp.length) {
    html += '<div>🔥 <b>قائمة الانفجار اليومي:</b> ' + mExp.map(function(e){
      return '<a href="#exp-' + e.name + '" style="color:#fbbf24;font-weight:700;text-decoration:underline;margin-left:8px">🔥 ' + e.name + ' (' + e.score.toFixed(1) + ')</a>';
    }).join(' ') + '</div>';
  }

  if (mTrack.length) {
    html += '<div>🔄 <b>متابعة المسح السابق:</b> ' + mTrack.map(function(x){
      var rtxt = (x.r_now !== null && x.r_now !== undefined) ? (' · ' + (x.r_now >= 0 ? '+' : '') + Number(x.r_now).toFixed(2) + 'R') : '';
      return '<a href="#track" style="color:#cbd5e1;text-decoration:underline;margin-left:8px"><b>' + x.name + '</b> (' + x.side + ' — ' + x.status + rtxt + ')</a>';
    }).join(' ') + '</div>';
  }

  html += '<div style="margin-top:9px"><button class="abtn pri" onclick="analyzeFromSearch(\'' + q.replace(/[^A-Z0-9]/g,'') + '\')">🎯 فحص وتحليل حي الآن لعملة ' + q + ' (مباشر من بايننس)</button></div>';
  sumBox.innerHTML = html;
  sumBox.style.display = 'block';
}

function clearSearchCoin() {
  document.getElementById('coinSearchInp').value = '';
  onSearchCoin();
}

function analyzeFromSearch(sym) {
  document.getElementById('customCoinInp').value = sym;
  analyzeCustomCoin();
}

// ===================== الميزة 2أ: المحلل الحي الفوري لعملة محددة (v3.4) =====================
function calcEMA(vals, n) {
  var out = new Array(vals.length).fill(null);
  if (vals.length < n || n <= 0) return out;
  var k = 2 / (n + 1), sum = 0;
  for (var i = 0; i < n; i++) sum += vals[i];
  var e = sum / n;
  out[n - 1] = e;
  for (var j = n; j < vals.length; j++) {
    e = vals[j] * k + e * (1 - k);
    out[j] = e;
  }
  return out;
}

function calcATR(h, l, c, n) {
  n = n || 14;
  var trs = [], out = [], a = null;
  for (var i = 0; i < c.length; i++) {
    if (i === 0) trs.push(h[i] - l[i]);
    else trs.push(Math.max(h[i] - l[i], Math.abs(h[i] - c[i - 1]), Math.abs(l[i] - c[i - 1])));
  }
  for (var j = 0; j < trs.length; j++) {
    if (j + 1 < n) out.push(null);
    else if (j + 1 === n) {
      var s = 0; for (var m = 0; m < n; m++) s += trs[m];
      a = s / n; out.push(a);
    } else {
      a = (a * (n - 1) + trs[j]) / n;
      out.push(a);
    }
  }
  return out;
}

function calcRSI(c, n) {
  n = n || 14;
  var out = new Array(c.length).fill(null);
  if (c.length <= n) return out;
  var gains = 0, losses = 0;
  for (var i = 1; i <= n; i++) {
    var d = c[i] - c[i - 1];
    if (d > 0) gains += d; else losses += (-d);
  }
  var ag = gains / n, al = losses / n;
  out[n] = 100 - 100 / (1 + (al ? ag / al : 999));
  for (var j = n + 1; j < c.length; j++) {
    var df = c[j] - c[j - 1];
    ag = (ag * (n - 1) + (df > 0 ? df : 0)) / n;
    al = (al * (n - 1) + (df < 0 ? -df : 0)) / n;
    out[j] = 100 - 100 / (1 + (al ? ag / al : 999));
  }
  return out;
}

function calcMACDHist(c) {
  var ef = calcEMA(c, 12), es = calcEMA(c, 26);
  var line = [], base = [];
  for (var i = 0; i < c.length; i++) {
    var v = (ef[i] === null || es[i] === null) ? null : (ef[i] - es[i]);
    line.push(v);
    if (v !== null) base.push(v);
  }
  if (!base.length) return new Array(c.length).fill(null);
  var sm = calcEMA(base, 9);
  var off = line.length - base.length;
  var hist = new Array(c.length).fill(null);
  for (var j = 0; j < sm.length; j++) {
    if (line[off + j] !== null && sm[j] !== null) hist[off + j] = line[off + j] - sm[j];
  }
  return hist;
}

function calcPivots(h, l, k) {
  k = k || 3;
  var highs = [], lows = [], n = h.length;
  for (var i = k; i < n - k; i++) {
    var okH = true, okL = true;
    for (var j = 1; j <= k; j++) {
      if (h[i] < h[i - j] || h[i] < h[i + j]) okH = false;
      if (l[i] > l[i - j] || l[i] > l[i + j]) okL = false;
    }
    if (okH) highs.push([i, h[i]]);
    if (okL) lows.push([i, l[i]]);
  }
  return {ph: highs, pl: lows};
}

function enrichKlines(raw) {
  var t = [], o = [], h = [], l = [], c = [];
  for (var i = 0; i < raw.length; i++) {
    t.push(Number(raw[i][0])); o.push(Number(raw[i][1]));
    h.push(Number(raw[i][2])); l.push(Number(raw[i][3])); c.push(Number(raw[i][4]));
  }
  var pv = calcPivots(h, l, 3);
  return {
    t:t, o:o, h:h, l:l, c:c,
    ema9: calcEMA(c, 9), ema20: calcEMA(c, 20), ema50: calcEMA(c, 50), ema200: calcEMA(c, 200),
    atr: calcATR(h, l, c, 14), rsi: calcRSI(c, 14), macd_hist: calcMACDHist(c),
    ph: pv.ph, pl: pv.pl
  };
}

function isAsiaWickNow() {
  var riyadhMs = Date.now() + 3 * 3600 * 1000;
  var d = new Date(riyadhMs);
  var hr = d.getUTCHours(), mn = d.getUTCMinutes();
  return (hr === 2 && mn >= 30) || hr === 3 || hr === 4;
}

function checkAlignedTrendJS(k4, k1h, price, side, chg) {
  if (!k1h || !k1h.ema20 || !k1h.ema50) return false;
  var e20_4 = k4.ema20[k4.ema20.length - 1], e50_4 = k4.ema50[k4.ema50.length - 1];
  var e20_1h = k1h.ema20[k1h.ema20.length - 1], e50_1h = k1h.ema50[k1h.ema50.length - 1];
  if (!e20_4 || !e50_4 || !e20_1h || !e50_1h) return false;
  if (side === 'LONG') return (chg >= 6.0 && chg <= 22.0) && (price > e20_4 && e20_4 > e50_4) && (e20_1h > e50_1h);
  return (chg >= -22.0 && chg <= -6.0) && (price < e20_4 && e20_4 < e50_4) && (e20_1h < e50_1h);
}

function isAgainstStrongTrendJS(k4, k1h, price, side, chg) {
  if (!k1h || !k1h.ema20 || !k1h.ema50) return false;
  var e20_4 = k4.ema20[k4.ema20.length - 1], e50_4 = k4.ema50[k4.ema50.length - 1];
  var e20_1h = k1h.ema20[k1h.ema20.length - 1], e50_1h = k1h.ema50[k1h.ema50.length - 1];
  if (!e20_4 || !e50_4 || !e20_1h || !e50_1h) return false;
  if (side === 'SHORT' && chg >= 8.0 && price > e20_4 && e20_4 > e50_4 && e20_1h > e50_1h) return true;
  if (side === 'LONG' && chg <= -8.0 && price < e20_4 && e20_4 < e50_4 && e20_1h < e50_1h) return true;
  return false;
}

function clusterLevelsJS(k4, k1, price, side, asiaWick, k1h, chg) {
  var src = [];
  function add(px, tag, w) { if (px && px > 0 && !isNaN(px)) src.push([px, tag, w || 1.0]); }
  k4.pl.slice(-8).forEach(function(p){ add(p[1], 'swing', 1.4); });
  k4.ph.slice(-8).forEach(function(p){ add(p[1], 'swing', 1.4); });
  ['ema20','ema50','ema200'].forEach(function(nm){ add(k4[nm][k4[nm].length - 1], nm, 1.0); });
  ['ema20','ema50'].forEach(function(nm){ add(k1[nm][k1[nm].length - 1], nm + 'd', 0.6); });

  var newborn = asiaWick && k1.t.length > 1 && (Date.now() - k1.t[k1.t.length - 1]) < 3 * 3600 * 1000;
  if (newborn) {
    add(k1.h[k1.h.length - 2], 'H_prev', 1.2); add(k1.l[k1.l.length - 2], 'L_prev', 1.2);
    if (k1.h.length > 2) { add(k1.h[k1.h.length - 3], 'H_prev', 0.7); add(k1.l[k1.l.length - 3], 'L_prev', 0.7); }
  } else {
    add(k1.h[k1.h.length - 1], 'H_today', 1.2); add(k1.l[k1.l.length - 1], 'L_today', 1.2);
    if (k1.h.length > 1) { add(k1.h[k1.h.length - 2], 'H_prev', 0.7); add(k1.l[k1.l.length - 2], 'L_prev', 0.7); }
  }

  var h60 = k4.h.slice(-60), l60 = k4.l.slice(-60);
  var hi = Math.max.apply(null, h60), lo = Math.min.apply(null, l60);
  if (hi > lo) {
    [[0.5,'fib50'],[0.618,'fib618'],[0.382,'fib382']].forEach(function(f){ add(hi - (hi - lo) * f[0], f[1], 0.5); });
  }

  var weak = newborn ? {fib50:1,fib618:1,fib382:1,ema20d:1,ema50d:1} : {fib50:1,fib618:1,fib382:1,H_prev:1,L_prev:1,ema20d:1,ema50d:1};
  var atr4 = k4.atr[k4.atr.length - 1] || (price * 0.02);
  var isTrend = k1h ? checkAlignedTrendJS(k4, k1h, price, side, chg || 0) : false;
  var tol = 0.0035;
  if (isTrend && k1h) {
    tol = Math.max(0.0035, Math.min(0.16 * atr4 / price, 0.011));
    add(k4.ema9[k4.ema9.length - 1], 'ema9_4h', 1.1);
    add(k1h.ema20[k1h.ema20.length - 1], 'ema20_1h', 1.1);
    add(k1h.ema50[k1h.ema50.length - 1], 'ema50_1h', 0.9);
    k1h.pl.slice(-8).forEach(function(p){ add(p[1], 'swing_1h', 1.1); });
    k1h.ph.slice(-8).forEach(function(p){ add(p[1], 'swing_1h', 1.1); });
    var hi12 = Math.max.apply(null, k4.h.slice(-12)), lo12 = Math.min.apply(null, k4.l.slice(-12));
    if (hi12 > lo12) {
      [[0.236,'ifib236'],[0.382,'ifib382'],[0.5,'ifib50']].forEach(function(f){
        var pxf = side === 'LONG' ? (hi12 - (hi12 - lo12) * f[0]) : (lo12 + (hi12 - lo12) * f[0]);
        add(pxf, f[1], 0.6);
      });
    }
    weak.ifib236 = 1; weak.ifib382 = 1; weak.ifib50 = 1; weak.ema50_1h = 1;
  }

  src.sort(function(a,b){ return a[0] - b[0]; });
  var groups = [];
  src.forEach(function(it){
    var px = it[0], tag = it[1], w = it[2], placed = false;
    for (var i = 0; i < groups.length; i++) {
      var g = groups[i];
      if (Math.abs(px - g.px) / g.px <= tol) {
        g.px = (g.px * g.w + px * w) / (g.w + w);
        g.w += w; g.tags.push(tag); placed = true; break;
      }
    }
    if (!placed) groups.push({px: px, w: w, tags: [tag]});
  });

  var out = [];
  groups.forEach(function(g){
    var uniqTags = Array.from(new Set(g.tags)).sort();
    if (uniqTags.length < 2) return;
    var strongCnt = uniqTags.filter(function(t){ return !weak[t]; }).length;
    if (side === 'LONG' && g.px < price) out.push({px:g.px, tags:uniqTags, n:uniqTags.length, strong:strongCnt, w:g.w});
    if (side === 'SHORT' && g.px > price) out.push({px:g.px, tags:uniqTags, n:uniqTags.length, strong:strongCnt, w:g.w});
  });
  out.sort(function(a,b){ return side === 'LONG' ? (b.px - a.px) : (a.px - b.px); });
  return out;
}

function pickClusterJS(clusters, price, atr4, minDistAtr, maxDistAtr) {
  var cands = [];
  clusters.forEach(function(cl){
    if (cl.n < 2 || cl.strong < 1) return;
    var d = Math.abs(price - cl.px) / atr4;
    if (d >= minDistAtr - 1e-9 && d <= maxDistAtr + 1e-9) cands.push([d, cl]);
  });
  if (!cands.length && minDistAtr > 0) {
    clusters.forEach(function(cl){
      if (cl.n < 2 || cl.strong < 1) return;
      var d = Math.abs(price - cl.px) / atr4;
      if (d <= maxDistAtr + 1e-9) cands.push([d, cl]);
    });
  }
  if (!cands.length) return null;
  cands.sort(function(a,b){ return a[0] - b[0]; });
  var nearD = cands[0][0], near = cands[0][1];
  for (var i = 1; i < cands.length; i++) {
    if (cands[i][0] - nearD > 0.25) break;
    if (cands[i][1].w >= near.w * 1.6 && cands[i][1].strong >= 2) return cands[i];
  }
  return [nearD, near];
}

function srLevelsJS(k4, k1, price, atr4) {
  var sup = [], res = [];
  clusterLevelsJS(k4, k1, price, 'LONG', false, null, 0).forEach(function(c){ sup.push([c.px, c.strong*2+c.n]); });
  clusterLevelsJS(k4, k1, price, 'SHORT', false, null, 0).forEach(function(c){ res.push([c.px, c.strong*2+c.n]); });
  k4.pl.slice(-8).forEach(function(p){ if (p[1] < price) sup.push([p[1], 1]); });
  k4.ph.slice(-8).forEach(function(p){ if (p[1] > price) res.push([p[1], 1]); });
  ['ema20','ema50','ema200'].forEach(function(nm){
    var v = k4[nm][k4[nm].length - 1];
    if (v) (v < price ? sup : res).push([v, 1]);
  });
  ['ema20','ema50'].forEach(function(nm){
    var v = k1[nm][k1[nm].length - 1];
    if (v) (v < price ? sup : res).push([v, 0.8]);
  });
  function dedup(arr, desc) {
    arr.sort(function(a,b){ return desc ? (b[0] - a[0]) : (a[0] - b[0]); });
    var out = [];
    for (var i = 0; i < arr.length; i++) {
      var px = arr[i][0];
      if (out.every(function(o){ return Math.abs(px - o) / o > 0.004; })) out.push(px);
      if (out.length === 3) break;
    }
    return out;
  }
  var s = dedup(sup, true), r = dedup(res, false);
  while (s.length < 3) s.push((s.length ? s[s.length - 1] : price) - 1.5 * atr4);
  while (r.length < 3) r.push((r.length ? r[r.length - 1] : price) + 1.5 * atr4);
  return {supports: s, resistances: r};
}

function structureJS(k4, side) {
  var ph = k4.ph.slice(-4), pl = k4.pl.slice(-4);
  var hh = ph.length >= 2 && ph[ph.length-1][1] > ph[ph.length-2][1];
  var hl = pl.length >= 2 && pl[pl.length-1][1] > pl[pl.length-2][1];
  var lh = ph.length >= 2 && ph[ph.length-1][1] < ph[ph.length-2][1];
  var ll = pl.length >= 2 && pl[pl.length-1][1] < pl[pl.length-2][1];
  if (side === 'LONG') {
    if (hh && hl) return ['صاعدة HH/HL', 1.0];
    if (hl) return ['قيعان صاعدة', 0.6];
    if (lh && ll) return ['هابطة LH/LL', -0.6];
    return ['عرضية', 0.0];
  } else {
    if (lh && ll) return ['هابطة LH/LL', 1.0];
    if (lh) return ['قمم هابطة', 0.6];
    if (hh && hl) return ['صاعدة HH/HL', -0.6];
    return ['عرضية', 0.0];
  }
}

function trendDirJS(k4, k1) {
  var c = k4.c[k4.c.length - 1], c1 = k1.c[k1.c.length - 1];
  var e20_4 = k4.ema20[k4.ema20.length - 1], e50_4 = k4.ema50[k4.ema50.length - 1], e200_4 = k4.ema200[k4.ema200.length - 1];
  var e20_1 = k1.ema20[k1.ema20.length - 1], e50_1 = k1.ema50[k1.ema50.length - 1];
  var s = 0, s1 = 0;
  if (e20_4) s += (c > e20_4 ? 1 : -1);
  if (e20_4 && e50_4) s += (e20_4 > e50_4 ? 1 : -1);
  if (e50_4 && e200_4) s += (e50_4 > e200_4 ? 1 : -1);
  else if (e50_4) s += (c > e50_4 ? 1 : -1);
  if (e20_1) s1 += (c1 > e20_1 ? 1 : -1);
  if (e20_1 && e50_1) s1 += (e20_1 > e50_1 ? 1 : -1);
  return [s, s1];
}

function evaluateSideJS(data, side) {
  var k4 = data.k4, k1 = data.k1, k1h = data.k1h;
  var price = data.price, atr4 = k4.atr[k4.atr.length - 1];
  var reasons = [];
  if (!atr4 || atr4 <= 0) return {ok:false, reasons:['بيانات شموع غير كافية لحساب ATR'], plan:null};

  if (data.qv < 8.0) reasons.push('سيولة 24س (' + data.qv.toFixed(1) + 'M$) أقل من الحد الأدنى المعتمد (8M$)');
  if (data.markDiffPct > 0.5) reasons.push('فجوة سعر العلامة Mark/Last (' + data.markDiffPct.toFixed(2) + '%) تتجاوز 0.5%');
  if (isAgainstStrongTrendJS(k4, k1h, price, side, data.chg)) {
    reasons.push('ممنوع الدخول (' + side + ') عكس ترند قوي متوافق على 4س و1س (قاعدة Trend is your friend)');
  }

  var asiaWick = isAsiaWickNow();
  var minDReq = asiaWick ? 0.22 : 0.0;
  var isTrend = checkAlignedTrendJS(k4, k1h, price, side, data.chg);
  var baseClusters = clusterLevelsJS(k4, k1, price, side, asiaWick, null, 0);
  var basePicked = pickClusterJS(baseClusters, price, atr4, minDReq, 1.0);
  var usedFastTrend = false, picked = null, allClusters = baseClusters;
  if (isTrend) {
    allClusters = clusterLevelsJS(k4, k1, price, side, asiaWick, k1h, data.chg);
    picked = pickClusterJS(allClusters, price, atr4, minDReq, 1.0);
    usedFastTrend = (basePicked === null);
  } else {
    picked = basePicked;
  }

  var waitingOnly = false;
  if (!picked) {
    var farPicked = pickClusterJS(allClusters, price, atr4, 0.0, 2.8);
    if (farPicked) {
      waitingOnly = true;
      picked = farPicked;
      reasons.push('أقرب حزمة ارتكاز قوية تقع على بُعد ' + farPicked[0].toFixed(2) + ' ATR (أبعد من سقف منع المطاردة 1.0 ATR — انتظر وصول السعر إليها)');
    } else {
      reasons.push('لا توجد حزمة تلاقي صالحة (مصدران فأكثر أحدهما قوي) قريبة من السعر في اتجاه ' + side);
      return {ok:false, reasons:reasons, plan:null};
    }
  }

  var best = picked[1], lvl = best.px;
  var width = Math.min(0.35 * atr4, 0.006 * price);
  var minGap = asiaWick ? (0.22 * atr4) : 0.0;
  var eLo, eHi, stop, nearEdge;
  if (side === 'LONG') {
    eHi = Math.min(lvl + width * 0.55, price - minGap);
    eLo = eHi - width;
    stop = eLo - 0.45 * atr4;
    var candL = k4.pl.slice(-8).map(function(p){return p[1];}).filter(function(v){ return v < eLo && (eLo - v) <= 1.0 * atr4; });
    if (candL.length) stop = Math.min(stop, Math.min.apply(null, candL) - 0.15 * atr4);
    nearEdge = eHi;
  } else {
    eLo = Math.max(lvl - width * 0.55, price + minGap);
    eHi = eLo + width;
    stop = eHi + 0.45 * atr4;
    var candS = k4.ph.slice(-8).map(function(p){return p[1];}).filter(function(v){ return v > eHi && (v - eHi) <= 1.0 * atr4; });
    if (candS.length) stop = Math.max(stop, Math.max.apply(null, candS) + 0.15 * atr4);
    nearEdge = eLo;
  }

  var avg = (eLo + eHi) / 2.0;
  var r = Math.abs(avg - stop);
  var riskPct = (r / avg) * 100.0;
  var atrPct = (atr4 / price) * 100.0;
  var distAtr = Math.abs(price - nearEdge) / atr4;
  var distPct = (nearEdge / price - 1.0) * 100.0;

  if (!waitingOnly && distAtr > 1.0) reasons.push('بُعد منطقة الدخول (' + distAtr.toFixed(2) + ' ATR) يتجاوز سقف 1.0 ATR');
  if (riskPct > 5.0) reasons.push('اتساع الوقف البنيوي (' + riskPct.toFixed(2) + '%) يتجاوز السقف الآمن (5.0%)');
  if (riskPct < 0.30) reasons.push('الوقف ضيق جداً (' + riskPct.toFixed(2) + '% < 0.30%) وعرضة للضرب بالضجيج');
  if (atrPct < 0.25) reasons.push('تذبذب العملة ميت حالياً (ATR = ' + atrPct.toFixed(2) + '% < 0.25%)');

  var pool = [];
  if (side === 'LONG') {
    clusterLevelsJS(k4, k1, price, 'SHORT', false, null, 0).forEach(function(cl){ pool.push(cl.px); });
    k4.ph.slice(-8).forEach(function(p){ pool.push(p[1]); });
    if (k1h) k1h.ph.slice(-8).forEach(function(p){ pool.push(p[1]); });
    if (data.hi24) pool.push(data.hi24);
    pool = pool.filter(function(x){ return x > avg + 0.55 * r; }).sort(function(a,b){ return a - b; });
  } else {
    clusterLevelsJS(k4, k1, price, 'LONG', false, null, 0).forEach(function(cl){ pool.push(cl.px); });
    k4.pl.slice(-8).forEach(function(p){ pool.push(p[1]); });
    if (k1h) k1h.pl.slice(-8).forEach(function(p){ pool.push(p[1]); });
    if (data.lo24) pool.push(data.lo24);
    pool = pool.filter(function(x){ return x < avg - 0.55 * r; }).sort(function(a,b){ return b - a; });
  }
  var uniq = [];
  pool.forEach(function(x){ if (!uniq.length || Math.abs(x - uniq[uniq.length-1]) / uniq[uniq.length-1] > 0.004) uniq.push(x); });

  var need = [1.8, 2.6, 3.5], maxCap = [4.0, 5.8, 8.5], fbR = [2.1, 3.1, 4.4], mults = [1.0, 2.0, 3.1];
  var tgts = [];
  for (var kk = 0; kk < 3; kk++) {
    var wantPx = side === 'LONG' ? (avg + need[kk] * r) : (avg - need[kk] * r);
    var capPx = side === 'LONG' ? (avg + maxCap[kk] * r) : (avg - maxCap[kk] * r);
    var pick = null;
    for (var u = 0; u < uniq.length; u++) {
      var tp = uniq[u];
      var ok = side === 'LONG' ? (tp >= wantPx && tp <= capPx) : (tp >= capPx && tp <= wantPx);
      if (ok) { pick = tp; break; }
    }
    if (pick === null) {
      var ext = Math.min(fbR[kk] * r, mults[kk] * 2.2 * atr4);
      ext = Math.max(ext, (need[kk] + 0.1) * r);
      pick = side === 'LONG' ? (avg + ext) : (avg - ext);
    }
    if (tgts.length) {
      if (side === 'LONG' && pick <= tgts[tgts.length - 1]) pick = tgts[tgts.length - 1] + 0.75 * r;
      if (side === 'SHORT' && pick >= tgts[tgts.length - 1]) pick = tgts[tgts.length - 1] - 0.75 * r;
    }
    tgts.push(pick);
  }
  var rr = tgts.map(function(t){ return Math.abs(t - avg) / r; });
  if (rr[0] < 1.8) reasons.push('العائد للمخاطرة للهدف الأول (R' + rr[0].toFixed(2) + ') أقل من الحد الأدنى (1.80)');
  if (rr[1] < 2.6) reasons.push('العائد للمخاطرة للهدف الثاني (R' + rr[1].toFixed(2) + ') أقل من الحد الأدنى (2.60)');

  var score = 90.0, notes = [];
  var td = trendDirJS(k4, k1);
  var want = side === 'LONG' ? 1 : -1;
  var al4 = td[0] * want, al1 = td[1] * want;
  if (al4 >= 3) { score += 3; notes.push('اتجاه 4س قوي'); }
  else if (al4 === 2) { score += 1; notes.push('اتجاه 4س'); }
  else if (al4 <= -1) { score -= 3; notes.push('ضد اتجاه 4س'); }
  if (al1 >= 2) score += 2; else if (al1 <= -2) score -= 2;

  var stObj = structureJS(k4, side);
  score += 3 * stObj[1];
  if (best.w >= 3.5 && best.strong >= 2) { score += 4; notes.push('حزمة قوية'); }
  else if (best.w >= 2.2) score += 2;
  else score -= 1;

  if (data.qv >= 500) score += 3;
  else if (data.qv >= 150) score += 2;
  else if (data.qv >= 40) score += 1;
  else score -= 1;

  var mh = k4.macd_hist[k4.macd_hist.length - 1], mhp = k4.macd_hist[k4.macd_hist.length - 2];
  var mom = (mh !== null && mhp !== null && mh > mhp) ? 1 : -1;
  if (mom * want > 0) { score += 2; notes.push('زخم مؤيد'); } else score -= 1;

  var rsi4 = k4.rsi[k4.rsi.length - 1] || 50, rsi1 = k1.rsi[k1.rsi.length - 1] || 50;
  if (side === 'LONG') {
    if (rsi4 > 74 || rsi1 > 76) { score -= 4; notes.push('RSI متطرف'); }
    else if (rsi4 < 62) score += 1;
  } else {
    if (rsi4 < 26 || rsi1 < 24) { score -= 3; notes.push('RSI متطرف'); }
    else if (rsi4 > 38) score += 1;
  }
  if (Math.abs(data.funding) > 0.10) { score -= 2; notes.push('فاندنغ شاذ'); }
  if (isTrend) notes.push('ارتكاز ترند نشط');
  if (asiaWick) notes.push('اصطياد ذيل آسيا');

  if (asiaWick) score += Math.max(0.0, 0.75 - Math.abs(distAtr - 0.38)) * 3.5;
  else score += Math.max(0.0, 0.70 - distAtr) * 4.0;
  score = Math.round(score * 10) / 10;

  if (usedFastTrend && score < 99.0) {
    reasons.push('صفقة ترند سريع بدرجة (' + score.toFixed(1) + ') أقل من شرط الدرجة A/B (99.0)');
  } else if (score < 95.0) {
    reasons.push('الدرجة الفنية الإجمالية (' + score.toFixed(1) + ') أقل من حد القبول الرسمي (95.0)');
  }

  var grade = score >= 103 ? 'A' : (score >= 99 ? 'B' : 'C');
  var reach = distAtr <= 0.35 ? 'A' : (distAtr <= 0.65 ? 'B' : 'C');
  var reachP = distAtr <= 0.35 ? 80 : (distAtr <= 0.65 ? 68 : 54);
  var lev = atrPct > 5.0 ? '2x (تذبذب عالٍ)' : ((['BTC','ETH','SOL','BNB'].indexOf(data.name) !== -1) ? '3x–5x' : '3x');

  return {
    ok: reasons.length === 0,
    reasons: reasons,
    plan: {
      side: side, entryLo: eLo, entryHi: eHi, avg: avg, stop: stop, targets: tgts, rr: rr,
      riskPct: riskPct, atrPct: atrPct, distAtr: distAtr, distPct: distPct,
      score: score, grade: grade, reach: reach, reachP: reachP, lev: lev,
      struct: stObj[0], rsi4: rsi4, rsi1: rsi1, isTrend: isTrend, waitingOnly: waitingOnly,
      tags: best.tags.map(function(t){ return TAG_AR_JS[t] || t; }).join(' + '), nSrc: best.n,
      notes: notes.join(' · ') || '—'
    }
  };
}

function fetchBinanceJson(path) {
  var bases = ['https://www.binance.com/fapi/v1', 'https://fapi.binance.com/fapi/v1'];
  return fetch(bases[0] + path).then(function(r){
    if (r.ok) return r.json();
    if (r.status === 400) throw {badSymbol: true};
    return fetch(bases[1] + path).then(function(r2){
      if (!r2.ok) throw {badSymbol: r2.status === 400};
      return r2.json();
    });
  }).catch(function(err){
    if (err && err.badSymbol) throw err;
    return fetch(bases[1] + path).then(function(r2){
      if (!r2.ok) throw {badSymbol: r2.status === 400};
      return r2.json();
    });
  });
}

function loadSymbolBundle(baseName) {
  var sym = baseName + 'USDT';
  return fetchBinanceJson('/ticker/24hr?symbol=' + sym).catch(function(err){
    if (err && err.badSymbol && baseName.indexOf('1000') !== 0) {
      sym = '1000' + baseName + 'USDT';
      baseName = '1000' + baseName;
      return fetchBinanceJson('/ticker/24hr?symbol=' + sym);
    }
    throw err;
  }).then(function(t24){
    return Promise.all([
      Promise.resolve(t24),
      fetchBinanceJson('/premiumIndex?symbol=' + sym),
      fetchBinanceJson('/klines?symbol=' + sym + '&interval=4h&limit=300'),
      fetchBinanceJson('/klines?symbol=' + sym + '&interval=1d&limit=220'),
      fetchBinanceJson('/klines?symbol=' + sym + '&interval=1h&limit=160'),
      fetchBinanceJson('/klines?symbol=' + sym + '&interval=1w&limit=55').catch(function(){ return []; }),
      fetchBinanceJson('/klines?symbol=' + sym + '&interval=1M&limit=18').catch(function(){ return []; })
    ]).then(function(res){
      var td = res[0], pm = res[1];
      var k4 = enrichKlines(res[2]), k1 = enrichKlines(res[3]), k1h = enrichKlines(res[4]);
      var kw = (res[5] && res[5].length) ? enrichKlines(res[5]) : null;
      var km = (res[6] && res[6].length) ? enrichKlines(res[6]) : null;
      var price = Number(td.lastPrice), mark = Number(pm.markPrice || price);
      return {
        sym: sym, name: baseName, price: price, mark: mark,
        markDiffPct: price > 0 ? Math.abs(mark - price) / price * 100.0 : 0,
        chg: Number(td.priceChangePercent), qv: Number(td.quoteVolume) / 1e6,
        hi24: Number(td.highPrice), lo24: Number(td.lowPrice),
        funding: Number(pm.lastFundingRate || 0) * 100.0,
        k4: k4, k1: k1, k1h: k1h, kw: kw, km: km
      };
    });
  });
}

function analyzeCustomCoin() {
  var inp = document.getElementById('customCoinInp');
  var box = document.getElementById('liveCoinResult');
  var base = normSymInput(inp.value);
  if (!base) {
    box.style.display = 'block';
    box.innerHTML = '<div class="warn">⚠️ اكتب رمز العملة أولاً (مثال: <b>SOL</b> أو <b>DOGE</b> أو <b>PEPE</b>).</div>';
    return;
  }
  box.style.display = 'block';
  box.innerHTML = '<div class="note" style="text-align:center">⏳ جاري جلب الشموع الحية من بايننس وتحليل <b>' + base + '</b> بمعادلات v3.4...</div>';

  loadSymbolBundle(base).then(function(data){
    var atr4 = data.k4.atr[data.k4.atr.length - 1] || (data.price * 0.02);
    var sr = srLevelsJS(data.k4, data.k1, data.price, atr4);
    var evL = evaluateSideJS(data, 'LONG');
    var evS = evaluateSideJS(data, 'SHORT');

    var pos24 = (data.hi24 > data.lo24) ? ((data.price - data.lo24) / (data.hi24 - data.lo24) * 100.0) : 50.0;
    var e20_4 = data.k4.ema20[data.k4.ema20.length - 1] || 0;
    var rsi4 = data.k4.rsi[data.k4.rsi.length - 1] || 50;
    var expCoiling = (pos24 >= 75 && data.chg >= 2 && data.chg <= 18 && data.price > e20_4 && data.funding <= 0.025 && rsi4 < 76);

    var chosen = null, alt = null;
    if (evL.ok && evS.ok) {
      chosen = evL.plan.score >= evS.plan.score ? evL : evS;
      alt = (chosen === evL) ? evS : evL;
    } else if (evL.ok) { chosen = evL; alt = evS; }
    else if (evS.ok) { chosen = evS; alt = evL; }
    else {
      // اختيار الاتجاه الأقرب فنياً لتوضيح أسباب الاستبعاد ومنطقة الانتظار
      var td = trendDirJS(data.k4, data.k1)[0];
      if (evL.plan && evS.plan) chosen = (td >= 0) ? evL : evS;
      else chosen = evL.plan ? evL : evS;
      alt = (chosen === evL) ? evS : evL;
    }

    var supTxt = sr.supports.map(fmtPx).join(' · ');
    var resTxt = sr.resistances.map(fmtPx).join(' · ');
    var chgCls = data.chg >= 0 ? 'pos' : 'neg';
    var fCls = data.funding >= 0 ? 'pos' : 'neg';
    var expNote = expCoiling ? '<span class="g expbadge" style="margin-right:6px">🔥 متماسكة قرب قمة 24س (مرشحة رادار انفجار)</span>' : '';

    var wSummary = '—', mSummary = '—', dSummary = '—';
    var riyadhHr = (new Date().getUTCHours() + 3) % 24;
    var isLateDailyJS = (riyadhHr >= 23 || riyadhHr < 3);
    if (data.k1 && data.k1.c && data.k1.c.length >= 3) {
      var dn = data.k1.c.length;
      var do0 = data.k1.o[dn-1], dc0 = data.k1.c[dn-1], dh0 = data.k1.h[dn-1], dl0 = data.k1.l[dn-1];
      var do1 = data.k1.o[dn-2], dc1 = data.k1.c[dn-2], dh1 = data.k1.h[dn-2], dl1 = data.k1.l[dn-2];
      var dl2 = data.k1.l[dn-3];
      var rng0 = Math.max(1e-9, dh0 - dl0), rng1 = Math.max(1e-9, dh1 - dl1);
      var lw0 = (Math.min(do0, dc0) - dl0) / rng0 * 100, uw0 = (dh0 - Math.max(do0, dc0)) / rng0 * 100;
      var lw1 = (Math.min(do1, dc1) - dl1) / rng1 * 100, uw1 = (dh1 - Math.max(do1, dc1)) / rng1 * 100;
      var bd0 = Math.abs(dc0 - do0) / rng0 * 100;
      var ham0 = (lw0 >= 55 && uw0 <= 20 && ((dh0 - dc0) / rng0) <= 0.35 && dl0 <= dl1);
      var ham1 = (lw1 >= 55 && uw1 <= 20 && ((dh1 - dc1) / rng1) <= 0.35 && dl1 <= dl2);
      var str0 = (dc0 > do0 && bd0 >= 50 && uw0 <= 28 && dc0 > dh1);
      if (!isLateDailyJS) {
        dSummary = '⏸️ قبل 23:05 الرياض (شمعة اليوم مستبعدة لعدم اكتمالها) · شمعة أمس المغلقة: ' +
          (ham1 ? ('🔨 همر يومي مكتمل (ذيل سفلي ' + lw1.toFixed(0) + '%)') : ((dc1 >= do1 ? '🟢 خضراء' : '🔴 حمراء') + ' إغلاق ' + fmtPx(dc1)));
      } else {
        dSummary = '🌙 بعد 23:05 الرياض (>83% مكتملة): ' +
          (ham0 ? ('🔨 همر انعكاسي حي (ذيل سفلي ' + lw0.toFixed(0) + '%)') :
           (str0 ? ('🟢 شمعة خضراء قوية فوق قمة أمس (جسم ' + bd0.toFixed(0) + '%)') :
            ('شمعة اليوم غير حاسمة بعد — القرار على إغلاق أمس ' + (ham1 ? '🔨 همر أمس' : fmtPx(dc1)))));
      }
    }
    if (data.kw && data.kw.c && data.kw.c.length >= 2) {
      var wn = data.kw.c.length;
      var wo = data.kw.o[wn-1], wc = data.kw.c[wn-1], wh = data.kw.h[wn-1], wl = data.kw.l[wn-1];
      var wchg = wo > 0 ? ((wc / wo - 1) * 100) : 0;
      var we20 = data.kw.ema20[wn-1] || data.kw.ema9[wn-1];
      var pwh = data.kw.h[wn-2];
      var wuw = (wh > wl) ? ((wh - Math.max(wo, wc)) / (wh - wl) * 100) : 0;
      wSummary = (wc >= wo ? '🟢 خضراء ' : '🔴 حمراء ') + (wchg>=0?'+':'') + wchg.toFixed(1) + '% · ' +
        (we20 ? (wc >= we20 ? 'فوق EMA20 الأسبوعي' : 'تحت EMA20 الأسبوعي') : '') +
        ' · قمة الأسبوع السابق ' + fmtPx(pwh) + ' (ذيل علوي ' + wuw.toFixed(0) + '%)';
    }
    if (data.km && data.km.c && data.km.c.length >= 2) {
      var mn = data.km.c.length;
      var mo = data.km.o[mn-1], mc = data.km.c[mn-1];
      var mchg = mo > 0 ? ((mc / mo - 1) * 100) : 0;
      var pmh = data.km.h[mn-2], pml = data.km.l[mn-2];
      mSummary = (mc >= mo ? '🟢 خضراء ' : '🔴 حمراء ') + (mchg>=0?'+':'') + mchg.toFixed(1) + '% عن افتتاح الشهر · ' +
        'نطاق الشهر السابق [' + fmtPx(pml) + ' – ' + fmtPx(pmh) + ']';
    }
    var htfRowsHtml = '<div class="sr"><span>☀️ الشمعة اليومية (بوابة 23:05)</span><b style="color:#fde68a">' + dSummary + '</b></div>' +
      '<div class="sr"><span>📅 شمعة الأسبوع (1W)</span><b style="color:#93c5fd">' + wSummary + '</b></div>' +
      '<div class="sr"><span>🗓️ شمعة الشهر (1M)</span><b style="color:#c4b5fd">' + mSummary + '</b></div>';

    var html = '';
    if (chosen && chosen.ok && chosen.plan) {
      var p = chosen.plan;
      var cls = p.side === 'LONG' ? 'long' : 'short';
      var sideAr = p.side === 'LONG' ? 'شراء LONG' : 'بيع SHORT';
      var gcol = p.grade === 'A' ? 'ga' : (p.grade === 'B' ? 'gb' : 'gc');
      var rcol = p.reach === 'A' ? 'ra' : (p.reach === 'B' ? 'rb' : 'rc');
      var tgHtml = [0,1,2].map(function(k){
        var pct = ((p.targets[k] / p.avg - 1) * 100);
        return '<div class="lv t' + (k+1) + '"><span>هدف ' + (k+1) + '</span><b>' + fmtPx(p.targets[k]) + '</b><i>' + (pct>=0?'+':'') + pct.toFixed(2) + '% · R' + p.rr[k].toFixed(2) + '</i></div>';
      }).join('');

      html = '<div class="okbox" style="margin:8px 0"><b>✅ نتيجة الفحص الحي (' + data.name + '/USDT):</b> العملة <b>تستوفي كامل شروط المحرك الرسمي (v3.4)</b> في هذه اللحظة!</div>' +
        '<article class="card ' + cls + '" style="margin-top:8px">' +
        '<div class="chead"><div class="csym">🎯 ' + data.name + '<span>/USDT</span> <small>' + p.score.toFixed(1) + ' نقطة</small> ' +
        '<em class="g ' + gcol + '">درجة ' + p.grade + '</em> <em class="g ' + rcol + '">وصول ' + p.reach + ' · ~' + p.reachP + '%</em>' +
        (p.isTrend ? ' <em class="g trtag">⚡ ترند</em>' : '') + expNote + '</div>' +
        '<div><span class="pill ' + cls + '">' + sideAr + '</span></div></div>' +
        '<div class="cbody"><div class="levels">' +
        '<div class="lv entry"><span>منطقة الدخول (Limit)</span><b>' + fmtPx(p.entryLo) + ' – ' + fmtPx(p.entryHi) + '</b><i>' + (p.distPct>=0?'+':'') + p.distPct.toFixed(2) + '% عن السعر · ' + p.distAtr.toFixed(2) + ' ATR</i></div>' +
        '<div class="lv stop"><span>الوقف البنيوي</span><b>' + fmtPx(p.stop) + '</b><i>مخاطرة ' + p.riskPct.toFixed(2) + '%</i></div>' +
        tgHtml + '</div>' +
        '<div class="meta">' +
        '<div><span>السعر اللحظي الآن</span><b>' + fmtPx(data.price) + '</b></div>' +
        '<div><span>تغيّر 24س</span><b class="' + chgCls + '">' + (data.chg>=0?'+':'') + data.chg.toFixed(2) + '%</b></div>' +
        '<div><span>موقع السعر في 24س</span><b>' + pos24.toFixed(0) + '%</b></div>' +
        '<div><span>سيولة 24س</span><b>' + data.qv.toFixed(1) + 'M$</b></div>' +
        '<div><span>فاندنغ</span><b class="' + fCls + '">' + (data.funding>=0?'+':'') + data.funding.toFixed(4) + '%</b></div>' +
        '<div><span>RSI 4س / يومي</span><b>' + p.rsi4.toFixed(0) + ' / ' + p.rsi1.toFixed(0) + '</b></div>' +
        '<div><span>البنية الفنية</span><b>' + p.struct + '</b></div>' +
        '<div><span>الرافعة المقترحة</span><b>' + p.lev + '</b></div>' +
        '<div class="sr"><span>أقرب 3 دعوم</span><b class="pos">' + supTxt + '</b></div>' +
        '<div class="sr"><span>أقرب 3 مقاومات</span><b class="neg">' + resTxt + '</b></div>' +
        htfRowsHtml +
        '<div class="sr"><span>مصادر منطقة الدخول</span><b>' + p.tags + ' (' + p.nSrc + ') · ' + p.notes + '</b></div>' +
        '</div>' +
        (alt ? ('<div class="plan" style="margin-top:10px"><b>↔️ حالة الاتجاه المعاكس (' + (p.side==='LONG'?'SHORT':'LONG') + '):</b> ' +
          (alt.ok && alt.plan
            ? ('متاح أيضاً كسيناريو مضاد بدرجة <b>' + alt.plan.score.toFixed(1) + ' (' + alt.plan.grade + ')</b> من منطقة <b style="direction:ltr;display:inline-block">' + fmtPx(alt.plan.entryLo) + ' – ' + fmtPx(alt.plan.entryHi) + '</b> (وقف ' + fmtPx(alt.plan.stop) + ').')
            : ('غير مؤهل حالياً — ' + (alt.reasons.join(' · ') || 'لا تتوفر شروطه'))) + '</div>') : '') +
        '</div></article>';
    } else {
      var allRej = [];
      if (chosen && chosen.reasons) allRej = chosen.reasons.slice();
      if (alt && alt.reasons && !chosen.plan) {
        alt.reasons.forEach(function(r){ if (allRej.indexOf(r) === -1) allRej.push(r); });
      }
      var rejHtml = allRej.map(function(r){ return '<li>' + r + '</li>'; }).join('');
      var p2 = chosen ? chosen.plan : null;
      var st4 = structureJS(data.k4, data.chg >= 0 ? 'LONG' : 'SHORT')[0];
      var waitHtml = '';
      if (p2) {
        var sideLbl = p2.side === 'LONG' ? 'الشراء (LONG)' : 'البيع (SHORT)';
        waitHtml = '<div class="plan" style="margin-top:10px;border-color:#785713;background:#171207;color:#fde68a">' +
          '<b>🧭 أقرب منطقة انتظار فنية (' + sideLbl + ' — للمراقبة فقط دون مطاردة):</b> ' +
          '<span style="direction:ltr;display:inline-block;font-weight:700;color:#fff">' + fmtPx(p2.entryLo) + ' – ' + fmtPx(p2.entryHi) + '</span> ' +
          '(على بُعد <b>' + p2.distAtr.toFixed(2) + ' ATR</b> · وقف بنيوي تقديري: <span style="direction:ltr;display:inline-block;color:#f87171">' + fmtPx(p2.stop) + '</span> · هدف أول: <span style="direction:ltr;display:inline-block;color:#4ade80">' + fmtPx(p2.targets[0]) + '</span> R' + p2.rr[0].toFixed(2) + ' · مصادرها: ' + p2.tags + ').' +
          '</div>';
      }
      html = '<div class="warn" style="margin:8px 0"><b>⚠️ نتيجة الفحص الحي (' + data.name + '/USDT): غير مؤهلة للدخول الفوري في التقرير الرسمي حالياً</b>' + expNote +
        '<div style="margin-top:6px;color:#fecaca"><b>أسباب الاستبعاد وفق قواعد v3.4 الصارمة:</b><ul style="margin:5px 0 2px">' + rejHtml + '</ul></div></div>' +
        '<article class="card" style="border-right:4px solid #f59e0b;margin-top:8px">' +
        '<div class="chead"><div class="csym">📊 الخريطة الفنية اللحظية لعملة ' + data.name + '<span>/USDT</span></div>' +
        '<div><em class="g gb">تشخيص فوري حي</em></div></div>' +
        '<div class="cbody"><div class="meta">' +
        '<div><span>السعر اللحظي الآن</span><b>' + fmtPx(data.price) + '</b></div>' +
        '<div><span>تغيّر 24س</span><b class="' + chgCls + '">' + (data.chg>=0?'+':'') + data.chg.toFixed(2) + '%</b></div>' +
        '<div><span>موقع السعر في مدى 24س</span><b>' + pos24.toFixed(0) + '%</b></div>' +
        '<div><span>سيولة 24س</span><b>' + data.qv.toFixed(1) + 'M$</b></div>' +
        '<div><span>فاندنغ</span><b class="' + fCls + '">' + (data.funding>=0?'+':'') + data.funding.toFixed(4) + '%</b></div>' +
        '<div><span>RSI 4س / يومي</span><b>' + rsi4.toFixed(0) + ' / ' + (data.k1.rsi[data.k1.rsi.length-1]||50).toFixed(0) + '</b></div>' +
        '<div><span>ATR(4س)</span><b>' + (atr4/data.price*100).toFixed(2) + '%</b></div>' +
        '<div><span>البنية الفنية (4س)</span><b>' + st4 + '</b></div>' +
        '<div class="sr"><span>أقرب 3 دعوم حقيقية</span><b class="pos">' + supTxt + '</b></div>' +
        '<div class="sr"><span>أقرب 3 مقاومات حقيقية</span><b class="neg">' + resTxt + '</b></div>' +
        htfRowsHtml +
        '</div>' + waitHtml + '</div></article>';
    }
    box.innerHTML = '<div style="text-align:left;margin-bottom:4px"><button class="abtn" style="padding:4px 10px;font-size:11.5px" onclick="document.getElementById(\'liveCoinResult\').style.display=\'none\'">✖ إغلاق نتيجة الفحص</button></div>' + html;
  }).catch(function(err){
    var msg = (err && err.badSymbol)
      ? ('❌ الرمز <b>' + base + '</b> غير موجود في عقود بايننس الآجلة الدائمة (USDT-M Perpetual). تأكد من كتابة الرمز الصحيح بالإنجليزية مثل BTC أو SOL أو PEPE.')
      : ('⚠️ تعذر الاتصال المباشر ببيانات بايننس من المتصفح الآن — تأكد من اتصالك بالإنترنت وأعد المحاولة.');
    box.innerHTML = '<div class="warn">' + msg + '</div>';
  });
}
"""


def fp(x, tick=0.0001):
    if x is None:
        return "-"
    ax = abs(x)
    if ax >= 1000:
        p = 2
    elif ax >= 10:
        p = 2
    elif ax >= 1:
        p = 4
    elif ax >= 0.01:
        p = 5
    elif ax >= 0.0001:
        p = 6
    else:
        p = 8
    if tick and tick > 0:
        d = max(0, min(p, int(round(-1 * __import__("math").log10(tick)))))
    else:
        d = p
    s = f"{x:,.{d}f}"
    return s


def load():
    trades = json.load(open(os.path.join(BASE, "scan_result.json")))
    meta = json.load(open(os.path.join(BASE, "scan_meta.json")))
    try:
        state = json.load(open(os.path.join(BASE, "cycle_state.json")))
    except Exception:
        state = {}
    stats = json.load(open(os.path.join(BASE, "fill_stats.json")))
    try:
        tracked = json.load(open(os.path.join(BASE, "prev_tracked.json")))
    except Exception:
        tracked = []
    # حالة التتبع المحفوظة تخصّ صفقات المسح السابق (held)
    try:
        held = json.load(open(os.path.join(BASE, "held.json")))
    except Exception:
        held = []
    try:
        t24 = {x["symbol"]: x for x in json.load(open(os.path.join(BASE, "cache", "t24.json")))}
        prem = {x["symbol"]: x for x in json.load(open(os.path.join(BASE, "cache", "prem.json")))}
    except Exception:
        t24, prem = {}, {}
    try:
        exp_data = json.load(open(os.path.join(BASE, "explosion_candidates.json")))
    except Exception:
        exp_data = {}
    return trades, meta, state, stats, t24, prem, tracked, held, exp_data


COMMODITY_AND_STABLE_SYMS = {
    "PAXGUSDT", "XAUUSDT", "XAUTUSDT", "XAGUSDT",
    "USDCUSDT", "FDUSDUSDT", "TUSDUSDT", "USDPUSDT", "DAIUSDT", "USDEUSDT", "USD1USDT",
}


def update_lifetime_stats(tracked_list, state, now_riyadh):
    """عداد تراكمي مستقل لحساب إجمالي الصفقات المغلقة على ربح أو خسارة منذ بدء التشغيل دون أي تأثير على المحرك."""
    lt_path = os.path.join(BASE, "lifetime_stats.json")
    if os.path.exists(lt_path):
        try:
            lt = json.load(open(lt_path, encoding="utf-8"))
        except Exception:
            lt = {}
    else:
        lt = {}
    lt.setdefault("started_at", now_riyadh.strftime("%Y-%m-%d %H:%M"))
    lt.setdefault("wins", 0)
    lt.setdefault("losses", 0)
    lt.setdefault("net_r", 0.0)
    lt.setdefault("counted", {})
    counted = lt["counted"]
    fallback_ts = int(state.get("prev_ts") or 0)
    now_ms = int(now_riyadh.timestamp() * 1000)

    for x in (tracked_list or []):
        ots = int(x.get("origin_ts") or fallback_ts or 0)
        tid = f"{x.get('sym','')}|{x.get('side','')}|{ots}"
        st = str(x.get("status") or "")
        if st.startswith("وصل"):
            r_val = float(x.get("r_now") if x.get("r_now") is not None else 1.8)
            if tid not in counted:
                lt["wins"] = int(lt["wins"]) + 1
                lt["net_r"] = round(float(lt["net_r"]) + r_val, 3)
                counted[tid] = {"sym": x.get("sym"), "side": x.get("side"), "res": "W", "r": round(r_val, 3), "ts": now_ms}
            elif counted[tid].get("res") == "W" and r_val > float(counted[tid].get("r", 0)) + 0.01:
                delta = r_val - float(counted[tid]["r"])
                lt["net_r"] = round(float(lt["net_r"]) + delta, 3)
                counted[tid]["r"] = round(r_val, 3)
        elif st == "ضربت الوقف":
            r_val = float(x.get("r_now") if x.get("r_now") is not None else -1.0)
            if tid not in counted:
                lt["losses"] = int(lt["losses"]) + 1
                lt["net_r"] = round(float(lt["net_r"]) + r_val, 3)
                counted[tid] = {"sym": x.get("sym"), "side": x.get("side"), "res": "L", "r": round(r_val, 3), "ts": now_ms}

    if len(counted) > 2000:
        keep_keys = sorted(counted.keys(), key=lambda k: counted[k].get("ts", 0))[-2000:]
        lt["counted"] = {k: counted[k] for k in keep_keys}
    lt["updated_at"] = now_riyadh.strftime("%Y-%m-%d %H:%M")
    try:
        json.dump(lt, open(lt_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    except Exception:
        pass
    return lt


def scan_macro_regimes(t24, prem, now_riyadh, is_confirm_run=False):
    """يمسح الفريم اليومي (1D) لبناء قائمتين متمايزتين بدقة:
    1) 🧲 العملات الاستثمارية (مرحلة القاع والعصر الأفقي + حساب التلاعب السُفلي Spring).
    2) 🚀 عملات كسر الهيكل اليومي النشط (3 إغلاقات يومية متتالية بالجسم الكامل BOS + تدفق سيولة).
    """
    import time as _time, concurrent.futures as _cf
    macro_path = os.path.join(BASE, "macro_investments.json")
    now_ms = int(_time.time() * 1000)

    if is_confirm_run and os.path.exists(macro_path):
        try:
            cached_m = json.load(open(macro_path, encoding="utf-8"))
            if now_ms - int(cached_m.get("ts", 0)) < 5 * 3600 * 1000:
                return cached_m
        except Exception:
            pass

    try:
        from core import klines as _klines, enrich as _enrich, cached_get as _cget
    except Exception:
        if os.path.exists(macro_path):
            return json.load(open(macro_path, encoding="utf-8"))
        return {"ts": now_ms, "squeeze": [], "bos3": []}

    try:
        ei = _cget("/v1/exchangeInfo", "exchangeInfo", ttl=6 * 3600)
        if not t24:
            t24 = {x["symbol"]: x for x in _cget("/v1/ticker/24hr", "t24", ttl=300)}
        if not prem:
            prem = {x["symbol"]: x for x in _cget("/v1/premiumIndex", "prem", ttl=300)}
    except Exception:
        if os.path.exists(macro_path):
            return json.load(open(macro_path, encoding="utf-8"))
        return {"ts": now_ms, "squeeze": [], "bos3": []}

    # قراءة مناخ البيتكوين اليومي (BTC Macro Regime) لتوجيه الحجم الاستثماري علمياً
    btc_regime = {"state": "neutral", "label": "🟡 مناخ محايد", "advice": "التزم بالحجم القياسي (1% مخاطرة لكل صفقة مع وقف صريح في المنصة)."}
    try:
        bk = _enrich(_klines("BTCUSDT", "1d", 120))
        bc = bk["c"][-1]
        be50 = bk["ema50"][-1] or bc
        brsi = bk["rsi"][-1] or 50.0
        if bc >= be50:
            btc_regime = {
                "state": "bull",
                "label": f"🟢 مناخ داعم للتجميع (BTC فوق EMA50 اليومي · RSI {brsi:.0f})",
                "advice": "المناخ الكلي إيجابي — يُسمح بالحجم القياسي (1% مخاطرة للصفقة) مع وقف صريح في المنصة.",
            }
        elif brsi <= 38.0:
            btc_regime = {
                "state": "oversold",
                "label": f"🟡 مناخ ارتداد من تشبع بيعي (BTC RSI اليومي {brsi:.0f} ≤ 38)",
                "advice": "البيتكوين في منطقة تشبع بيعي تاريخية تدعم ارتداد قيعان التلاعب السُفلي (Spring) — التزم بوقف صريح.",
            }
        else:
            btc_regime = {
                "state": "caution",
                "label": f"🟠 مناخ حذر (BTC دون EMA50 اليومي · RSI {brsi:.0f})",
                "advice": "البيتكوين تحت متوسطه اليومي — خفّض حجم المركز الاستثماري للنصف (0.5% مخاطرة فقط) ولا تدخل إلا عملة اكتمل فيها ذيل التلاعب السُفلي.",
            }
    except Exception:
        pass

    pool = []
    for s in ei.get("symbols", []):
        sym = s.get("symbol", "")
        if s.get("contractType") != "PERPETUAL" or s.get("quoteAsset") != "USDT" or s.get("status") != "TRADING":
            continue
        if sym in COMMODITY_AND_STABLE_SYMS or not all(ord(ch) < 128 for ch in sym):
            continue
        td_item = t24.get(sym)
        pm_item = prem.get(sym)
        if not td_item or not pm_item:
            continue
        qv = float(td_item.get("quoteVolume", 0)) / 1e6
        age_d = (now_ms - int(s.get("onboardDate", now_ms))) / 86400000.0
        if qv < 8.0 or age_d < 35:
            continue
        tick = 0.0001
        for flt in s.get("filters", []):
            if flt.get("filterType") == "PRICE_FILTER":
                tick = float(flt.get("tickSize", 0.0001))
        pool.append((sym, s.get("baseAsset", sym[:-4]), qv, age_d, tick, td_item, pm_item))

    pool.sort(key=lambda x: -x[2])
    pool = pool[:110]

    def _eval_one(item):
        sym, name, qv, age_d, tick, td_item, pm_item = item
        try:
            k1 = _enrich(_klines(sym, "1d", 300))
        except Exception:
            return None, None
        c, h, l, o, v = k1["c"], k1["h"], k1["l"], k1["o"], k1["v"]
        atr, rsi, e9, e20, e50 = k1["atr"], k1["rsi"], k1["ema9"], k1["ema20"], k1["ema50"]
        n = len(c)
        if n < 90 or not atr[-1] or atr[-1] <= 0:
            return None, None

        price = float(td_item["lastPrice"])
        chg24 = float(td_item["priceChangePercent"])
        fund = float(pm_item.get("lastFundingRate", 0)) * 100.0
        atr_d = atr[-1]
        rsi_d = rsi[-1] or 50.0

        win180 = min(180, n)
        hi180, lo180 = max(h[-win180:]), min(l[-win180:])
        pos180 = (price - lo180) / (hi180 - lo180) if hi180 > lo180 else 0.5

        # قياس صندوق التجميع الأفقي (آخر 20 يوماً مغلقاً بالأجسام لتجنب تشويه ذيول التلاعب)
        bodies_low = sorted(min(o[i], c[i]) for i in range(-21, -1))
        bodies_high = sorted(max(o[i], c[i]) for i in range(-21, -1))
        core_floor = bodies_low[2]
        core_ceil = bodies_high[-3]
        box_atr_ratio = (core_ceil - core_floor) / atr_d if atr_d > 0 else 99.0
        box_pct = (core_ceil - core_floor) / core_floor * 100.0 if core_floor > 0 else 99.0

        bw_hist = []
        for i in range(max(20, n - 95), n):
            if atr[i]:
                seg = c[i - 20:i]
                m = sum(seg) / 20.0
                sd = (sum((x - m) ** 2 for x in seg) / 20.0) ** 0.5
                bw_hist.append((sd / m) * 0.6 + (atr[i] / c[i]) * 0.4)
        cur_bw = bw_hist[-1] if bw_hist else 1.0
        squeeze_pct = (1.0 - sum(1 for x in bw_hist if x <= cur_bw) / max(1, len(bw_hist))) * 100.0

        inv_item = None
        # -------- 1) فحص العملات الاستثمارية العلمي (قاع 180ي + صندوق أفقي حقيقي بدون ذيول ضخ وتفريغ + دفاع شرائي فعلي + وقف صريح Hard Stop)
        full_rng20 = (max(h[-20:]) - min(l[-20:])) / max(1e-9, min(l[-20:])) * 100.0 if n >= 21 else 99.0
        chg20 = (price / c[-21] - 1.0) * 100.0 if n >= 21 and c[-21] > 0 else 0.0
        chg10 = (price / c[-11] - 1.0) * 100.0 if n >= 11 and c[-11] > 0 else 0.0
        if (age_d >= 60 and pos180 <= 0.25 and box_atr_ratio <= 4.0 and box_pct <= 20.0
            and full_rng20 <= 35.0 and -16.0 <= chg20 <= 16.0 and chg10 >= -12.0
            and squeeze_pct >= 50.0 and fund <= 0.015 and core_floor - 0.50 * atr_d <= price <= core_ceil * 1.01):
            spring_done = any((l[i] < core_floor - 0.08 * atr_d and c[i] >= core_floor) for i in range(-8, 0))
            rsi_min14 = min((rsi[i] or 50.0) for i in range(-15, 0))
            rsi_div = (26.0 <= rsi_d <= 54.0) and (rsi_d >= rsi_min14 + 3.0)
            if spring_done or rsi_div:
                e_hi = min(core_floor + 0.25 * atr_d, price)
                e_lo = max(lo180 * 0.94, min(core_floor - 0.35 * atr_d, e_hi - 0.38 * atr_d))
                avg_e = (e_lo + e_hi) / 2.0
                lowest_wick = min(core_floor, min(l[-21:]))
                stop = lowest_wick - 0.65 * atr_d
                r = abs(avg_e - stop)
                risk_pct = (r / avg_e) * 100.0 if avg_e > 0 else 99.0

                if r > 0 and 1.2 <= risk_pct <= 18.0:
                    t1 = max(core_ceil, e50[-1] or 0, avg_e + 1.9 * r)
                    hi90 = max(h[-min(90, n):-5])
                    t2 = max(hi90 if hi90 > t1 * 1.04 else 0, avg_e + 3.1 * r)
                    mid180 = lo180 + 0.52 * (hi180 - lo180)
                    t3 = max(mid180 if mid180 > t2 * 1.05 else 0, avg_e + 4.6 * r)
                    rr = [(t1 - avg_e) / r, (t2 - avg_e) / r, (t3 - avg_e) / r]

                    sc = 92.0 + (1.0 - pos180 / 0.25) * 4.0 + (squeeze_pct - 50.0) * 0.10
                    tags_ar = [f"قاع 180ي ({pos180*100:.0f}%)", f"نطاق أفقي {box_pct:.1f}%", f"عصر {squeeze_pct:.0f}%"]
                    if spring_done and rsi_div:
                        sc += 7.0
                        badge = "🪤 ذيل تلاعب مكتمل + تعافي RSI (النموذج الأقوى +0.39R)"
                        tags_ar.append("Spring + انحراف RSI")
                    elif spring_done:
                        sc += 5.0
                        badge = "🪤 اكتمل ذيل التلاعب السُفلي (Spring)"
                        tags_ar.append("ذيل تلاعب سُفلي مكتمل")
                    else:
                        sc += 3.0
                        badge = "📈 قاع أفقي معصور + تعافي RSI"
                        tags_ar.append("تعافي RSI من القاع")
                    if qv >= 50:
                        sc += 1.5

                    qty_1r = round(10.0 / r, 6)
                    pos_usd_1r = round(qty_1r * avg_e, 1)

                    inv_item = {
                        "sym": sym, "name": name, "price": price, "tick": tick, "qv": qv, "chg": chg24,
                        "funding": fund, "rsi_d": rsi_d, "pos180": pos180 * 100.0,
                        "squeeze_pct": squeeze_pct, "box_floor": core_floor, "box_ceil": core_ceil, "box_pct": box_pct,
                        "spring_done": spring_done, "badge": badge, "score": round(sc, 1),
                        "entry_lo": e_lo, "entry_hi": e_hi, "avg": avg_e, "stop": stop,
                        "targets": [t1, t2, t3], "rr": rr, "risk_pct": risk_pct,
                        "qty_1r": qty_1r, "pos_usd_1r": pos_usd_1r,
                        "dist_pct": (e_hi / price - 1.0) * 100.0,
                        "reasons": tags_ar,
                    }

        # -------- 2) محرك كسر الهيكل والاتجاه الصاعد والهمر اليومي + القاعدة الزمنية لشمعة اليوم (23:05) + فلتر 1W/1M:
        # • طوال اليوم (03:00 – 22:59 بتوقيت الرياض): شمعة اليوم الجارية (-1) غير ناضجة (<83%) ← لا تُحسب أبداً ضمن الإغلاقات ولا كهمر؛
        #   يُعتمد حصراً على الشموع اليومية المغلقة (-4,-3,-2 أو همر أمس المغلق -2)، ويُفحص السعر اللحظي فقط للتأكد أنه لم يكسر الوقف!
        # • ابتداءً من مسح 23:05 حتى 02:59 فجراً (اكتمل ≥83.5% من الشمعة اليومية):
        #   1) تُقبل شمعة اليوم (-1) كشمعة إغلاق ثالثة/ثانية فقط إذا كانت خضراء قوية وصحية (جسم ≥50%، ذيل علوي ≤28%، فوق قمة أمس)
        #      وليس أمامها مقاومة قريبة تعطّل إغلاقها (ثبات إحصائي 96.6% حتى الإغلاق 03:00).
        #   2) كما تُرصد شمعة الهمر الانعكاسية (🔨 Hammer بذيل رفض سُفلي ≥55% وذيل علوي ≤20% بعد كنس قاع اليوم السابق داخل اتجاه صاعد
        #      فوق EMA20 الأسبوعي وEMA50 اليومي، حتى لو لم يصل جسمها لليوم السابق · 50.0% نجاح و+0.27R EV).
        is_late_daily = (now_riyadh.hour >= 23 or now_riyadh.hour < 3)
        bos_item = None
        if n >= 50 and rsi_d < 78.0:
            cand_modes = []
            e50_now = e50[-1]
            e20_now = k1["ema20"][-1]

            # ====== (1) التقييم على الشموع اليومية المغلقة تماماً (يعمل في جميع الأوقات دون تشويش من شمعة اليوم غير المكتملة) ======
            rlive_chk = max(1e-9, h[-1] - l[-1])
            # في المساء المتأخر فقط نتحقق ألا تكون شمعة اليوم شبه المكتملة قد انقلبت لشمعة تصريف حمراء كبيرة
            late_not_dumping = (not is_late_daily) or (
                (c[-1] >= o[-1] or ((o[-1] - c[-1]) <= 0.32 * atr_d and (h[-1] - max(o[-1], c[-1])) / rlive_chk <= 0.45))
                and chg24 > -5.5
            )

            if late_not_dumping:
                i1, i2, i3 = -4, -3, -2
                lvl3 = max(h[n + i1 - 30 : n + i1])
                r1, r2, r3 = max(1e-9, h[i1] - l[i1]), max(1e-9, h[i2] - l[i2]), max(1e-9, h[i3] - l[i3])
                pre_run3 = (lvl3 - min(l[n + i1 - 10 : n + i1])) / atr_d
                vol3 = (v[i1] + v[i2] + v[i3]) / 3.0
                vol20_3 = sum(v[n + i1 - 20 : n + i1]) / 20.0
                vx3 = vol3 / vol20_3 if vol20_3 > 0 else 1.0

                # (أ-1) 3 إغلاقات يومية مغلقة خضراء بالجسم الكامل فوق قمة 30 يوماً
                if (c[i1 - 1] <= lvl3
                    and c[i1] > o[i1] and c[i3] > o[i3]
                    and (c[i2] >= o[i2] or (o[i2] - c[i2]) <= 0.12 * atr_d)
                    and c[i1] >= lvl3 + 0.05 * atr_d
                    and min(o[i2], c[i2]) > lvl3 and min(o[i3], c[i3]) > lvl3
                    and (c[i1] - o[i1]) / r1 >= 0.45
                    and (h[i1] - c[i1]) / r1 <= 0.35
                    and (h[i2] - max(o[i2], c[i2])) / r2 <= 0.35
                    and (h[i3] - max(o[i3], c[i3])) / r3 <= 0.35
                    and pre_run3 <= 4.2 and vx3 >= 1.15 and price > lvl3 - 0.10 * atr_d
                    and (price - lvl3) / atr_d <= 1.85):
                    e_hi = min(price, lvl3 + 0.35 * atr_d)
                    e_lo = max(lvl3 - 0.05 * atr_d, e_hi - 0.28 * atr_d)
                    if e_hi <= e_lo:
                        e_hi = e_lo + 0.15 * atr_d
                    stop = lvl3 - 0.50 * atr_d
                    if price > stop + 0.15 * atr_d:
                        cand_modes.append((
                            "3closes", "🚀 3 إغلاقات يومية مغلقة بالجسم فوق قمة 30 يوماً",
                            "أعلى قمة هيكلية لـ 30 يوماً", lvl3, lvl3, [c[i1], c[i2], c[i3]], vx3, n + i1, e_lo, e_hi, stop
                        ))

                # (أ-2) إغلاقان يوميان مغلقان أخضران بالجسم فوق قمة 30 يوماً
                if not cand_modes:
                    j1, j2 = -3, -2
                    lvl2 = max(h[n + j1 - 30 : n + j1])
                    rj1, rj2 = max(1e-9, h[j1] - l[j1]), max(1e-9, h[j2] - l[j2])
                    pre_run2 = (lvl2 - min(l[n + j1 - 10 : n + j1])) / atr_d
                    vol2 = (v[j1] + v[j2]) / 2.0
                    vol20_2 = sum(v[n + j1 - 20 : n + j1]) / 20.0
                    vx2 = vol2 / vol20_2 if vol20_2 > 0 else 1.0
                    if (c[j1 - 1] <= lvl2
                        and c[j1] > o[j1] and c[j2] > o[j2]
                        and c[j1] >= lvl2 + 0.05 * atr_d
                        and min(o[j2], c[j2]) > lvl2
                        and (c[j1] - o[j1]) / rj1 >= 0.45 and (c[j2] - o[j2]) / rj2 >= 0.35
                        and (h[j1] - c[j1]) / rj1 <= 0.35 and (h[j2] - c[j2]) / rj2 <= 0.35
                        and pre_run2 <= 4.2 and vx2 >= 1.15 and price > lvl2 - 0.10 * atr_d
                        and (price - lvl2) / atr_d <= 1.85):
                        e_hi = min(price, lvl2 + 0.35 * atr_d)
                        e_lo = max(lvl2 - 0.05 * atr_d, e_hi - 0.28 * atr_d)
                        if e_hi <= e_lo:
                            e_hi = e_lo + 0.15 * atr_d
                        stop = lvl2 - 0.50 * atr_d
                        if price > stop + 0.15 * atr_d:
                            cand_modes.append((
                                "2closes", "⚡ إغلاقان يوميان مغلقان بالجسم فوق قمة 30 يوماً",
                                "أعلى قمة هيكلية لـ 30 يوماً", lvl2, lvl2, [c[j1], c[j2]], vx2, n + j1, e_lo, e_hi, stop
                            ))

                # (ب) 3 إغلاقات يومية مغلقة خضراء في اتجاه صاعد قبل الوصول لقمة 30 يوماً (مساحة ≥ 1.8R)
                if not cand_modes:
                    hl_uptrend = min(l[-9:-1]) > min(l[-27:-9])
                    in_uptrend = bool((e50_now and c[-2] > e50_now) or (e20_now and c[-2] > e20_now and hl_uptrend))
                    three_rising_green = (
                        c[i1] > o[i1] and c[i2] > o[i2] and c[i3] > o[i3]
                        and c[i2] > c[i1] and c[i3] > c[i2]
                        and (c[i1] - o[i1]) / r1 >= 0.40 and (c[i2] - o[i2]) / r2 >= 0.35 and (c[i3] - o[i3]) / r3 >= 0.35
                        and (h[i1] - c[i1]) / r1 <= 0.36 and (h[i2] - c[i2]) / r2 <= 0.36 and (h[i3] - c[i3]) / r3 <= 0.36
                    )
                    if three_rising_green and in_uptrend and c[i3] < lvl3 and vx3 >= 1.05:
                        b10_ceil = max(max(o[k], c[k]) for k in range(n + i1 - 10, n + i1))
                        e_hi = min(price, c[i3] - 0.15 * atr_d)
                        e_lo = max(o[i2], e_hi - 0.30 * atr_d)
                        stop = min(l[i2], l[i3]) - 0.25 * atr_d
                        if e_hi > e_lo and price > stop + 0.15 * atr_d and (price - c[i3]) <= 1.2 * atr_d:
                            avg_sub = (e_lo + e_hi) / 2.0
                            r_sub = avg_sub - stop
                            if r_sub > 0 and (lvl3 - avg_sub) >= 1.8 * r_sub:
                                cand_modes.append((
                                    "uptrend3g", "📈 3 إغلاقات يومية مغلقة خضراء في اتجاه صاعد (قبل قمة 30ي)",
                                    "مرتكز الموجة الصاعدة (قمة 10ي)", b10_ceil, lvl3, [c[i1], c[i2], c[i3]], vx3, n + i1, e_lo, e_hi, stop
                                ))

            # ====== (2) القراءة المتقدمة بعد 23:05 فقط (اكتمل ≥83.5% من الشمعة اليومية الجارية -1) ======
            if not cand_modes and is_late_daily:
                rl1 = max(1e-9, h[-1] - l[-1])
                body1_pct = (c[-1] - o[-1]) / rl1
                upw1_pct = (h[-1] - max(o[-1], c[-1])) / rl1
                lvl_late30 = max(h[n - 3 - 30 : n - 3])
                # شرط عدم وجود مقاومة قريبة تعطّل إغلاق شمعة 23:05 فوق شمعة أمس:
                clear_close_wall = (c[-1] > lvl_late30 + 0.12 * atr_d) or ((lvl_late30 - c[-1]) >= 0.85 * atr_d)
                strong_today = (c[-1] > o[-1] and c[-1] > h[-2] and body1_pct >= 0.50 and upw1_pct <= 0.28 and clear_close_wall)

                if strong_today:
                    rm3, rm2 = max(1e-9, h[-3] - l[-3]), max(1e-9, h[-2] - l[-2])
                    prev2_ok = (
                        c[-3] > o[-3] and c[-2] > o[-2] and c[-2] > c[-3]
                        and (c[-3] - o[-3]) / rm3 >= 0.38 and (c[-2] - o[-2]) / rm2 >= 0.35
                        and (h[-3] - c[-3]) / rm3 <= 0.36 and (h[-2] - c[-2]) / rm2 <= 0.36
                    )
                    vol_l3 = (v[-3] + v[-2] + v[-1]) / 3.0
                    vol20_l = sum(v[n - 23 : n - 3]) / 20.0
                    vx_l = vol_l3 / vol20_l if vol20_l > 0 else 1.0
                    if prev2_ok and vx_l >= 1.05:
                        if c[-4] <= lvl_late30 and min(o[-2], c[-2]) > lvl_late30 and min(o[-1], c[-1]) > lvl_late30 and (price - lvl_late30) / atr_d <= 1.85:
                            e_hi = min(price - 0.05 * atr_d, lvl_late30 + 0.38 * atr_d)
                            e_lo = max(lvl_late30 - 0.05 * atr_d, e_hi - 0.28 * atr_d)
                            stop = lvl_late30 - 0.50 * atr_d
                            if e_hi > e_lo:
                                cand_modes.append((
                                    "3closes", "🌙 كسر قمة 30ي + شمعة اليوم (بعد 23:05 · مكتملة >85% بلا عائق)",
                                    "أعلى قمة هيكلية لـ 30 يوماً", lvl_late30, lvl_late30, [c[-3], c[-2], c[-1]], vx_l, n - 3, e_lo, e_hi, stop
                                ))
                        elif e50_now and price > e50_now and price < lvl_late30:
                            b10_l = max(max(o[k], c[k]) for k in range(n - 13, n - 3))
                            e_hi = c[-1] - 0.18 * atr_d
                            e_lo = max(o[-2], e_hi - 0.30 * atr_d)
                            stop = min(l[-2], l[-1]) - 0.25 * atr_d
                            avg_s = (e_lo + e_hi) / 2.0
                            r_s = avg_s - stop
                            if e_hi > e_lo and r_s > 0 and (lvl_late30 - avg_s) >= 1.8 * r_s:
                                cand_modes.append((
                                    "uptrend3g", "🌙 3 شموع خضراء صاعدة (شمعة 23:05 مكتملة >85% بلا عائق قبل قمة 30ي)",
                                    "مرتكز الموجة الصاعدة (قمة 10ي)", b10_l, lvl_late30, [c[-3], c[-2], c[-1]], vx_l, n - 3, e_lo, e_hi, stop
                                ))

            # ====== (3) رصد شمعة الهمر اليومية الانعكاسية (🔨 Hammer بذيل رفض سُفلي ≥55% داخل اتجاه صاعد · 50% نجاح و+0.27R EV) ======
            # نفحص شمعة -1 فقط إذا كنا بعد 23:05 (>83% مكتملة)، ونفحص شمعة أمس المغلقة (-2) خلال اليوم لالتقاط تراجع الشمعة الجديدة نحو الذيل!
            if not cand_modes:
                hm_indices = [-1, -2] if is_late_daily else [-2]
                for hi_idx in hm_indices:
                    oh, hh, lh, ch = o[hi_idx], h[hi_idx], l[hi_idx], c[hi_idx]
                    rng_h = max(1e-9, hh - lh)
                    lo_wick_h = (min(oh, ch) - lh) / rng_h
                    up_wick_h = (hh - max(oh, ch)) / rng_h
                    prev_low_d = l[hi_idx - 1]
                    hi30_h = max(h[n + hi_idx - 30 : n + hi_idx])
                    # شروط الهمر الانعكاسي الصحيح علمياً: مدى ≥0.65 ATR، كنس قاع اليوم السابق، ذيل سُفلي ≥55%، ذيل علوي ≤20%، إغلاق بأعلى 35% من الشمعة، واتجاه صاعد (>EMA50 اليومي)
                    if (rng_h >= 0.65 * atr_d and lo_wick_h >= 0.55 and up_wick_h <= 0.20
                        and lh < prev_low_d and ch >= lh + 0.65 * rng_h
                        and e50_now and ch >= e50_now * 0.98 and price > lh + 0.20 * rng_h
                        and (price - ch) <= 0.85 * atr_d):
                        body_floor_h = min(oh, ch)
                        e_hi = min(price, ch - 0.10 * atr_d)
                        e_lo = max(lh + 0.35 * (body_floor_h - lh), e_hi - 0.32 * atr_d)
                        if e_hi <= e_lo:
                            e_hi = min(price, body_floor_h + 0.05 * atr_d)
                            e_lo = lh + 0.35 * (body_floor_h - lh)
                        stop = lh - 0.18 * atr_d
                        avg_hm = (e_lo + e_hi) / 2.0
                        r_hm = avg_hm - stop
                        vol20_h = sum(v[n + hi_idx - 20 : n + hi_idx]) / 20.0
                        vx_h = v[hi_idx] / vol20_h if vol20_h > 0 else 1.0
                        if e_hi > e_lo and r_hm > 0 and (ch > hi30_h or (hi30_h - avg_hm) >= 1.8 * r_hm):
                            hm_lbl = (
                                f"🔨 همر يومي انعكاسي (بعد 23:05 · ذيل رفض سُفلي {lo_wick_h*100:.0f}%)"
                                if hi_idx == -1
                                else f"🔨 همر يومي مغلق أمس (ذيل رفض سُفلي {lo_wick_h*100:.0f}% للشمعة الجديدة)"
                            )
                            cand_modes.append((
                                "hammer1d", hm_lbl,
                                "قاع ذيل الرفض اليومي (Hammer)", lh, hi30_h, [ch], vx_h, n + hi_idx, e_lo, e_hi, stop
                            ))
                            break

            # الفحص الإلزامي لشمعة الأسبوع (1W) وشمعة الشهر (1M) لكل مرشح يومي:
            for b_kind, k_badge, lvl_type, struct_lvl, ref_hi30, cls_arr, vol_x, end_idx, e_lo, e_hi, stop in cand_modes:
                avg_e = (e_lo + e_hi) / 2.0
                r = abs(avg_e - stop)
                risk_pct = (r / avg_e) * 100.0 if avg_e > 0 else 99.0
                if r <= 0 or risk_pct > 22.0 or risk_pct < 1.0:
                    continue

                try:
                    kw = _enrich(_klines(sym, "1w", 55))
                    km = _klines(sym, "1M", 18)
                except Exception:
                    kw, km = None, None
                if not kw or not km or len(kw["c"]) < 4 or len(km["c"]) < 2:
                    continue

                w_o, w_h, w_l, w_c = kw["o"][-1], kw["h"][-1], kw["l"][-1], kw["c"][-1]
                w_up_wick = (w_h - max(w_o, w_c)) / max(1e-9, w_h - w_l)
                pw_h, pw_l = kw["h"][-2], kw["l"][-2]
                w_ema20 = kw["ema20"][-1] or kw["ema20"][-2]
                w_ema9 = kw["ema9"][-1] or kw["ema9"][-2]
                if w_ema20 is not None:
                    w_struct_ok = (price >= w_ema20) or (w_ema9 is not None and price >= w_ema9 and price > pw_h)
                else:
                    w_struct_ok = (w_ema9 is not None and price >= w_ema9 and price >= (pw_h + pw_l) / 2.0)
                w_candle_ok = (w_c >= w_o or (w_o - w_c) <= 0.35 * atr_d or b_kind == "hammer1d") and (w_up_wick <= 0.42 or w_c >= w_o)

                m_o, m_h, m_l, m_c = km["o"][-1], km["h"][-1], km["l"][-1], km["c"][-1]
                pm_h, pm_l = km["h"][-2], km["l"][-2]
                m_struct_ok = (price >= pm_l) and ((price > pm_h) or ((pm_h - avg_e) >= 1.5 * r))

                if not (w_struct_ok and w_candle_ok and m_struct_ok):
                    continue

                w_chg = (w_c / w_o - 1.0) * 100.0 if w_o > 0 else 0.0
                m_chg = (m_c / m_o - 1.0) * 100.0 if m_o > 0 else 0.0
                w_ema_txt = "فوق EMA20 الأسبوعي" if (w_ema20 and price >= w_ema20) else "فوق EMA9 الأسبوعي"
                w_pwh_txt = "مخترقة قمة الأسبوع السابق" if price > pw_h else f"قمة الأسبوع السابق {fp(pw_h, tick)}"
                w_summary = f"{'🟢 خضراء' if w_c >= w_o else '🟡 متماسكة'} ({w_chg:+.1f}%) · {w_ema_txt} · {w_pwh_txt}"
                m_pmh_txt = "فوق قمة الشهر السابق (PMH)" if price > pm_h else f"مساحة مفتوحة لقمة الشهر السابق {fp(pm_h, tick)}"
                m_summary = f"{'🟢 خضراء' if m_c >= m_o else '🟡 فوق قاع الشهر السابق'} ({m_chg:+.1f}% من افتتاح الشهر) · {m_pmh_txt}"
                room_30d_pct = ((ref_hi30 / price - 1.0) * 100.0) if b_kind in ("uptrend3g", "hammer1d") and price > 0 and ref_hi30 > price else 0.0

                pre_hi = max(h[max(0, end_idx - 160):end_idx])
                pre_lo = min(l[max(0, end_idx - 160):end_idx])
                pre_pos = (struct_lvl - pre_lo) / (pre_hi - pre_lo) if pre_hi > pre_lo else 0.5
                pre_bodies_lo = sorted(min(o[k], c[k]) for k in range(max(0, end_idx - 20), end_idx))
                pre_bodies_hi = sorted(max(o[k], c[k]) for k in range(max(0, end_idx - 20), end_idx))
                pre_box_atr = (pre_bodies_hi[-2] - pre_bodies_lo[1]) / atr_d if (atr_d > 0 and len(pre_bodies_hi) >= 4) else 9.0
                from_squeeze = (pre_pos <= 0.35 and pre_box_atr <= 4.2)

                hi120 = max(h[-min(120, n):])
                hi220 = max(h[-min(220, n):])
                if b_kind in ("uptrend3g", "hammer1d") and ref_hi30 > avg_e:
                    t1 = min(ref_hi30 * 0.995, max(avg_e + 1.95 * r, avg_e + 2.0 * r))
                    if (t1 - avg_e) < 1.8 * r:
                        t1 = avg_e + 1.9 * r
                else:
                    t1 = max(avg_e + 2.0 * r, min(hi120, avg_e + 3.2 * r) if hi120 > avg_e + 1.95 * r else avg_e + 2.0 * r)
                t2 = max(t1 + 0.9 * r, avg_e + 3.2 * r)
                t3 = max(hi220 if (avg_e + 4.2 * r <= hi220 <= avg_e + 8.0 * r) else 0, avg_e + 4.6 * r)
                if t3 <= t2:
                    t3 = t2 + 1.2 * r
                rr = [(t1 - avg_e) / r, (t2 - avg_e) / r, (t3 - avg_e) / r]

                dist_atr = abs(price - e_hi) / atr_d
                in_retest = dist_atr <= 0.55
                base_sc = 97.5 if b_kind == "3closes" else (96.0 if b_kind == "2closes" else (95.5 if b_kind == "uptrend3g" else 95.0))
                sc = base_sc + min(5.0, (vol_x - 1.0) * 2.2) + (2.5 if in_retest else 0.0) + (3.0 if from_squeeze else 0.0) + (1.5 if m_c >= m_o else 0.0)
                c_str = (f"إغلاق همر انعكاسي {fp(cls_arr[0], tick)} (قاع الذيل {fp(struct_lvl, tick)})"
                         if b_kind == "hammer1d" else " ← ".join(fp(x, tick) for x in cls_arr))
                bos_item = {
                    "sym": sym, "name": name, "price": price, "tick": tick, "qv": qv, "chg": chg24,
                    "funding": fund, "rsi_d": rsi_d, "bos_kind": b_kind,
                    "kind_badge": k_badge,
                    "lvl_type": lvl_type, "struct_lvl": struct_lvl, "hi30_ref": ref_hi30, "room_30d_pct": room_30d_pct,
                    "w_summary": w_summary, "m_summary": m_summary,
                    "closes_3": cls_arr, "close_note": c_str,
                    "vol_x": vol_x, "dist_atr": dist_atr,
                    "from_squeeze": from_squeeze, "in_retest": in_retest,
                    "state_lbl": "🎯 في منطقة التراجع/الذيل الآن" if in_retest else "⏳ علّق Limit عند التراجع للمنطقة",
                    "score": round(sc, 1), "entry_lo": e_lo, "entry_hi": e_hi, "avg": avg_e, "stop": stop,
                    "targets": [t1, t2, t3], "rr": rr, "risk_pct": risk_pct,
                    "dist_pct": (e_hi / price - 1.0) * 100.0,
                }
                break

        return inv_item, bos_item

    squeeze_list, bos_list = [], []
    with _cf.ThreadPoolExecutor(max_workers=10) as ex:
        for inv_it, bos_it in ex.map(_eval_one, pool):
            if inv_it:
                squeeze_list.append(inv_it)
            if bos_it:
                bos_list.append(bos_it)

    # إذا انتقلت عملة فعلياً إلى كسر الهيكل بـ 3 إغلاقات يومية، تُعرض في قسم الكسر النشط مع شارة التاج ولا تُكرر في الانتظار القاعي
    bos_syms = {b["sym"] for b in bos_list}
    squeeze_list = [s for s in squeeze_list if s["sym"] not in bos_syms]

    _kr = {"3closes": 4, "2closes": 3, "uptrend3g": 2, "hammer1d": 1}
    squeeze_list.sort(key=lambda x: (-int(x["spring_done"]), -x["score"], x["pos180"]))
    bos_list.sort(key=lambda x: (-_kr.get(x.get("bos_kind"), 0), -int(x["from_squeeze"]), -int(x["in_retest"]), -x["score"]))

    out = {"ts": now_ms, "btc_regime": btc_regime, "squeeze": squeeze_list[:10], "bos3": bos_list[:10]}
    try:
        json.dump(out, open(macro_path, "w", encoding="utf-8"), ensure_ascii=False, default=str)
    except Exception:
        pass
    return out


def build_html(trades, meta, state, stats, t24, prem, tracked, held, now, exp_data=None, lt_stats=None, macro_data=None):
    if exp_data is None:
        try:
            exp_data = json.load(open(os.path.join(BASE, "explosion_candidates.json")))
        except Exception:
            exp_data = {}
    if lt_stats is None:
        lt_stats = update_lifetime_stats(held or tracked, state, now)
    if macro_data is None:
        is_conf = state.get("confirm_ts", 0) > meta.get("ts", 0)
        macro_data = scan_macro_regimes(t24, prem, now, is_confirm_run=is_conf)
    ts = now.strftime("%Y-%m-%d %H:%M")
    day = now.strftime("%Y-%m-%d")
    longs = [t for t in trades if t["side"] == "LONG"]
    shorts = [t for t in trades if t["side"] == "SHORT"]
    gradeA = [t for t in trades if t["grade"] == "A"]
    now_ok = [t for t in trades if t["reach"] == "A"]
    near = [t for t in trades if t["reach"] == "B"]
    far = [t for t in trades if t["reach"] == "C"]
    med_d = sorted(t["dist_atr"] for t in trades)[len(trades) // 2]

    def ctx(sym):
        t = t24.get(sym)
        p = prem.get(sym)
        if not t:
            return None
        return {
            "chg": float(t["priceChangePercent"]),
            "qv": float(t["quoteVolume"]) / 1e6,
            "fund": float(p["lastFundingRate"]) * 100 if p else 0,
        }

    btc = ctx("BTCUSDT") or {"chg": 0.0}
    eth = ctx("ETHUSDT") or {"chg": 0.0}
    sol = ctx("SOLUSDT") or {"chg": 0.0}
    try:
        _ei = json.load(open(os.path.join(BASE, "cache", "exchangeInfo.json")))
        _now_ms = now.timestamp() * 1000
        _pool = []
        for _s in _ei["symbols"]:
            if _s["contractType"] != "PERPETUAL" or _s["quoteAsset"] != "USDT" or _s["status"] != "TRADING":
                continue
            _t = t24.get(_s["symbol"])
            if not _t:
                continue
            if float(_t["quoteVolume"]) / 1e6 < 8 or (_now_ms - _s["onboardDate"]) / 86400000 < 30:
                continue
            _pool.append(float(_t["priceChangePercent"]))
        n_up = sum(1 for c in _pool if c > 0)
        n_dn = sum(1 for c in _pool if c < 0)
    except Exception:
        n_up = n_dn = 0
    top_longs = " · ".join(t["name"] for t in longs[:4]) if longs else "—"

    try:
        _cur_dt = dt.datetime.fromtimestamp(meta.get("ts", now.timestamp() * 1000) / 1000, RIYADH)
    except Exception:
        _cur_dt = now
    cur_hf_name = f"scan_{_cur_dt.strftime('%Y-%m-%d_%H%M')}.json"
    hist_dir = os.path.join(BASE, "history")
    hist_files = sorted(f for f in os.listdir(hist_dir) if f.startswith("scan_") and f.endswith(".json")) if os.path.isdir(hist_dir) else []
    prev_hist = [f for f in hist_files if f != cur_hf_name]
    prev_scan_syms = set()
    if prev_hist:
        try:
            prev_scan = json.load(open(os.path.join(hist_dir, prev_hist[-1])))
            prev_scan_syms = {(x["sym"], x["side"]) for x in prev_scan}
        except Exception:
            prev_scan_syms = set()
    elif tracked:
        prev_scan_syms = {(x["sym"], x["side"]) for x in tracked}
    prev_syms = prev_scan_syms

    tracked_list = held or tracked
    is_confirm_view = state.get("confirm_ts", 0) > meta.get("ts", 0)
    live_map = {(x["sym"], x["side"]): x for x in tracked_list} if is_confirm_view else {}

    def _live_pill(t):
        lx = live_map.get((t["sym"], t["side"]))
        if not lx:
            return ""
        st = lx.get("status", "")
        rv = lx.get("r_now")
        if st == "مفتوحة":
            ost = lx.get("open_state") or ("رابحة" if (rv or 0) > 0 else ("خاسرة" if (rv or 0) < 0 else "عند الدخول"))
            if ost == "رابحة":
                return f'<em class="g owin">🟢 مفتوحة رابحة {rv:+.2f}R</em>'
            if ost == "خاسرة":
                return f'<em class="g oloss">🔴 مفتوحة خاسرة {rv:+.2f}R</em>'
            return '<em class="g oflat">⚪ مفتوحة عند الدخول</em>'
        if str(st).startswith("وصل"):
            return f'<em class="g tpbadge">🎯 {st} ({rv:+.2f}R)</em>'
        if st == "ضربت الوقف":
            return '<em class="g slbadge">🛑 ضربت الوقف</em>'
        if st == "بانتظار التفعيل":
            d = lx.get("dist_now_atr")
            return f'<em class="g waitbadge">⏳ بانتظار التفعيل ({d:.2f} ATR)</em>' if d is not None else '<em class="g waitbadge">⏳ بانتظار التفعيل</em>'
        if st == "أُلغيت (ابتعدت)":
            d = lx.get("dist_now_atr")
            return f'<em class="g cancelbadge">⛔ أُلغيت · ابتعدت {d:.2f} ATR</em>' if d is not None else '<em class="g cancelbadge">⛔ أُلغيت (ابتعدت)</em>'
        return ""

    def card(t, idx, with_id=True):
        c = ctx(t["sym"]) or {"chg": t["chg"], "qv": t["qv"], "fund": t["funding"]}
        side = t["side"]
        side_ar = "شراء LONG" if side == "LONG" else "بيع SHORT"
        cls = "long" if side == "LONG" else "short"
        gcol = {"A": "ga", "B": "gb", "C": "gc"}[t["grade"]]
        rcol = {"A": "ra", "B": "rb", "C": "rc"}[t["reach"]]
        tags = " · ".join(TAG_AR.get(x, x) for x in t["tags"])
        tg = "".join(
            f'<div class="lv t{k+1}"><span>هدف {k+1}{" (قريب)" if k==0 else ""}</span><b>{fp(t["targets"][k], t["tick"])}</b>'
            f'<i>{((t["targets"][k]/t["avg"]-1)*100):+.2f}% · R{t["rr"][k]:.2f}</i></div>'
            for k in range(3)
        )
        chgcls = "pos" if c["chg"] >= 0 else "neg"
        fcls = "pos" if c["fund"] >= 0 else "neg"
        dist_txt = f'{t["dist_pct"]:+.2f}%'
        notes = " · ".join(t["notes"]) if t["notes"] else "—"
        if prev_syms:
            tag_html = (f'<em class="g {"ntag" if (t["sym"], t["side"]) not in prev_syms else "ktag"}">'
                        f'{"جديد" if (t["sym"], t["side"]) not in prev_syms else "مستمر"}</em>')
        else:
            tag_html = ""
        trend_badge = '<em class="g trtag">⚡ ترند</em>' if t.get("is_trend") else ""
        lpill = _live_pill(t)
        lx = live_map.get((t["sym"], t["side"]))
        disp_price = lx["last"] if (lx and lx.get("last") is not None) else t["price"]
        sup_txt = " · ".join(fp(x, t["tick"]) for x in t["supports"][:3])
        res_txt = " · ".join(fp(x, t["tick"]) for x in t["resistances"][:3])
        plan = ("50% عند هدف 1 ← نقل الوقف للتعادل ← 25% عند هدف 2 ← الباقي لهدف 3"
                if True else "")
        id_attr = f' id="t-{t["name"]}"' if with_id else ""
        return f'''
<article class="card {cls}"{id_attr} data-sym="{t["name"]}">
  <div class="chead">
    <div class="csym">{t["name"]}<span>/USDT</span> <small>{t["score"]:.1f} نقطة</small>
      <em class="g {gcol}">درجة {t["grade"]}</em> <em class="g {rcol}">وصول {t["reach"]} · ~{t["reach_p"]}%</em>
      {trend_badge} {tag_html} {lpill}
    </div>
    <div><span class="pill {cls}">{side_ar}</span></div>
  </div>
  <div class="cbody">
    <div class="levels">
      <div class="lv entry"><span>منطقة الدخول</span><b>{fp(t["entry_lo"], t["tick"])} – {fp(t["entry_hi"], t["tick"])}</b><i>{dist_txt} عن السعر · {t["dist_atr"]:.2f} ATR</i></div>
      <div class="lv stop"><span>الوقف</span><b>{fp(t["stop"], t["tick"])}</b><i>مخاطرة {t["risk_pct"]:.2f}%</i></div>
      {tg}
    </div>
    <div class="meta">
      <div><span>السعر الآن</span><b>{fp(disp_price, t["tick"])}</b></div>
      <div><span>تغيّر 24س</span><b class="{chgcls}">{c["chg"]:+.2f}%</b></div>
      <div><span>R:R للأهداف 1/2/3</span><b>{t["rr"][0]:.2f} · {t["rr"][1]:.2f} · {t["rr"][2]:.2f}</b></div>
      <div><span>مصادر المستوى</span><b>{tags} ({t["n_src"]})</b></div>
      <div class="sr"><span>الدعوم</span><b class="pos">{sup_txt}</b></div>
      <div class="sr"><span>المقاومات</span><b class="neg">{res_txt}</b></div>
      <div><span>البنية</span><b>{t["struct"]}</b></div>
      <div><span>ATR(4س)</span><b>{t["atr_pct"]:.2f}%</b></div>
      <div><span>RSI 4س/يومي</span><b>{t["rsi4"]:.0f}/{t["rsi1"]:.0f}</b></div>
      <div><span>سيولة 24س</span><b>{c["qv"]:,.0f}M$</b></div>
      <div><span>فاندنغ</span><b class="{fcls}">{c["fund"]:+.4f}%</b></div>
      <div><span>Δ OI (4س)</span><b class="{'pos' if t["oi_chg"]>=0 else 'neg'}">{t["oi_chg"]:+.2f}%</b></div>
      <div><span>حجم المركز (1000$ · 1%)</span><b>{t["qty"]:,.4f}</b></div>
      <div><span>ملاحظات</span><b>{notes}</b></div>
    </div>
    <div class="plan"><b>الإدارة:</b> {plan}</div>
  </div>
</article>'''

    def row(t, i):
        c = ctx(t["sym"]) or {"chg": t["chg"], "qv": t["qv"]}
        cls = "long" if t["side"] == "LONG" else "short"
        gcol = {"A": "ga", "B": "gb", "C": "gc"}[t["grade"]]
        rcol = {"A": "ra", "B": "rb", "C": "rc"}[t["reach"]]
        s_txt = " · ".join(fp(x, t["tick"]) for x in t["supports"][:3])
        r_txt = " · ".join(fp(x, t["tick"]) for x in t["resistances"][:3])
        tr_b = ' <em class="g trtag" style="font-size:9.5px;padding:1px 5px">⚡ ترند</em>' if t.get("is_trend") else ""
        lpill = f'<div style="margin-top:2px">{_live_pill(t)}</div>' if is_confirm_view else ""
        return f'''<tr data-sym="{t["name"]}">
<td class="c">{i}</td>
<td class="sym"><a href="#t-{t["name"]}">{t["name"]}</a>{tr_b}{lpill}</td>
<td class="c"><span class="pill {cls}">{t["side"]}</span></td>
<td class="n">{fp(t["entry_lo"], t["tick"])} – {fp(t["entry_hi"], t["tick"])}<span class="sub">{t["dist_pct"]:+.2f}% · {t["dist_atr"]:.2f} ATR</span></td>
<td class="n sl">{fp(t["stop"], t["tick"])}<span class="sub">مخاطرة {t["risk_pct"]:.2f}%</span></td>
<td class="n tp">{fp(t["targets"][0], t["tick"])}<span class="sub">R{t["rr"][0]:.2f}</span></td>
<td class="n tp">{fp(t["targets"][1], t["tick"])}<span class="sub">R{t["rr"][1]:.2f}</span></td>
<td class="c">{t["score"]:.1f}</td>
<td class="c"><em class="g {gcol}">{t["grade"]}</em> / <em class="g {rcol}">{t["reach"]}</em></td>
<td class="n">{t["qv"]:,.0f}M</td>
<td class="n" style="font-size:10.5px"><span class="pos">د: {s_txt}</span><span class="sub neg">م: {r_txt}</span></td>
<td class="c" style="font-size:11px">{t["struct"]}</td>
</tr>'''

    try:
        prev_label = dt.datetime.fromtimestamp(state.get("prev_ts", 0) / 1000, RIYADH).strftime("%H:%M")
    except Exception:
        prev_label = "—"
    try:
        scan_hm = dt.datetime.fromtimestamp(meta.get("ts", now.timestamp() * 1000) / 1000, RIYADH).strftime("%H:%M")
    except Exception:
        scan_hm = now.strftime("%H:%M")
    try:
        track_hm = dt.datetime.fromtimestamp(state.get("track_ts", 0) / 1000, RIYADH).strftime("%H:%M")
        if state.get("track_ts", 0) < 1e12:
            track_hm = scan_hm
    except Exception:
        track_hm = scan_hm
    universe = meta["universe"]
    # ------- تحديث صفقات المسح السابق (held)
    tracked = held or tracked

    def _open_state(x):
        if x.get("open_state") in ("رابحة", "خاسرة", "عند الدخول"):
            return x["open_state"]
        r = float(x.get("r_now") or 0)
        if r > 0:
            return "رابحة"
        if r < 0:
            return "خاسرة"
        return "عند الدخول"

    triggered = [
        x for x in tracked
        if x.get("filled") or x.get("status") in ("مفتوحة", "ضربت الوقف") or str(x.get("status", "")).startswith("وصل")
    ]
    n_tr = len(tracked)
    c_wait = sum(1 for x in tracked if x.get("status") == "بانتظار التفعيل")
    c_cancel = sum(1 for x in tracked if x.get("status") == "أُلغيت (ابتعدت)")
    open_list = [x for x in tracked if x.get("status") == "مفتوحة"]
    c_open = len(open_list)
    c_open_win = sum(1 for x in open_list if _open_state(x) == "رابحة")
    c_open_loss = sum(1 for x in open_list if _open_state(x) == "خاسرة")
    c_open_flat = sum(1 for x in open_list if _open_state(x) == "عند الدخول")
    c_stop = sum(1 for x in tracked if x.get("status") == "ضربت الوقف")
    c_tp = sum(1 for x in tracked if str(x.get("status", "")).startswith("وصل"))
    net_r = sum(
        float(x.get("r_now") or 0)
        for x in tracked
        if x.get("status") not in ("بانتظار التفعيل", "أُلغيت (ابتعدت)", "لا بيانات", None)
    )

    def trrow(x):
        st = x.get("status", "-")
        r = x.get("r_now")
        pnl = x.get("pnl_pct")
        if pnl is None and r is not None and x.get("fill_price") is None and x.get("last") is not None:
            ref = x.get("avg") or x.get("price") or 1
            diff = (x["last"] - ref) if x["side"] == "LONG" else (ref - x["last"])
            pnl = (diff / ref) * 100.0
        rtxt = f"{r:+.2f}R" if r is not None else "—"
        ptxt = f"{pnl:+.2f}%" if pnl is not None else ""
        rowcls = ""
        if st == "مفتوحة":
            ost = _open_state(x)
            if ost == "رابحة":
                badge = '<em class="g owin">🟢 مفتوحة · رابحة</em>'
                rcls = "pos"
                rowcls = ' class="rwin"'
            elif ost == "خاسرة":
                badge = '<em class="g oloss">🔴 مفتوحة · خاسرة</em>'
                rcls = "neg"
                rowcls = ' class="rloss"'
            else:
                badge = '<em class="g oflat">⚪ مفتوحة · عند الدخول</em>'
                rcls = ""
        elif str(st).startswith("وصل"):
            badge = f'<em class="g tpbadge">🎯 {st}</em>'
            rcls = "pos"
        elif st == "ضربت الوقف":
            badge = '<em class="g slbadge">🛑 ضربت الوقف</em>'
            rcls = "neg"
        elif st == "بانتظار التفعيل":
            badge = '<em class="g waitbadge">⏳ بانتظار التفعيل</em>'
            rcls = ""
        elif st == "أُلغيت (ابتعدت)":
            badge = '<em class="g cancelbadge">⛔ أُلغيت (ابتعدت &gt; 1 ATR)</em>'
            rcls = "neg"
            rowcls = ' class="rcancel"'
        else:
            badge = f'<em class="g gc">{st}</em>'
            rcls = ""

        fill_p = x.get("fill_price")
        fill_sub = f'<span class="sub">متوسط التفعيل: {fp(fill_p, x["tick"])}</span>' if fill_p is not None else ""
        last_txt = fp(x["last"], x["tick"]) if x.get("last") is not None else "—"
        dist_now = x.get("dist_now_atr")
        if r is not None:
            res_cell = f'<b class="{rcls}">{rtxt}</b>' + (f'<span class="sub {rcls}">{ptxt}</span>' if ptxt else "")
        elif st == "بانتظار التفعيل" and dist_now is not None:
            res_cell = f'<span style="color:#9ecbff;font-size:11.5px">على بُعد {dist_now:.2f} ATR</span>'
        elif st == "أُلغيت (ابتعدت)" and dist_now is not None:
            res_cell = f'<span class="neg" style="font-size:11.5px">ابتعد {dist_now:.2f} ATR</span>'
        else:
            res_cell = "—"
        sym_link = f'<a href="#t-{x["name"]}">{x["name"]}</a>' if any(t["name"] == x["name"] for t in trades) else x["name"]
        return (
            f'<tr{rowcls} data-sym="{x["name"]}"><td class="sym">{sym_link}</td>'
            f'<td class="c"><span class="pill {"long" if x["side"]=="LONG" else "short"}">{x["side"]}</span></td>'
            f'<td class="n">{fp(x["entry_lo"], x["tick"])} – {fp(x["entry_hi"], x["tick"])}{fill_sub}</td>'
            f'<td class="n sl">{fp(x["stop"], x["tick"])}</td>'
            f'<td class="n">{last_txt}</td>'
            f'<td class="n" style="text-align:center">{res_cell}</td>'
            f'<td class="c">{badge}</td></tr>'
        )

    def _tr_sort_key(x):
        st = x.get("status", "")
        rv = float(x.get("r_raw") if x.get("r_raw") is not None else (x.get("r_now") or 0))
        dn = float(x.get("dist_now_atr") or 99)
        if st == "مفتوحة":
            ost = _open_state(x)
            sub_ord = {"رابحة": 0, "عند الدخول": 1, "خاسرة": 2}.get(ost, 1)
            return (0, sub_ord, -rv, x["name"])
        if str(st).startswith("وصل"):
            return (1, 0, -rv, x["name"])
        if st == "ضربت الوقف":
            return (2, 0, 0, x["name"])
        if st == "بانتظار التفعيل":
            return (3, 0, dn, x["name"])
        if st == "أُلغيت (ابتعدت)":
            return (4, 0, dn, x["name"])
        return (5, 0, 0, x["name"])

    track_rows = "".join(trrow(x) for x in sorted(tracked, key=_tr_sort_key))

    win_items = sorted([x for x in open_list if _open_state(x) == "رابحة"], key=lambda z: -(z.get("r_now") or 0))
    loss_items = sorted([x for x in open_list if _open_state(x) == "خاسرة"], key=lambda z: (z.get("r_now") or 0))
    top_win_txt = " · ".join(f'{x["name"]} (<span class="pos">{x["r_now"]:+.2f}R</span>)' for x in win_items[:6]) or "—"
    loss_txt = " · ".join(f'{x["name"]} (<span class="neg">{x["r_now"]:+.2f}R</span>)' for x in loss_items) or "لا توجد مراكز مفتوحة خاسرة حالياً"
    flat_sub = f'<span class="sub">عند الدخول: {c_open_flat}</span>' if c_open_flat else ""
    open_summary_html = (
        f'<div class="note" style="background:#0c1420;border-color:#1c2941;margin:8px 0 10px;padding:11px 14px;font-size:12.5px">'
        f'<div><b class="pos">🟢 المفتوحة الرابحة ({c_open_win}):</b> أبرزها {top_win_txt}</div>'
        f'<div style="margin-top:4px"><b class="neg">🔴 المفتوحة الخاسرة ({c_open_loss}):</b> {loss_txt}</div>'
        f'</div>'
    ) if c_open else ""


    css = """
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:#080c12;color:#e6edf5;font-family:'Segoe UI',Tahoma,system-ui,sans-serif;line-height:1.65}
.wrap{max-width:1280px;margin:0 auto;padding:24px 16px 80px}
h1{font-size:24px;margin:0 0 4px}h2{font-size:19px;margin:34px 0 12px;padding-right:12px;border-right:4px solid #2f81f7;scroll-margin-top:80px}
h3{font-size:15px;margin:18px 0 8px;color:#b9c9dc}
.sub{color:#8798ab;font-size:12px;display:block}
.stamp{display:inline-block;background:#0b3b4d;color:#5ee0ff;border:1px solid #155e75;border-radius:20px;padding:4px 14px;font-size:13px;font-weight:700;margin-bottom:10px}
.hero{background:linear-gradient(135deg,#101a2a,#0c131d);border:1px solid #1e2c42;border-radius:16px;padding:20px 22px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin-top:16px}
.kpi{background:#0e1725;border:1px solid #1c2941;border-radius:12px;padding:11px 13px}
.kpi span{display:block;color:#8798ab;font-size:11px}.kpi b{font-size:17px}
.note{background:#1a1509;border:1px solid #6b5218;border-radius:14px;padding:16px 18px;margin:16px 0;font-size:13.5px}
.note b{color:#ffd479}
.warn{background:#1e1116;border:1px solid #6b2432;border-radius:14px;padding:14px 18px;margin:14px 0;font-size:13.5px}
.okbox{background:#0b1f16;border:1px solid #1c5c39;border-radius:14px;padding:14px 18px;margin:14px 0;font-size:13.5px}
.twrap{width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch;border-radius:12px;margin:8px 0 4px}
table{width:100%;min-width:680px;border-collapse:collapse;font-size:12.5px;background:#0c1320;border-radius:12px;overflow:hidden;margin:0}
.appbar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;justify-content:space-between;background:#0d1626;border:1px solid #1f3352;border-radius:14px;padding:10px 14px;margin-bottom:14px}
.appbtns{display:flex;flex-wrap:wrap;gap:7px}
.abtn{appearance:none;border:1px solid #2b456b;background:#13233a;color:#e6edf5;border-radius:10px;padding:8px 13px;font-size:12.5px;font-weight:700;cursor:pointer;font-family:inherit;display:inline-flex;align-items:center;gap:5px}
.abtn:active{transform:scale(.97)}
.abtn.pri{background:linear-gradient(135deg,#1d4ed8,#2563eb);border-color:#3b82f6;color:#fff}
.abtn.conf{background:linear-gradient(135deg,#92400e,#b45309);border-color:#f59e0b;color:#fff}
.modal-bg{display:none;position:fixed;inset:0;background:rgba(4,8,15,.82);z-index:999;align-items:center;justify-content:center;padding:16px}
.modal-bg.open{display:flex}
.modal{background:#0f1929;border:1px solid #294166;border-radius:16px;max-width:460px;width:100%;padding:20px;color:#e6edf5}
.modal input{width:100%;padding:10px 12px;border-radius:10px;border:1px solid #2b456b;background:#080e18;color:#fff;direction:ltr;font-size:13px;margin:6px 0 12px}
.status-toast{display:none;background:#0d2818;border:1px solid #22c55e;color:#86efac;padding:10px 14px;border-radius:12px;margin-bottom:12px;font-size:13px;font-weight:600}
.tools-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:14px 0}
.tbox{background:#0d1626;border:1px solid #223859;border-radius:14px;padding:13px 15px}
.tbox h3{margin:0 0 6px;font-size:14px;color:#93c5fd;display:flex;align-items:center;gap:6px}
.tbox .tsub{font-size:11.5px;color:#8798ab;margin-bottom:9px}
.tinp-row{display:flex;gap:7px;align-items:center}
.tinp{flex:1;min-width:0;padding:9px 12px;border-radius:10px;border:1px solid #2b456b;background:#070d17;color:#fff;font-size:13.5px;font-weight:700;direction:ltr;text-align:left}
.tinp::placeholder{color:#5c7089;font-weight:400;direction:rtl;text-align:right}
.sres{display:none;margin-top:10px;padding:10px 12px;border-radius:11px;background:#091220;border:1px solid #1e3354;font-size:12.5px;line-height:1.75}
@media(max-width:760px){.tools-grid{grid-template-columns:1fr}}
@media(max-width:680px){.wrap{padding:12px 10px 76px}h1{font-size:19px}.hero{padding:15px}.abtn{flex:1 1 auto;justify-content:center;padding:9px 10px;font-size:12px}}
th{background:#152033;color:#9db1c8;font-weight:600;padding:9px 7px;text-align:right;font-size:11px;white-space:nowrap}
td{padding:8px 7px;border-top:1px solid #16223a;vertical-align:middle}
tr:hover td{background:#111c2c}
.n{direction:ltr;text-align:left;font-variant-numeric:tabular-nums;white-space:nowrap;font-weight:600}
.n .sub{font-size:9.5px;color:#7d8ea3;font-weight:400}
.c{text-align:center}.sym{font-weight:700;white-space:nowrap}.sym a{color:#e6edf5;text-decoration:none}.sym a:hover{color:#79b8ff}
.sl{color:#f87171}.tp{color:#86e0a0}
.pill{display:inline-block;padding:1px 8px;border-radius:20px;font-size:10.5px;font-weight:700}
.pill.long{background:#0e2f1d;color:#4ade80;border:1px solid #1c5c39}
.pill.short{background:#2f1319;color:#f87171;border:1px solid #5c2029}
.g{font-style:normal;font-size:10.5px;padding:1px 7px;border-radius:6px;font-weight:700;white-space:nowrap}
.ga{background:#0b3b4d;color:#5ee0ff}.gb{background:#2a2a12;color:#e3c34a}.gc{background:#331124;color:#e879c7}
.ntag{background:#1a1130;color:#c4a6ff;border:1px solid #4c2a85}.ktag{background:#101a24;color:#7d8ea3;border:1px solid #24384f}
.trtag{background:#2a1d08;color:#fbbf24;border:1px solid #784f12}
.ra{background:#0e2f1d;color:#4ade80}.rb{background:#1c2a12;color:#c9e06a}.rc{background:#2f1319;color:#f87171}
.owin{background:#0d3320;color:#4ade80;border:1px solid #1f7a46;padding:2px 9px}
.oloss{background:#3a1219;color:#ff8585;border:1px solid #8a2838;padding:2px 9px}
.oflat{background:#162436;color:#9ecbff;border:1px solid #2b4566;padding:2px 9px}
.tpbadge{background:#0b3b2c;color:#6ee7b7;border:1px solid #18795b;padding:2px 9px}
.slbadge{background:#2d1218;color:#f87171;border:1px solid #6b2432;padding:2px 9px}
.waitbadge{background:#12243a;color:#9ecbff;border:1px solid #254b75;padding:2px 9px}
.cancelbadge{background:#25151a;color:#fca5a5;border:1px solid #592531;padding:2px 9px}
tr.rwin td:first-child{box-shadow:inset -3px 0 0 #22c55e}
tr.rloss{background:rgba(239,68,68,.045)}
tr.rloss td:first-child{box-shadow:inset -3px 0 0 #ef4444}
tr.rcancel td{opacity:.68}
.pos{color:#4ade80}.neg{color:#f87171}
.card{background:#0c1320;border:1px solid #1c2941;border-radius:16px;margin:14px 0;overflow:hidden;scroll-margin-top:80px}
.card.long{border-right:4px solid #22c55e}.card.short{border-right:4px solid #ef4444}
.chead{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;padding:12px 16px;background:#111b2b}
.csym{font-size:17px;font-weight:700}.csym span{color:#6b7c92;font-size:12.5px}
.csym small{color:#7d8ea3;font-size:10.5px;margin-right:6px}.csym em{margin-right:5px}
.cbody{padding:14px 16px}
.levels{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:9px}
.lv{background:#0e1725;border:1px solid #1c2941;border-radius:11px;padding:9px 11px}
.lv span{display:block;color:#8798ab;font-size:10.5px}
.lv b{font-size:14.5px;direction:ltr;display:block;font-variant-numeric:tabular-nums}
.lv i{display:block;color:#7d8ea3;font-size:10px;font-style:normal}
.lv.entry{border-color:#2f81f7;background:#0d1a2e}.lv.entry b{color:#9ecbff}
.lv.stop{border-color:#7f1d1d;background:#1a0f12}.lv.stop b{color:#f87171}
.lv.t1,.lv.t2{border-color:#14532d}.lv.t1 b,.lv.t2 b{color:#4ade80}
.lv.t3{border-color:#155e75}.lv.t3 b{color:#5ee0ff}
.meta{display:grid;grid-template-columns:repeat(auto-fit,minmax(132px,1fr));gap:7px;margin-top:11px;font-size:11.5px}
.meta div{background:#0a111c;border-radius:8px;padding:6px 9px;display:flex;justify-content:space-between;gap:6px}
.meta div.sr{grid-column:span 2;background:#0c1420;border:1px solid #1b2740}
.meta span{color:#7d8ea3}.meta b{font-weight:600;text-align:left}
.plan{margin-top:11px;background:#0b1526;border:1px dashed #24406b;border-radius:9px;padding:8px 11px;font-size:11.5px;color:#9fb3c9}
.plan b{color:#79b8ff}
.nav{position:sticky;top:0;z-index:40;display:flex;gap:8px;flex-wrap:wrap;background:rgba(8,12,18,.95);backdrop-filter:blur(8px);padding:10px 12px;margin:16px 0 6px;border:1px solid #1e2c42;border-radius:14px}
.nav a{text-decoration:none;font-size:12.5px;font-weight:700;padding:7px 14px;border-radius:10px;color:#9db1c8;background:#152033;border:1px solid #1e2c42;transition:.15s}
.nav a:hover{color:#fff;background:#1c2a41;transform:translateY(-1px)}
.nav a.longb{background:#0e2f1d;color:#4ade80;border-color:#1c5c39}
.nav a.longb:hover{background:#14472c;color:#86efac}
.nav a.shortb{background:#2f1319;color:#f87171;border-color:#5c2029}
.nav a.shortb:hover{background:#43191f;color:#fca5a5}
.nav a.expb{background:#2f1f09;color:#fbbf24;border-color:#784f12}
.nav a.expb:hover{background:#452c0c;color:#fde68a}
.nav a.invb{background:linear-gradient(135deg,#24133d,#10293d);color:#d8b4fe;border-color:#6d28d9}
.nav a.invb:hover{background:linear-gradient(135deg,#331a57,#163a54);color:#f3e8ff}
.nav .cnt{background:rgba(255,255,255,.12);border-radius:20px;padding:0 7px;font-size:11px;margin-right:4px}
h2.hlong{border-right-color:#22c55e}
h2.hshort{border-right-color:#ef4444}
h2.hexp{border-right-color:#f59e0b}
h2.hinv{border-right-color:#a855f7}
h2.hbos{border-right-color:#38bdf8}
.card.exp{border-right:4px solid #f59e0b;background:#0e131d}
.card.inv{border-right:4px solid #a855f7;background:#0e1120}
.card.bos{border-right:4px solid #38bdf8;background:#0b1522}
.expbadge{background:#382408;color:#fbbf24;border:1px solid #855512;padding:2px 9px}
.invbadge{background:#281442;color:#d8b4fe;border:1px solid #7e22ce;padding:2px 9px}
.bosbadge{background:#0c2d48;color:#7dd3fc;border:1px solid #0284c7;padding:2px 9px}
.crownbadge{background:linear-gradient(135deg,#422006,#3b0764);color:#fde047;border:1px solid #eab308;padding:2px 9px}
.ltbar{background:linear-gradient(135deg,#0d192b,#0a1220);border:1px solid #243b5e;border-radius:14px;padding:11px 15px;margin-bottom:14px;display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between}
.ltpills{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.ltp{background:#08101c;border:1px solid #1e314d;border-radius:10px;padding:5px 11px;font-size:12.5px;display:inline-flex;align-items:center;gap:6px}
.ltp b{font-size:14px;font-variant-numeric:tabular-nums}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0 12px}
.chip{text-decoration:none;font-size:11.5px;font-weight:700;padding:4px 10px;border-radius:8px;background:#101a29;border:1px solid #1e2c42;color:#cbd8e8}
.chip.long:hover{border-color:#22c55e;color:#4ade80;background:#0e2419}
.chip.short:hover{border-color:#ef4444;color:#f87171;background:#271217}
.top{position:fixed;left:16px;bottom:16px;z-index:60;background:#152033;color:#9db1c8;border:1px solid #1e2c42;border-radius:50%;width:44px;height:44px;display:flex;align-items:center;justify-content:center;text-decoration:none;font-size:18px;font-weight:700}
.top:hover{color:#fff;background:#1f304d}
.bars{display:grid;gap:6px;margin:10px 0}
.bar{display:grid;grid-template-columns:88px 1fr 52px;align-items:center;gap:9px;font-size:11.5px}
.bar .tr{background:#111c2c;border-radius:6px;height:16px;overflow:hidden}
.bar .fl{height:100%;background:linear-gradient(90deg,#2f81f7,#5ee0ff)}
.bar .fl.red{background:linear-gradient(90deg,#7f1d1d,#f87171)}
ul{margin:8px 0;padding-right:20px}li{margin:4px 0;font-size:13px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:760px){.grid2{grid-template-columns:1fr}}
"""

    bars = ""
    for th, lab in ((0.4, "0.4 ATR"), (0.6, "0.6 ATR"), (0.8, "0.8 ATR"), (1.0, "1.0 ATR"), (1.2, "1.2 ATR")):
        pu = sum(1 for x in stats["up"] if x >= th) / len(stats["up"]) * 100
        pd = sum(1 for x in stats["dn"] if x >= th) / len(stats["dn"]) * 100
        bars += f'<div class="bar"><span>صعود {lab}</span><div class="tr"><div class="fl" style="width:{pu:.0f}%"></div></div><b>{pu:.0f}%</b></div>'
        bars += f'<div class="bar"><span>هبوط {lab}</span><div class="tr"><div class="fl red" style="width:{pd:.0f}%"></div></div><b>{pd:.0f}%</b></div>'

    table_all = "".join(row(t, i + 1) for i, t in enumerate(trades))

    def _chips(arr, cls):
        if not arr:
            return ""
        return '<div class="chips">' + "".join(
            f'<a class="chip {cls}" data-sym="{t["name"]}" href="#t-{t["name"]}">{t["name"]}</a>' for t in arr
        ) + '</div>'

    side_sections = ""
    for title, arr, idd, hcls, ccls, desc in (
        ("🟢 صفقات الشراء LONG", longs, "longs", "hlong", "long", "مرتبة بالأولوية وقرب منطقة الدخول · الشراء من مناطق الدعم"),
        ("🔴 صفقات البيع SHORT", shorts, "shorts", "hshort", "short", "مرتبة بالأولوية وقرب منطقة الدخول · البيع من مناطق المقاومة"),
    ):
        side_sections += f'<h2 id="{idd}" class="{hcls}">{title} — {len(arr)}</h2><div class="sub" style="margin-bottom:8px">{desc}</div>'
        if arr:
            side_sections += _chips(arr, ccls)
            side_sections += "".join(card(t, i, with_id=True) for i, t in enumerate(arr))
        else:
            side_sections += '<div class="note" style="background:#0d1622;border-color:#1e2c42">لا توجد صفقات مؤهلة في هذا الاتجاه خلال هذه الدورة.</div>'

    # ------- قسم العملات القابلة للانفجار مع الافتتاح اليومي
    exp_active = (exp_data or {}).get("active") or []
    exp_cancelled = (exp_data or {}).get("cancelled") or []
    exp_stage = (exp_data or {}).get("stage") or "radar"

    def card_exp(e):
        gcol = {"A": "ga", "B": "gb", "C": "gc"}.get(e.get("grade", "B"), "gb")
        tg = "".join(
            f'<div class="lv t{k+1}"><span>هدف {k+1}{" (قمة اليوم+)" if k==0 else ""}</span><b>{fp(e["targets"][k], e["tick"])}</b>'
            f'<i>{((e["targets"][k]/e["avg"]-1)*100):+.2f}% · R{e["rr"][k]:.2f}</i></div>'
            for k in range(3)
        )
        sup_txt = " · ".join(fp(x, e["tick"]) for x in e.get("supports", [])[:3])
        res_txt = " · ".join(fp(x, e["tick"]) for x in e.get("resistances", [])[:3])
        reasons_txt = " · ".join(e.get("reasons") or []) or "—"
        fcls = "pos" if e["funding"] <= 0 else "neg"
        return f'''
<article class="card exp" id="exp-{e["name"]}" data-sym="{e["name"]}">
  <div class="chead">
    <div class="csym">🔥 {e["name"]}<span>/USDT</span> <small>{e["score"]:.1f} نقطة</small>
      <em class="g {gcol}">درجة {e["grade"]}</em>
      <em class="g expbadge">{e.get("stage_label", "قابلة للانفجار")}</em>
    </div>
    <div><span class="pill long">اصطياد ذيل LONG</span></div>
  </div>
  <div class="cbody">
    <div class="levels">
      <div class="lv entry"><span>منطقة صيد الذيل (Limit)</span><b>{fp(e["entry_lo"], e["tick"])} – {fp(e["entry_hi"], e["tick"])}</b><i>{e["dist_pct"]:+.2f}% عن السعر · {e["dist_atr"]:.2f} ATR</i></div>
      <div class="lv stop"><span>الوقف البنيوي</span><b>{fp(e["stop"], e["tick"])}</b><i>مخاطرة {e["risk_pct"]:.2f}%</i></div>
      {tg}
    </div>
    <div class="meta">
      <div><span>السعر الآن</span><b>{fp(e["price"], e["tick"])}</b></div>
      <div><span>موقع السعر في مدى 24س</span><b class="pos">{e["pos24"]:.1f}% (قرب القمة)</b></div>
      <div><span>تغيّر 24س</span><b class="pos">{e["chg"]:+.2f}%</b></div>
      <div><span>Δ OI (4س)</span><b class="{'pos' if e['oi_chg']>=0 else 'neg'}">{e["oi_chg"]:+.2f}%</b></div>
      <div><span>فاندنغ</span><b class="{fcls}">{e["funding"]:+.4f}%</b></div>
      <div><span>سيولة 24س</span><b>{e["qv"]:,.1f}M$</b></div>
      <div><span>RSI 4س/يومي</span><b>{e["rsi4"]:.0f}/{e["rsi1"]:.0f}</b></div>
      <div><span>حجم المركز (1000$)</span><b>{e["qty"]:,.4f}</b></div>
      <div class="sr"><span>الدعوم</span><b class="pos">{sup_txt}</b></div>
      <div class="sr"><span>المقاومات</span><b class="neg">{res_txt}</b></div>
      <div class="sr"><span>بصمة الانفجار</span><b style="color:#fbbf24">{reasons_txt}</b></div>
    </div>
    <div class="plan"><b>خطة اصطياد ذيل آسيا:</b> ممنوع الشراء السوقي عند 03:00 ← علّق Limit في منطقة صيد الذيل بعد تأكيد 02:45 ← اترك الأمر يلتقط تلاعب آسيا (انطلاقة البدائل ~04:30 والكبار ~06:30) ← أغلق 50% عند هدف 1 وانقل الوقف للتعادل.</div>
  </div>
</article>'''

    if exp_stage == "confirm":
        exp_banner = '<div class="okbox"><b>✅ مرحلة التأكيد النهائي (02:45 قبل الإغلاق اليومي):</b> هذه العملات حافظت على تماسكها في الربع العلوي حتى نهاية اليوم — علّق أوامر <b>Limit</b> في منطقة صيد الذيل الآسيوي (لا شراء سوقي عند 03:00).</div>'
    elif exp_stage == "active":
        exp_banner = '<div class="okbox"><b>🎯 مصيدة ذيل آسيا نشطة (03:00 – 07:00):</b> الجلسة الآسيوية تصنع الآن الذيل اليومي — اترك أوامر <b>Limit</b> المعلّقة تعمل بهدوء دون مطاردة.</div>'
    elif exp_stage == "daytime":
        exp_banner = '<div class="note"><b>ℹ️ ملاحظة التوقيت:</b> الرصد الرسمي لقائمة الانفجار يبدأ في مسح <b>23:05</b> ويُؤكَّد في فحص <b>02:45</b> قبل الإغلاق اليومي. ما يظهر أدناه معاينة نهارية للعملات المتماسكة في قممها حالياً.</div>'
    else:
        exp_banner = '<div class="note"><b>📡 مرحلة الرصد المبكر (23:05 — للمراقبة فقط):</b> ~40% من مرشحات الليل تفقد تماسكها قبل الفجر؛ لذلك <b>تُراقب فقط الآن</b> ويتم تثبيت الصامد منها وشطب الفاشل في <b>فحص التأكيد 02:45</b> قبل الإغلاق اليومي.</div>'

    cancel_box = ""
    if exp_cancelled:
        c_items = " · ".join(f'<b>{c["name"]}</b> ({c.get("cancel_reason", "فقدت التماسك")})' for c in exp_cancelled)
        cancel_box = f'<div class="warn"><b>⛔ شُطبت في فحص التأكيد (02:45):</b> {c_items}</div>'

    exp_section = f'<h2 id="explode" class="hexp">🔥 عملات قابلة للانفجار مع الافتتاح اليومي — {len(exp_active)}</h2>'
    exp_section += exp_banner + cancel_box
    if exp_active:
        exp_section += "".join(card_exp(e) for e in exp_active)
    else:
        exp_section += '<div class="note" style="background:#0d1622;border-color:#1e2c42">لا توجد عملات تستوفي شروط الانفجار الصارمة في هذه اللحظة.</div>'

    # ------- قسم العملات الاستثمارية (العصر والقاع) + كسر الهيكل اليومي النشط (المحرّك المزدوج)
    inv_squeeze = (macro_data or {}).get("squeeze") or []
    bos_active = (macro_data or {}).get("bos3") or []
    btc_reg = (macro_data or {}).get("btc_regime") or {"state": "neutral", "label": "🟡 مناخ محايد", "advice": "التزم بوقف صريح 1% لكل صفقة."}
    n_macro = len(inv_squeeze) + len(bos_active)

    def card_inv(m):
        tg = "".join(
            f'<div class="lv t{k+1}"><span>هدف استثماري {k+1}</span><b>{fp(m["targets"][k], m["tick"])}</b>'
            f'<i>{((m["targets"][k]/m["avg"]-1)*100):+.1f}% · R{m["rr"][k]:.1f}</i></div>'
            for k in range(3)
        )
        fcls = "pos" if m["funding"] <= 0 else "neg"
        reasons_txt = " · ".join(m.get("reasons") or [])
        pos_usd = m.get("pos_usd_1r", 100.0)
        return f'''
<article class="card inv" id="inv-{m["name"]}" data-sym="{m["name"]}">
  <div class="chead">
    <div class="csym">💎 {m["name"]}<span>/USDT</span> <small>{m["score"]:.1f} نقطة</small>
      <em class="g invbadge">{m["badge"]}</em>
    </div>
    <div><span class="pill" style="background:#281442;color:#e9d5ff;border:1px solid #7e22ce">استثمارية · تجميع قاعي (+0.39R EV)</span></div>
  </div>
  <div class="cbody">
    <div class="levels">
      <div class="lv entry" style="border-color:#8b5cf6;background:#150f29"><span>منطقة التمركز وصيد التلاعب (دفعتين)</span><b style="color:#ddd6fe">{fp(m["entry_lo"], m["tick"])} – {fp(m["entry_hi"], m["tick"])}</b><i>{m["dist_pct"]:+.2f}% عن السعر · تشمل جيب التلاعب السُفلي</i></div>
      <div class="lv stop"><span>وقف صريح إلزامي في المنصة (Hard Stop)</span><b>{fp(m["stop"], m["tick"])}</b><i>مخاطرة السعر {m["risk_pct"]:.2f}% ← حجم الصفقة {pos_usd:.0f}$ لكل 1000$ (= 1R)</i></div>
      {tg}
    </div>
    <div class="meta">
      <div><span>السعر الآن</span><b>{fp(m["price"], m["tick"])}</b></div>
      <div><span>نطاق العصر الأفقي (20ي)</span><b style="direction:ltr">{fp(m["box_floor"], m["tick"])} – {fp(m["box_ceil"], m["tick"])} ({m["box_pct"]:.1f}%)</b></div>
      <div><span>موقع القاع الكلي (180ي)</span><b class="pos">{m["pos180"]:.1f}% (منطقة قاع)</b></div>
      <div><span>شدة العصر والانكماش</span><b style="color:#d8b4fe">{m["squeeze_pct"]:.0f}%</b></div>
      <div><span>RSI اليومي</span><b>{m["rsi_d"]:.1f}</b></div>
      <div><span>فاندنغ</span><b class="{fcls}">{m["funding"]:+.4f}%</b></div>
      <div><span>سيولة 24س</span><b>{m["qv"]:,.1f}M$</b></div>
      <div><span>بصمة التجميع والدفاع الشرائي</span><b style="color:#c4b5fd">{reasons_txt}</b></div>
    </div>
    <div class="plan" style="border-color:#6d28d9;background:#120d24;color:#d8b4fe"><b style="color:#e9d5ff">القاعدة العلمية الصارمة للتنفيذ:</b> لا توجد عملة مضمونة الصعود 100%؛ التفوق الإحصائي هنا (+0.39R) يأتي من <b>تثبيت أمر وقف صريح (Hard Stop) في المنصة</b> تحت ذيل التلاعب وتصغير حجم المركز إلى <b>{pos_usd:.0f}$</b> (من كل 1000$ بالمحفظة · <b>Spot أو رافعة 1x–2x فقط</b>) بحيث يستحيل أن تتجاوز الخسارة <b>-1R (1%)</b> حتى لو انهار السوق فجأة، بينما تُغلق 50% عند هدف 1 ويُنقل الوقف للتعادل.</div>
  </div>
</article>'''

    def card_bos(b):
        tg = "".join(
            f'<div class="lv t{k+1}"><span>هدف موجة {k+1}</span><b>{fp(b["targets"][k], b["tick"])}</b>'
            f'<i>{((b["targets"][k]/b["avg"]-1)*100):+.1f}% · R{b["rr"][k]:.1f}</i></div>'
            for k in range(3)
        )
        c_note = b.get("close_note") or " ← ".join(fp(x, b["tick"]) for x in b["closes_3"])
        kind_b = b.get("kind_badge", "🚀 كسر هيكل يومي")
        crown = '<em class="g crownbadge">👑 جوهرة متكاملة (خرجت من قاع تجميعي)</em>' if b.get("from_squeeze") else ""
        bos_lev = "2x–3x" if b["risk_pct"] <= 9.0 else "Spot أو 1x–2x"
        pos_usd_b = round((10.0 / abs(b["avg"] - b["stop"])) * b["avg"], 0) if abs(b["avg"] - b["stop"]) > 0 else 100
        room_note = (
            f'<div><span>قمة 30 يوماً المستهدفة</span><b style="color:#fde047">{fp(b.get("hi30_ref", b["struct_lvl"]), b["tick"])} (+{b.get("room_30d_pct", 0):.1f}% مساحة مفتوحة)</b></div>'
            if b.get("bos_kind") in ("uptrend3g", "hammer1d") and b.get("room_30d_pct", 0) > 0
            else f'<div><span>السقف المكسور ({b["lvl_type"]})</span><b class="pos">{fp(b["struct_lvl"], b["tick"])}</b></div>'
        )
        w_sum = b.get("w_summary", "—")
        m_sum = b.get("m_summary", "—")
        return f'''
<article class="card bos" id="bos-{b["name"]}" data-sym="{b["name"]}">
  <div class="chead">
    <div class="csym">🚀 {b["name"]}<span>/USDT</span> <small>{b["score"]:.1f} نقطة</small>
      <em class="g bosbadge">{kind_b}</em>
      <em class="g" style="background:#0f291e;color:#6ee7b7;border:1px solid #15803d">{b["state_lbl"]}</em> {crown}
    </div>
    <div><span class="pill" style="background:#0c2d48;color:#7dd3fc;border:1px solid #0284c7">زخم / كسر يومي + تأييد 1W/1M</span></div>
  </div>
  <div class="cbody">
    <div class="levels">
      <div class="lv entry" style="border-color:#0284c7;background:#0a1d30"><span>منطقة التراجع / إعادة الاختبار (Limit)</span><b style="color:#bae6fd">{fp(b["entry_lo"], b["tick"])} – {fp(b["entry_hi"], b["tick"])}</b><i>{b["dist_pct"]:+.2f}% عن السعر · بُعد {b["dist_atr"]:.2f} ATR يومي</i></div>
      <div class="lv stop"><span>وقف صريح إلزامي (Hard Stop)</span><b>{fp(b["stop"], b["tick"])}</b><i>مخاطرة {b["risk_pct"]:.2f}% ({bos_lev} · حجم {pos_usd_b:.0f}$ لكل 1000$)</i></div>
      {tg}
    </div>
    <div class="meta">
      <div><span>السعر الآن</span><b>{fp(b["price"], b["tick"])}</b></div>
      {room_note}
      <div class="sr"><span>الإغلاقات اليومية الخضراء بالجسم الكامل</span><b style="color:#7dd3fc;direction:ltr">{c_note}</b></div>
      <div class="sr"><span>📅 قراءة شمعة الأسبوع (1W)</span><b style="color:#93c5fd">{w_sum}</b></div>
      <div class="sr"><span>🗓️ قراءة شمعة الشهر (1M)</span><b style="color:#c4b5fd">{m_sum}</b></div>
      <div><span>تدفق السيولة المؤسسية</span><b class="pos">{b["vol_x"]:.2f}x من متوسط 20ي</b></div>
      <div><span>RSI اليومي</span><b>{b["rsi_d"]:.1f}</b></div>
      <div><span>سيولة 24س</span><b>{b["qv"]:,.1f}M$</b></div>
    </div>
    <div class="plan" style="border-color:#0284c7;background:#091829;color:#bae6fd"><b style="color:#7dd3fc">خطة التنفيذ المتوافقة مع 1D + 1W + 1M (+0.51R EV):</b> العملة مدعومة ببنية أسبوعية وشهرية سليمة وأغلقت شموعاً يومية خضراء ممتلئة الجسم · <b>لا تطارد القمة سوقياً؛ علّق أمر Limit في منطقة التراجع/إعادة الاختبار مع وقف صريح في المنصة</b>.</div>
  </div>
</article>'''

    is_late_now = (_cur_dt.hour >= 23 or _cur_dt.hour < 3)
    daily_clock_note = (
        "🌙 <b>التوقيت الليلي المتأخر (بعد 23:05 — اكتمل &gt;83% من الشمعة اليومية):</b> مفعَّل الآن احتساب شمعة اليوم الجارية القوية التي لا يواجهها عائق مقاومة قريب (دقة ثبات 96.6%)، وكذلك شمعة الهمر الانعكاسية (🔨 Hammer بذيل رفض سُفلي &ge;55% في اتجاه صاعد)."
        if is_late_now else
        "☀️ <b>التوقيت النهاري (قبل 23:05 — وقت طويل على الإغلاق اليومي 03:00):</b> يتم <b>تجاهل شمعة اليوم الجارية غير المكتملة تماماً</b> في حساب الإغلاقات، والاعتماد حصراً على الشموع اليومية المغلقة (أو همر أمس المغلق) حتى يحين مسح <b>23:05</b>."
    )
    reg_bg = "#092115" if btc_reg["state"] == "bull" else ("#1f1908" if btc_reg["state"] == "oversold" else "#23120b")
    reg_bd = "#1b683e" if btc_reg["state"] == "bull" else ("#855512" if btc_reg["state"] == "oversold" else "#9a3412")
    macro_section = f'''
<div id="macro" style="scroll-margin-top:75px">
  <h2 class="hinv">💎 العملات الاستثمارية وكسر الهيكل اليومي (1D) — {n_macro} عملة</h2>
  <div class="note" style="background:{reg_bg};border-color:{reg_bd};margin-bottom:8px">
    <b>🧭 مؤشر مناخ البيتكوين اليومي للتمركز: {btc_reg["label"]}</b> — {btc_reg["advice"]}
  </div>
  <div class="note" style="background:#0b1526;border-color:#1e3a5f;margin-top:0;margin-bottom:10px;padding:11px 15px;font-size:12.5px">
    {daily_clock_note}
  </div>
  <div class="grid2" style="margin-bottom:12px">
    <div class="note" style="background:#120d22;border-color:#581c87;margin:0">
      <b style="color:#e9d5ff">🟣 أولاً: 🧲 العملات الاستثمارية (مرحلة العصر والقاع — {len(inv_squeeze)})</b><br>
      تُشترط هنا <b>علامة دفاع شرائي فعلية</b> (اكتمال ذيل التلاعب السُفلي <i>Spring</i> أو انحراف تعافي <i>RSI</i>) لاستبعاد العملات الميتة، مع <b>أمر وقف صريح إلزامي (Hard Stop)</b> وتصغير حجم المركز ليبقى أقصى خطر -1R بالضبط.
    </div>
    <div class="note" style="background:#091829;border-color:#0369a1;margin:0">
      <b style="color:#7dd3fc">🩵 ثانياً: 🚀 الكسر اليومي + 3 إغلاقات صاعدة + الهمر الانعكاسي (1D + 1W + 1M — {len(bos_active)})</b><br>
      يرصد: <b>(1) كسر قمة 30 يوماً</b>، و<b>(2) 3 إغلاقات خضراء صاعدة قبل قمة 30ي بمساحة &ge;1.8R</b>، و<b>(3) 🔨 شمعة الهمر الانعكاسية بذيل رفض سُفلي &ge;55% داخل اتجاه صاعد</b> (تُتجاهل شمعة اليوم الحية نهاراً ولا تُقرأ إلا بعد <b>23:05</b>)، مع شرط <b>EMA20 الأسبوعي وأرضية الشهر السابق</b>.
    </div>
  </div>
  <h2 class="hinv" style="font-size:16.5px;margin-top:14px">🧲 1) قائمة العصر الأفقي والقاع الاستثماري المؤيد بدفاع شرائي — {len(inv_squeeze)}</h2>
  {"".join(card_inv(m) for m in inv_squeeze) if inv_squeeze else '<div class="note" style="background:#0d1622;border-color:#1e2c42">لا توجد عملات في قاع وعصر أفقي مكتمل مع دفاع شرائي في هذه اللحظة.</div>'}
  <h2 class="hbos" style="font-size:16.5px;margin-top:20px">🚀 2) قائمة الكسر اليومي و3 إغلاقات صاعدة بالجسم المؤيدة بشمعتي الأسبوع والشهر — {len(bos_active)}</h2>
  {"".join(card_bos(b) for b in bos_active) if bos_active else '<div class="note" style="background:#0d1622;border-color:#1e2c42">لا توجد حالياً أي عملة حققت إغلاقات الأجسام الخضراء اليومية (فوق قمة 30 يوماً أو في اتجاه صاعد قبلها بمساحة مفتوحة) مع اجتياز شرطي شمعة الأسبوع (1W) وشمعة الشهر (1M) ضمن مسافة الدخول.</div>'}
</div>'''

    # ------- شريط العداد التراكمي العام منذ بدء التشغيل
    lt_w = int((lt_stats or {}).get("wins", 0))
    lt_l = int((lt_stats or {}).get("losses", 0))
    lt_tot = lt_w + lt_l
    lt_wr = (lt_w / lt_tot * 100.0) if lt_tot > 0 else 0.0
    lt_net = float((lt_stats or {}).get("net_r", 0.0))
    lt_since = (lt_stats or {}).get("started_at", ts)
    lifetime_bar_html = f'''
<div class="ltbar">
  <div style="font-size:12.5px;font-weight:700;color:#cbd5e1">
    📊 السجل التراكمي العام للصفقات المحسومة <span style="color:#7d8ea3;font-weight:400">(منذ {lt_since} · يُحدَّث آلياً مع كل تقرير)</span>
  </div>
  <div class="ltpills">
    <div class="ltp"><span>✅ رابحة مغلقة:</span><b class="pos">{lt_w}</b></div>
    <div class="ltp"><span>🛑 خاسرة مغلقة:</span><b class="neg">{lt_l}</b></div>
    <div class="ltp"><span>🏆 نسبة النجاح:</span><b style="color:#fde047">{lt_wr:.1f}%</b></div>
    <div class="ltp"><span>💰 صافي محقق:</span><b class="{'pos' if lt_net>=0 else 'neg'}" style="direction:ltr">{lt_net:+.2f}R</b></div>
    <div class="ltp" style="border-style:dashed"><span>⏳ مفتوحة الآن:</span><b><span class="pos">{c_open_win} رابحة</span> / <span class="neg">{c_open_loss} خاسرة</span></b></div>
  </div>
</div>'''

    sections = ""
    for title, arr, idd, desc in (
        ("✅ لمسة فورية — المنطقة على بُعد ≤ 0.5 ATR", now_ok, "now", "أعلى احتمال تنفيذ (~80% خلال 24 ساعة حسب القياس)"),
        ("🟡 قريبة — 0.5 إلى 0.65 ATR", near, "near", "احتمال تنفيذ جيد (~65%)"),
        ("🟠 أبعد قليلاً — 0.65 إلى 1.0 ATR", far, "far", "تُراقب فقط؛ لا تُلاحق إن ابتعدت أكثر"),
    ):
        sections += f'<h2 id="{idd}">{title} — {len(arr)}</h2><div class="sub" style="margin-bottom:8px">{desc}</div>'
        if arr:
            sections += "".join(card(t, i, with_id=False) for i, t in enumerate(arr))
        else:
            sections += '<div class="note" style="background:#0d1622;border-color:#1e2c42">لا توجد صفقات ضمن هذه الفئة حالياً.</div>'

    sched_slots = {
        3: "نافذة 03:05 — إغلاق يومي + 4س + فاندنغ + وضع اصطياد ذيل آسيا",
        11: "نافذة 11:05 — إغلاق 4س + فاندنغ + لندن",
        15: "نافذة 15:05 — إغلاق 4س قبل الجلسة الأمريكية",
        19: "نافذة 19:05 — أفضل نافذة: إغلاق 4س + نيويورك + فاندنغ",
        23: "نافذة 23:05 — إغلاق 4س + رصد قائمة قابلة للانفجار",
    }
    confirm_ts = state.get("confirm_ts", 0)
    is_gh_sched = os.environ.get("GITHUB_EVENT_NAME") == "schedule"
    if confirm_ts and confirm_ts > meta.get("ts", 0):
        confirm_hm = dt.datetime.fromtimestamp(confirm_ts / 1000, RIYADH).strftime("%H:%M")
        win_note = f'✅ فحص التأكيد الرسمي ({confirm_hm} — تثبيت قائمة قابلة للانفجار قبل الإغلاق اليومي)'
    elif (_cur_dt.hour in sched_slots and 0 <= _cur_dt.minute <= 35) or (is_gh_sched and _cur_dt.hour in sched_slots):
        win_note = f'✅ تنفيذ ضمن الموعد المتفق عليه ({sched_slots[_cur_dt.hour]})'
    else:
        dead_warn = " · ⚠️ تنبيه: ساعة سيولة ضعيفة" if _cur_dt.hour in (1, 2, 7, 13, 14, 22) else ""
        win_note = f'تنفيذ خارج المواعيد المتفق عليها (02:45 تأكيدي · 03:05 · 11:05 · 15:05 · 19:05 · 23:05) بطلب صريح من المستخدم{dead_warn}'

    # ------- صفوة الدورة المتوازنة (منع التكدس ومخاطرة الارتباط العالي بالبيتكوين)
    BIG_MAJORS = {"BTC", "ETH", "SOL", "BNB"}
    ordered_pool = sorted(trades, key=lambda x: (0 if x["reach"] in ("A", "B") else 1, -x["score"], x["dist_atr"]))
    div_picks = []
    cnt_side = {"LONG": 0, "SHORT": 0}
    used_major = False
    for cand_t in ordered_pool:
        if len(div_picks) >= 4:
            break
        is_maj = cand_t["name"] in BIG_MAJORS
        if is_maj and used_major:
            continue
        if cnt_side[cand_t["side"]] >= 2:
            continue
        div_picks.append(cand_t)
        cnt_side[cand_t["side"]] += 1
        if is_maj:
            used_major = True

    if div_picks:
        dp_cards = "".join(
            f'<a href="#t-{p["name"]}" style="text-decoration:none;background:#0a1424;border:1px solid {"#1c5c39" if p["side"]=="LONG" else "#5c2029"};border-radius:11px;padding:8px 12px;display:flex;flex-direction:column;gap:3px;min-width:175px;flex:1">'
            f'<div style="display:flex;justify-content:space-between;align-items:center">'
            f'<b style="color:#fff;font-size:14px">{p["name"]}</b>'
            f'<span class="pill {"long" if p["side"]=="LONG" else "short"}">{p["side"]}</span></div>'
            f'<div style="font-size:11.5px;color:#9db1c8">الدرجة <b style="color:#fde047">{p["score"]:.1f} ({p["grade"]})</b> · وصول <b>{p["reach"]}</b> ({p["dist_atr"]:.2f} ATR)</div>'
            f'<div style="font-size:11px;color:#93c5fd;direction:ltr;text-align:left">{fp(p["entry_lo"], p["tick"])} – {fp(p["entry_hi"], p["tick"])}</div>'
            f'</a>'
            for p in div_picks
        )
        diversified_picks_html = f'''
<div class="okbox" style="background:linear-gradient(135deg,#0b1929,#0a1520);border-color:#2563eb;margin:12px 0 16px">
  <div style="font-size:13.5px;font-weight:800;color:#93c5fd;margin-bottom:4px">🛡️ صفوة الدورة المتوازنة (تشكيلة مضادة للتكدس والارتباط — بحد أقصى 4 مراكز)</div>
  <div style="font-size:12px;color:#9db1c8;margin-bottom:10px">لتفادي فتح عدة صفقات متطابقة تتحرك معاً كصفقة واحدة مع البيتكوين، اختار المحرك تلقائياً أعلى الفرص القريبة مع <b>منع تكرار الكبار (BTC/ETH/SOL/BNB مركز واحد فقط)</b> و<b>موازنة الاتجاه (بحد أقصى 2 شراء + 2 بيع)</b>:</div>
  <div style="display:flex;flex-wrap:wrap;gap:9px">{dp_cards}</div>
</div>'''
    else:
        diversified_picks_html = ""

    report_idx_json = json.dumps({
        "trades": [{"name": t["name"], "side": t["side"], "grade": t["grade"], "score": float(t["score"])} for t in trades],
        "exp": [{"name": e["name"], "score": float(e.get("score", 0))} for e in exp_active],
        "inv": [{"name": m["name"], "badge": m["badge"], "score": float(m["score"])} for m in inv_squeeze],
        "bos": [{"name": b["name"], "vol_x": float(b["vol_x"]), "score": float(b["score"])} for b in bos_active],
        "track": [{"name": x["name"], "side": x["side"], "status": x.get("status", "-"), "r_now": x.get("r_now")} for x in tracked],
    }, ensure_ascii=False)

    html_doc = f'''<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#080c12">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="ماسح بايننس">
<link rel="manifest" href="manifest.json">
<link rel="icon" href="icon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="icon.svg">
<title>ماسح بايننس — {ts}</title>
<style>{css}</style></head><body><div class="wrap" id="top">

<div class="appbar">
  <div style="font-size:13px;font-weight:700;color:#9ecbff">📱 تطبيق ماسح بايننس الآجل (v3.4)</div>
  <div class="appbtns">
    <button class="abtn pri" onclick="triggerCloud('scan')">🔄 ابدأ المسح الآن</button>
    <button class="abtn conf" onclick="triggerCloud('confirm')">✅ فحص تأكيد 02:45</button>
    <button class="abtn" onclick="refreshNow()">↻ تحديث الصفحة</button>
    <button class="abtn" onclick="openCfg()">⚙️ إعداد الضغطة الواحدة</button>
  </div>
</div>
<div id="toast" class="status-toast"></div>
{lifetime_bar_html}

<div class="hero">
  <span class="stamp">🕒 {ts} — توقيت الرياض (UTC+3)</span>
  <h1>مسح عقود بايننس الآجلة — نسخة مناطق الدخول المُراجَعة (v3)</h1>
  <span class="sub">{win_note} ·
  <b>بيانات المسح: {scan_hm}</b> · آخر تحديث للمراكز: {track_hm} · المصدر: Binance Futures API</span>
  <div class="kpis">
    <div class="kpi"><span>صفقات مؤهلة</span><b>{len(trades)}</b></div>
    <div class="kpi"><span>شراء / بيع</span><b>{len(longs)} / {len(shorts)}</b></div>
    <div class="kpi"><span>🔥 قابلة للانفجار</span><b style="color:#fbbf24">{len(exp_active)}</b></div>
    <div class="kpi"><span>💎 استثمارية / كسر هيكل</span><b style="color:#d8b4fe">{len(inv_squeeze)} / {len(bos_active)}</b></div>
    <div class="kpi"><span>درجة A</span><b>{len(gradeA)}</b></div>
    <div class="kpi"><span>لمسة فورية (≤0.5 ATR)</span><b>{len(now_ok)}</b></div>
    <div class="kpi"><span>وسيط المسافة عن السعر</span><b>{med_d:.2f} ATR</b></div>
    <div class="kpi"><span>عقود مفحوصة</span><b>{universe} من 522</b></div>
  </div>
</div>

<div class="nav">
  <a href="#tools" style="background:#172b4d;color:#93c5fd;border-color:#2f5a9e">🔍 بحث / فحص عملة</a>
  <a href="#all">📋 كل الصفقات <span class="cnt">{len(trades)}</span></a>
  <a class="longb" href="#longs">🟢 صفقات الشراء <span class="cnt">{len(longs)}</span></a>
  <a class="shortb" href="#shorts">🔴 صفقات البيع <span class="cnt">{len(shorts)}</span></a>
  <a class="expb" href="#explode">🔥 قابلة للانفجار <span class="cnt">{len(exp_active)}</span></a>
  <a class="invb" href="#macro">💎 استثمارية وكسر هيكل <span class="cnt">{n_macro}</span></a>
  <a href="#now">✅ لمسة فورية <span class="cnt">{len(now_ok)}</span></a>
  <a href="#near">🟡 قريبة <span class="cnt">{len(near)}</span></a>
  <a href="#far">🟠 أبعد <span class="cnt">{len(far)}</span></a>
  <a href="#track">🔄 تحديث السابق <span class="cnt">{n_tr}</span></a>
  <a href="#rules">📌 القواعد</a>
</div>

<div id="tools" class="tools-grid" style="scroll-margin-top:75px">
  <div class="tbox">
    <h3>🔍 البحث الفوري داخل التقرير الحالي</h3>
    <div class="tsub">اكتب رمز العملة لفلترة الجداول والبطاقات ومعرفة وضعها في الصفقات المؤهلة والانفجار والمتابعة فوراً:</div>
    <div class="tinp-row">
      <input id="coinSearchInp" class="tinp" placeholder="اكتب رمز العملة (مثل BTC أو SOL أو ZEC)..." oninput="onSearchCoin()">
      <button id="clrSearchBtn" class="abtn" style="display:none;flex:0 0 auto" onclick="clearSearchCoin()">✖ مسح</button>
    </div>
    <div id="searchSummary" class="sres"></div>
  </div>

  <div class="tbox" style="border-color:#2c4c7e">
    <h3>🎯 فحص وتحليل عملة محددة حياً (خلال ثانية)</h3>
    <div class="tsub">اكتب أي عملة في عقود بايننس الآجلة (حتى لو لم تكن بالتقرير) لفحصها حياً بمعادلات v3.4 وكشف الدعوم والمقاومات وسبب قبولها أو استبعادها:</div>
    <div class="tinp-row">
      <input id="customCoinInp" class="tinp" placeholder="مثال: DOGE أو PEPE أو ARB أو XRP..." onkeydown="if(event.key==='Enter')analyzeCustomCoin()">
      <button class="abtn pri" style="flex:0 0 auto" onclick="analyzeCustomCoin()">🎯 حلّل الآن</button>
    </div>
  </div>
</div>
<div id="liveCoinResult" style="display:none;margin:10px 0 18px"></div>

{diversified_picks_html}

<h2 id="all">📋 كل الصفقات المؤهلة — {len(trades)}</h2>
<div class="sub" style="margin-bottom:8px">مرتبة بالأولوية: الدرجة ثم قرب منطقة الدخول · اضغط على رمز العملة للانتقال إلى بطاقتها التفصيلية · الدرجة A = ≥103 · B = 99–103 · C = 95–99</div>
<div class="twrap"><table>
<thead><tr><th class="c">#</th><th>العملة</th><th class="c">الاتجاه</th><th>منطقة الدخول</th><th>الوقف</th><th>هدف 1</th><th>هدف 2</th><th class="c">الدرجة</th><th class="c">الدرجة/الوصول</th><th class="c">سيولة</th><th>الدعوم / المقاومات</th><th class="c">البنية</th></tr></thead>
<tbody>{table_all}</tbody></table></div>

{side_sections}

{exp_section}

{macro_section}

{sections}

<h2 id="track">🔄 تحديث جميع صفقات المسح السابق ({prev_label}) — {n_tr} صفقة</h2>
<div class="sub" style="margin-bottom:8px">حالة جميع صفقات المسح السابق: المفتوحة (رابحة/خاسرة) · المغلقة (هدف/وقف — الصفقة التي تضرب الوقف تُعرض مرة واحدة فقط ثم تُزال في التقرير التالي) · بانتظار التفعيل · والملغاة (&gt; 1.0 ATR){f' · <b>أُزيلت تلقائياً {state.get("pruned_stops")} صفقة سبق عرض ضربها للوقف</b>' if state.get("pruned_stops", 0) else ''}</div>
<div class="kpis" style="margin-bottom:10px">
  <div class="kpi"><span>إجمالي صفقات المسح السابق</span><b>{n_tr}</b></div>
  <div class="kpi"><span>مفتوحة الآن</span><b>{c_open}</b>{flat_sub}</div>
  <div class="kpi"><span>🟢 مفتوحة رابحة</span><b class="pos">{c_open_win}</b></div>
  <div class="kpi"><span>🔴 مفتوحة خاسرة</span><b class="neg">{c_open_loss}</b></div>
  <div class="kpi"><span>🎯 وصلت هدفاً</span><b class="pos">{c_tp}</b></div>
  <div class="kpi"><span>🛑 ضربت الوقف</span><b class="neg">{c_stop}</b></div>
  <div class="kpi"><span>⏳ بانتظار التفعيل</span><b>{c_wait}</b></div>
  <div class="kpi"><span>⛔ أُلغيت (ابتعدت)</span><b class="neg">{c_cancel}</b></div>
  <div class="kpi"><span>صافي R (عائم + محقق)</span><b class="{'pos' if net_r>=0 else 'neg'}">{net_r:+.2f}R</b></div>
</div>
{open_summary_html}
<div class="twrap"><table><thead><tr><th>العملة</th><th class="c">الاتجاه</th><th>منطقة الدخول</th><th>الوقف</th><th>السعر الآن</th><th class="c">الربح / الخسارة · البُعد</th><th class="c">الحالة</th></tr></thead>
<tbody>{track_rows}</tbody></table></div>

<h2 id="rules">📌 القواعد المطبقة في هذا التقرير</h2>
<div class="grid2">
<div class="note" style="background:#0d1622;border-color:#1e2c42">
<b>الفلترة ومنطقة الدخول ومواعيد المسح</b>
<ul>
<li><b>المواعيد الرسمية (الرياض):</b> <b>02:45</b> (تأكيدي لقائمة الانفجار) · <b>03:05</b> · <b>11:05</b> · <b>15:05</b> · <b>19:05</b> (الأفضل) · <b>23:05</b> (مع الرصد المبكر للانفجار).</li>
<li><b>منطقة الدخول = أقرب حزمة صالحة</b> (2+ مصادر منها مصدر قوي)، سقف بُعد 1.0 ATR وعرض ≤ 0.35 ATR.</li>
<li><b>مرتكزات عملات الترند الصحي قبل الانفجار (⚡ ترند، 6%–22%):</b> انتقاء <b>الصفقات القوية فقط (درجة A/B ≥ 99)</b> من مرتكزات إعادة الاختبار السريعة (EMA9·4س + EMA20/50·1س + تأرجح 1س) دون تقييد التقرير بالترند ودون مطاردة بعد الانفجار (&gt; 22%)، مع منع الدخول عكس ترند قوي (Trend is your friend).</li>
<li><b>وضع اصطياد ذيل آسيا (02:45 و03:05):</b> مسافة دنيا ≥ 0.22 ATR عن الافتتاح اليومي لالتقاط الذيل الآسيوي مع اعتماد قمة/قاع اليوم المغلق.</li>
<li>عقود USDT دائمة فقط · سيولة 24س ≥ 8M$ · عمر ≥ 30 يوماً · استبعاد العملات المستقرة والرموز غير اللاتينية → <b>{universe} عقداً</b>.</li>
<li>R:R أول ≥ 1.8 · ثانٍ ≥ 2.6 · فرق mark/last ≤ 0.5%.</li>
</ul>
</div>
<div class="note" style="background:#0d1622;border-color:#1e2c42">
<b>المخاطرة والإدارة وقاعدة الانفجار اليومي</b>
<ul>
<li>1% لكل صفقة · 3% كلية · 3–4 مراكز مفتوحة كحد أقصى · BTC/ETH/SOL مركز واحد.</li>
<li>رافعة 3–5x للكبار · 2x لما ATR(4س) &gt; 5%.</li>
<li><b>قاعدة الانفجار اليومي:</b> رصد في <b>23:05</b> (مراقبة فقط) ← تأكيد في <b>02:45</b> ← تعليق Limit لصيد ذيل آسيا (لا شراء سوقي عند 03:00).</li>
<li>50% عند هدف 1 ← التعادل ← 25% عند هدف 2 ← الباقي لهدف 3 · لا نقل للوقف نحو الخسارة.</li>
<li>لا مطاردة: إذا ابتعد السعر &gt; 1.0 ATR عن المنطقة قبل التفعيل تُلغى.</li>
<li><b>تنظيف الصفقات المنتهية:</b> الصفقات التي تضرب الوقف أو تُلغى لابتعاد السعر (&gt; 1.0 ATR) تُعرض <b>مرة واحدة فقط</b> في أول تقرير أو مسح لتحديث وضعها ثم تُزال تلقائياً في التقرير التالي، بينما تبقى المراكز المفتوحة (رابحة وخاسرة عائمة) تحت المتابعة الحية.</li>
</ul>
</div>
</div>

<div class="note" style="background:#0d1622;border-color:#1e2c42;margin-top:14px">
<b>قراءة السوق لحظة التنفيذ:</b> BTC {fp(float(t24["BTCUSDT"]["lastPrice"]) if "BTCUSDT" in t24 else 0)} ({btc["chg"]:+.2f}%) ·
ETH {fp(float(t24["ETHUSDT"]["lastPrice"]) if "ETHUSDT" in t24 else 0)} ({eth["chg"]:+.2f}%) ·
SOL {fp(float(t24["SOLUSDT"]["lastPrice"]) if "SOLUSDT" in t24 else 0)} ({sol["chg"]:+.2f}%) ·
فاندنغ قريب من الصفر (لا انحياز تمويلي حاد).
من {universe} عقداً سائلاً: <b>{n_up} صاعدة</b> مقابل <b>{n_dn} هابطة</b> على مدى 24 ساعة — لذلك صفقات البيع ({len(shorts)}) أكثر من الشراء ({len(longs)}).
أقوى صفقات الشراء المتاحة الآن: {top_longs}.
</div>

<div class="sub" style="margin-top:22px;text-align:center">
تقرير أُعيد توليده آلياً بواسطة محرك v3 · المصدر: Binance Futures API · {ts} بتوقيت الرياض ·
هذا تحليل آلي وليس نصيحة استثمارية — الالتزام بحدود المخاطرة أهم من أي صفقة.
</div>
<div id="cfgModal" class="modal-bg" onclick="if(event.target===this)closeCfg()">
  <div class="modal">
    <h3 style="margin-top:0;color:#9ecbff">⚙️ إعداد التشغيل بضغطة واحدة (اختياري)</h3>
    <div style="font-size:12.5px;color:#b9c9dc;margin-bottom:10px">
      المسح المجدول في المواعيد الستة يعمل تلقائياً <b>بدون أي إعداد</b>.<br>
      إذا أردت تشغيل المسح بضغطة زر من داخل هذه الشاشة دون فتح صفحة GitHub، أدخل اسم المستودع ومفتاح الوصول مرة واحدة (يُحفظ في جوالك فقط):
    </div>
    <label style="font-size:12px;color:#8798ab">اسم حسابك واسم المستودع (مثال: ahmad/binance-scan)</label>
    <input id="ghRepo" placeholder="username/repo-name">
    <label style="font-size:12px;color:#8798ab">مفتاح GitHub الشخصي (اختياري — يبدأ بـ github_pat_ أو ghp_)</label>
    <input id="ghTok" type="password" placeholder="github_pat_...">
    <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:6px">
      <button class="abtn" onclick="closeCfg()">إلغاء</button>
      <button class="abtn pri" onclick="saveCfg()">💾 حفظ في هذا الجهاز</button>
    </div>
  </div>
</div>

<script>
window.REPORT_INDEX = {report_idx_json};
{SEARCH_ANALYZER_JS}
if ('serviceWorker' in navigator && location.protocol.startsWith('http')) {{
  navigator.serviceWorker.register('./sw.js').catch(function(){{}});
}}
function detectRepo() {{
  var saved = localStorage.getItem('bs_gh_repo');
  if (saved) return saved.trim();
  if (location.hostname.endsWith('.github.io')) {{
    var owner = location.hostname.replace('.github.io', '');
    var parts = location.pathname.split('/').filter(Boolean);
    if (parts.length > 0) return owner + '/' + parts[0];
  }}
  return '';
}}
function openCfg() {{
  document.getElementById('ghRepo').value = detectRepo();
  document.getElementById('ghTok').value = localStorage.getItem('bs_gh_tok') || '';
  document.getElementById('cfgModal').classList.add('open');
}}
function closeCfg() {{ document.getElementById('cfgModal').classList.remove('open'); }}
function saveCfg() {{
  localStorage.setItem('bs_gh_repo', document.getElementById('ghRepo').value.trim());
  localStorage.setItem('bs_gh_tok', document.getElementById('ghTok').value.trim());
  closeCfg();
  showToast('✅ تم حفظ الإعداد في جهازك بنجاح.');
}}
function showToast(msg) {{
  var el = document.getElementById('toast');
  el.innerHTML = msg;
  el.style.display = 'block';
}}
function refreshNow() {{
  location.href = location.pathname + '?t=' + Date.now();
}}
function triggerCloud(mode) {{
  var repo = detectRepo();
  var tok = (localStorage.getItem('bs_gh_tok') || '').trim();
  if (!repo) {{
    openCfg();
    return;
  }}
  if (!tok) {{
    window.open('https://github.com/' + repo + '/actions/workflows/scanner.yml', '_blank');
    return;
  }}
  var label = (mode === 'confirm') ? 'فحص تأكيد 02:45' : 'المسح الشامل';
  showToast('⏳ جاري إرسال طلب ' + label + ' إلى السحابة...');
  fetch('https://api.github.com/repos/' + repo + '/actions/workflows/scanner.yml/dispatches', {{
    method: 'POST',
    headers: {{
      'Accept': 'application/vnd.github+json',
      'Authorization': 'Bearer ' + tok,
      'Content-Type': 'application/json'
    }},
    body: JSON.stringify({{ ref: 'main', inputs: {{ mode: mode }} }})
  }}).then(function(r) {{
    if (r.status === 204 || r.ok) {{
      var sec = 65;
      var iv = setInterval(function() {{
        sec--;
        if (sec <= 0) {{
          clearInterval(iv);
          refreshNow();
        }} else {{
          showToast('🚀 بدأ ' + label + ' في السحابة! سيُحدَّث التقرير تلقائياً خلال ' + sec + ' ثانية...');
        }}
      }}, 1000);
    }} else {{
      showToast('⚠️ تعذر التشغيل المباشر (تأكد من صلاحية المفتاح Actions: Read & Write) — سيتم فتح صفحة التشغيل اليدوي.');
      setTimeout(function(){{ window.open('https://github.com/' + repo + '/actions/workflows/scanner.yml', '_blank'); }}, 1500);
    }}
  }}).catch(function() {{
    window.open('https://github.com/' + repo + '/actions/workflows/scanner.yml', '_blank');
  }});
}}
</script>
<a class="top" href="#top" title="العودة للأعلى">↑</a>
</div></body></html>'''
    return html_doc, ts


if __name__ == "__main__":
    trades, meta, state, stats, t24, prem, tracked, held, exp_data = load()
    now = dt.datetime.now(RIYADH)
    doc, ts = build_html(trades, meta, state, stats, t24, prem, tracked, held, now, exp_data=exp_data)
    is_confirm_run = state.get("confirm_ts", 0) > meta.get("ts", 0)
    try:
        eff_ts = state["confirm_ts"] if is_confirm_run else meta.get("ts", now.timestamp() * 1000)
        _stamp = dt.datetime.fromtimestamp(eff_ts / 1000, RIYADH)
    except Exception:
        _stamp = now
    open(OUT_FILE, "w", encoding="utf-8").write(doc)
    if not is_confirm_run:
        try:
            hist = os.path.join(BASE, "history")
            os.makedirs(hist, exist_ok=True)
            hf = os.path.join(hist, f"scan_{_stamp.strftime('%Y-%m-%d_%H%M')}.json")
            if not os.path.exists(hf):
                json.dump(trades, open(hf, "w"), ensure_ascii=False, default=str)
            # الإبقاء على آخر 10 ملفات سجل فقط ليبقى المستودع خفيفاً دائماً
            hfiles = sorted(f for f in os.listdir(hist) if f.endswith(".json"))
            for old_h in hfiles[:-10]:
                os.remove(os.path.join(hist, old_h))
        except Exception as e:
            print("history save failed", e)
    print(OUT_FILE, len(doc))
