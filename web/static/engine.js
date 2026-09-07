/* GitHub Pages / 정적 호스팅용 FAQ 엔진. 글자 겹침 검색만 사용. */
(function (global) {
  const REFUSE_MESSAGE =
    "자료에 없는 내용입니다. 개별 건은 추측하지 않습니다. " +
    "재무인프라팀 송민규 과장(010-5110-1784)에게 문의해 주세요.";
  const DISCLAIMER =
    "이 안내는 일반 절차입니다. 개별 건의 적격·금액·예외는 담당 확인이 필요합니다.";
  const CLARIFY_MESSAGE =
    "가까운 안내가 여러 건입니다. 해당하는 항목을 골라 주세요.";
  const FOLLOW_HINT =
    /(그\s*(양식|화면|절차|건|거|것|안내)|그거|이어서|그럼|그러면|위에|방금|앞에서)/;
  const SEARCH_K = 8;
  const QUICK_REFUSE = 0.45;
  const REFUSE_BELOW = 0.58;
  const AMBIGUOUS_GAP = 0.08;
  const CONFIDENT = 0.78;
  const KW_SURE = 0.78;
  const KW_GAP = 0.12;
  const KW_MIN = 0.55;
  const KW_MIN_HITS = 4;

  let ROWS = [];
  let BY_QID = Object.create(null);
  let READY = null;

  // 질문마다 흔히 겹치는 글자쌍은 매칭 점수에서 제외
  const STOP_BI = new Set([
    "하나", "나요", "니까", "어떻", "게하", "해야", "무엇", "인가",
    "합니", "입니", "있는", "없는", "경우", "관련", "대한", "에서",
    "으로", "또는", "그리", "언제", "누가", "어떤", "되나", "됩니",
    "습니", "까요", "을까", "인가", "는지", "는데",
  ]);

  function bigrams(text) {
    const clean = String(text || "")
      .toLowerCase()
      .replace(/[^0-9a-z가-힣]/g, "");
    if (clean.length < 2) return clean ? new Set([clean]) : new Set();
    const out = new Set();
    for (let i = 0; i < clean.length - 1; i++) {
      const g = clean.slice(i, i + 2);
      if (!STOP_BI.has(g)) out.add(g);
    }
    if (!out.size && clean.length >= 2) {
      for (let i = 0; i < clean.length - 1; i++) out.add(clean.slice(i, i + 2));
    }
    return out;
  }

  function ensureBi(row) {
    if (row._bi instanceof Set) return row._bi;
    row._bi = Array.isArray(row.bi) ? new Set(row.bi.filter((g) => !STOP_BI.has(g))) : bigrams(row.q);
    if (!row._bi.size) row._bi = Array.isArray(row.bi) ? new Set(row.bi) : bigrams(row.q);
    return row._bi;
  }

  async function load(url) {
    if (READY) return READY;
    READY = (async () => {
      const res = await fetch(url || "./data/faq.json", { cache: "no-store" });
      if (!res.ok) throw new Error("FAQ 데이터를 불러오지 못했습니다");
      const data = await res.json();
      ROWS = Array.isArray(data.rows) ? data.rows : [];
      BY_QID = Object.create(null);
      for (const row of ROWS) BY_QID[row.qid] = row;
      return ROWS.length;
    })();
    return READY;
  }

  function keywordRank(query, k) {
    const qb = bigrams(query);
    if (!qb.size) return [];
    const scored = ROWS.map((row) => {
      const bi = ensureBi(row);
      let hit = 0;
      for (const g of qb) if (bi.has(g)) hit++;
      return [hit / qb.size, hit, row];
    });
    scored.sort((a, b) => b[0] - a[0] || b[1] - a[1]);
    return scored.slice(0, k).map(([cover, , row]) => [cover, row]);
  }

  function keywordFallback(query, k) {
    const out = [];
    const qb = bigrams(query);
    for (const [cover, row] of keywordRank(query, k)) {
      const bi = ensureBi(row);
      let hits = 0;
      for (const g of qb) if (bi.has(g)) hits++;
      if (cover < KW_MIN || hits < KW_MIN_HITS) continue;
      // 점수를 부풀리지 않는다. 겹침 비율 그대로 써서 약한 일치는 거절한다.
      out.push([cover, row]);
    }
    return out;
  }

  function packRow(row, score, ranked) {
    const candidates = (ranked || []).map(([s, r]) => ({
      qid: r.qid,
      category: r.cat || "",
      question: r.q,
      score: Math.round(s * 1000) / 1000,
    }));
    return {
      refused: false,
      score: score == null ? null : Math.round(score * 1000) / 1000,
      qid: row.qid,
      category: row.cat || "",
      question: row.q,
      answer: row.answer || "",
      forms: row.forms || [],
      captures: row.captures || [],
      similar: row.similar || [],
      rule: row.rule || "",
      law: row.law || "",
      disclaimer: DISCLAIMER,
      candidates,
      ambiguous: false,
    };
  }

  function refuseResult(score, ranked) {
    const candidates = (ranked || []).slice(0, 3).map(([s, r]) => ({
      qid: r.qid,
      category: r.cat || "",
      question: r.q,
      score: Math.round(s * 1000) / 1000,
    }));
    return {
      refused: true,
      score: score == null ? null : Math.round(score * 1000) / 1000,
      message: REFUSE_MESSAGE,
      candidates,
      disclaimer: DISCLAIMER,
    };
  }

  function decideLocally(ranked) {
    if (!ranked.length) return { action: "refuse" };
    const topS = ranked[0][0];
    const gap = ranked.length >= 2 ? topS - ranked[1][0] : 1;
    if (topS < QUICK_REFUSE) return { action: "refuse" };
    if (topS >= REFUSE_BELOW && gap >= AMBIGUOUS_GAP) {
      return { action: "top", show_others: topS < CONFIDENT };
    }
    if (topS >= REFUSE_BELOW) return { action: "pick" };
    return { action: "route" };
  }

  function lastQid(history) {
    for (let i = (history || []).length - 1; i >= 0; i--) {
      const item = history[i];
      if (!item || typeof item !== "object") continue;
      if (item.role === "user" || item.refused) continue;
      const qid = String(item.qid || "").trim();
      if (qid) return qid;
    }
    return "";
  }

  async function ask(query, history) {
    await load();
    history = (history || []).filter((h) => h && typeof h === "object").slice(-8);
    const prior = lastQid(history);
    if (prior && FOLLOW_HINT.test(query)) {
      const row = BY_QID[prior];
      if (row) return packRow(row, null, null);
    }

    const kw = keywordRank(query, SEARCH_K);
    if (kw.length && kw[0][0] >= KW_SURE) {
      const gap = kw.length >= 2 ? kw[0][0] - kw[1][0] : 1;
      if (gap >= KW_GAP) {
        const [cover, row] = kw[0];
        return packRow(row, Math.round(cover * 1000) / 1000, null);
      }
    }

    const ranked = keywordFallback(query, SEARCH_K);
    const plan = decideLocally(ranked);
    if (plan.action === "refuse" && !ranked.length) return refuseResult();
    if (plan.action === "top") {
      const [topS, top] = ranked[0];
      const result = packRow(top, topS, ranked.slice(0, 3));
      result.ambiguous = !!plan.show_others;
      return result;
    }
    if (plan.action === "refuse") return refuseResult(ranked[0][0], ranked);

    const [topS, top] = ranked[0];
    if (topS < REFUSE_BELOW) return refuseResult(topS, ranked);
    const result = packRow(top, topS, ranked.slice(0, 3));
    result.ambiguous = true;
    return result;
  }

  async function guide(qid) {
    await load();
    const row = BY_QID[qid];
    if (!row) {
      return { refused: true, message: REFUSE_MESSAGE, disclaimer: DISCLAIMER };
    }
    return packRow(row, null, null);
  }

  function adminCatalog() {
    const cats = [];
    const seen = new Set();
    let answered = 0;
    let formReady = 0;
    let capReady = 0;
    const items = ROWS.map((row) => {
      const forms = row.forms || [];
      const caps = (row.captures || []).filter((c) => c.url);
      const hasAnswer = !!(row.answer || "").trim();
      if (hasAnswer) answered += 1;
      if (forms.some((f) => f.url)) formReady += 1;
      if (caps.length) capReady += 1;
      const cat = row.cat || "";
      if (cat && !seen.has(cat)) {
        seen.add(cat);
        cats.push(cat);
      }
      return {
        qid: row.qid,
        category: cat,
        question: row.q,
        has_answer: hasAnswer,
        forms_ready: forms.filter((f) => f.url).length,
        forms_total: forms.length,
        captures: caps.length,
      };
    });
    return {
      indexed: ROWS.length,
      answered,
      form_ready: formReady,
      cap_ready: capReady,
      categories: cats,
      items,
    };
  }

  function adminItem(qid) {
    const row = BY_QID[qid];
    if (!row) return null;
    return {
      qid,
      category: row.cat || "",
      question: row.q,
      answer: row.answer || "",
      forms: row.forms || [],
      similar: row.similar || [],
      capture_notes: row.capture_notes || (row.captures || []).map((c) => c.title).filter(Boolean),
      captures: row.captures || [],
      rule: row.rule || "",
      law: row.law || "",
    };
  }

  const LOG_KEY = "tta-guide-query-logs";
  const LOG_KEEP = 500;

  function pad(n) {
    return String(n).padStart(2, "0");
  }

  function nowKst() {
    const d = new Date(Date.now() + 9 * 60 * 60 * 1000);
    return (
      d.getUTCFullYear() +
      "-" + pad(d.getUTCMonth() + 1) +
      "-" + pad(d.getUTCDate()) +
      " " + pad(d.getUTCHours()) +
      ":" + pad(d.getUTCMinutes()) +
      ":" + pad(d.getUTCSeconds())
    );
  }

  function readLogs(limit) {
    try {
      const rows = JSON.parse(localStorage.getItem(LOG_KEY) || "[]");
      if (!Array.isArray(rows)) return [];
      return rows.slice(-(limit || 200)).reverse();
    } catch (_) {
      return [];
    }
  }

  function appendLog(user, query, result, source, files) {
    const answer = (result && (result.answer || result.message)) || "";
    const entry = {
      time: nowKst(),
      user: String(user || "").trim().slice(0, 40) || "이름 없음",
      query: String(query || "").trim().slice(0, 500),
      source: source || "질문",
      refused: !!(result && result.refused),
      qid: (result && result.qid) || "",
      matched: (result && result.question) || "",
      score: result ? result.score : null,
      ambiguous: !!(result && result.ambiguous),
      answer: String(answer).slice(0, 2000),
      forms: ((result && result.forms) || [])
        .map((f) => f && f.name)
        .filter(Boolean),
      files: (files || [])
        .filter((f) => f && f.url)
        .map((f) => ({ name: f.name, url: f.url })),
    };
    let rows = [];
    try {
      rows = JSON.parse(localStorage.getItem(LOG_KEY) || "[]");
      if (!Array.isArray(rows)) rows = [];
    } catch (_) {
      rows = [];
    }
    rows.push(entry);
    if (rows.length > LOG_KEEP) rows = rows.slice(-LOG_KEEP);
    localStorage.setItem(LOG_KEY, JSON.stringify(rows));
    return entry;
  }

  global.StaticFaq = {
    load,
    ask,
    guide,
    adminCatalog,
    adminItem,
    appendLog,
    readLogs,
    CLARIFY_MESSAGE,
  };
})(typeof window !== "undefined" ? window : globalThis);
