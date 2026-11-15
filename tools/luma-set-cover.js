// Replace the cover image of Luma events, including past ones (the UI hides the option once an
// event is over, but the API still accepts it).
//
// Usage:
//   1. Open https://luma.com while signed in as a calendar manager, open DevTools > Console,
//      paste this whole file, press Enter.
//   2. A panel appears top-right. Click the folder picker and choose the project's data/ folder.
//      Each data/<n>/img-open.jpg is matched to its event by folder name using EVENTS below.
//   3. Tick the events to update (none are ticked by default), then click "Upload". Each event's
//      result is logged in the panel.
//
// Same steps the Luma editor makes (from the recorded HAR):
//   POST api.luma.com/cdn/create-presigned-url {content_type}  -> {upload_url}
//   PUT  <upload_url> (raw file bytes)                          -> images.lumacdn.com/uploads/…
//   POST media.lu.ma/media/images/extract-palette {image_url}  -> {colors: [tint, …]}
//   POST api.luma.com/event/admin/update {event_api_id, cover_url, tint_color}

(() => {
  // event folder name (data/<n>) -> Luma event id
  const EVENTS = {
    "2": "evt-RSiSPHQ24SjNOvR",    // n4pemchi  2025-12-16  Hacknight #2 Zaid Khraibut
    "3": "evt-3uH2d7FQbOtogUF",    // m2qinnhr  2026-01-15  Hacknight #3 Maxime Cuillerier
    "4": "evt-dU3dCMAqGc9tvb8",    // ehcnklzv  2026-02-12  Hacknight #4 (online)
    "5": "evt-Rpfc2LfWX7ot566",    // rb21xw1v  2026-03-19  Hacknight #5 Demystifying AI
    "6": "evt-JxWFhDKUmtbOLAa",    // vbn4hdzb  2026-04-09  #6 Faiz Abhuani
    "7": "evt-V5pJ9YXp8m4KhqU",    // 52wyh8gy  2026-05-07  #7 Kim Donaldson
    "8": "evt-5zCmVXgZ5zFz6Kg",    // xc7prb8i  2026-06-04  #8 Smoothop
    "9": "evt-gt9HekFGJlg3fhQ",    // 326hnwje  2026-07-07  #9 Dorothy Eng (data/9/img-open.jpg is the premade image)
    "10":"evt-4ijZ7rAF62zfMAo",    // iryzwqdi  2026-08-06  #10 Workshop
    "10.5": "evt-JkJOL9rocgfO4py", // r1ciypx8  2026-08-19  #10.5 Workshop Part 2
    "11": "evt-LZVXBN2K6hwXafJ",   // c48u14bs  2026-09-10  #11 Residential Data
    "12": "evt-eBBZD39cPeXvbLD",   // kq6ornmo  2026-09-24  #12 September Build Night
    "13": "evt-0vjhVjnohivStMU",   // ql5pbdgm  2026-10-08  #13 AT Protocol
    "14": "evt-fXPoC8w4QcC6qxM",   // e89xnxqm  2026-10-22  #14 October Build Night
    "15": "evt-Fa72HSE28kudAfe",   // 3s21h9py  2026-11-12  #15 Mimi
    "16": "evt-rh5F3xJyazkoPAp",   // 3gxss3g5  2026-11-26  #16 November Build Night
    "17": "evt-n71Kb74j3fyXfAb",   // 908s4dkr  2026-12-10  #17 (speaker TBA)
    "18": "evt-cOIwFPCBLDfyRvD",   // wsl322rz  2027-01-14  #18 (speaker TBA)
    "19": "evt-syLgqCfFbAG1YzY",   // 6uqt1r2k  2027-01-28  #19 January Build Night
  };

  const POSTER = "img-open.jpg"; // which layout to use as the Luma cover
  const API = "https://api.luma.com";
  const HEADERS = { "Content-Type": "application/json", "x-luma-client-type": "luma-web" };

  async function api(path, opts = {}) {
    const res = await fetch(API + path, { credentials: "include", headers: HEADERS, ...opts });
    const text = await res.text();
    if (!res.ok) throw new Error(`${opts.method || "GET"} ${path} -> ${res.status}: ${text.slice(0, 300)}`);
    return text ? JSON.parse(text) : {};
  }

  async function uploadImage(file) {
    const { upload_url } = await api("/cdn/create-presigned-url", {
      method: "POST",
      body: JSON.stringify({ content_type: file.type }),
    });
    const put = await fetch(upload_url, { method: "PUT", headers: { "Content-Type": file.type }, body: file });
    if (!put.ok) throw new Error(`S3 upload -> ${put.status}: ${(await put.text()).slice(0, 300)}`);
    const u = new URL(upload_url);
    return "https://images.lumacdn.com" + u.pathname.replace(/^\/images\.lumacdn\.com/, "");
  }

  async function tintFor(imageUrl) {
    try {
      const res = await fetch("https://media.lu.ma/media/images/extract-palette", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image_url: imageUrl, quality: "fast" }),
      });
      return (await res.json()).colors?.[0];
    } catch {
      return undefined; // tint is cosmetic; update without it
    }
  }

  async function setCover(eventId, file) {
    const before = (await api(`/event/admin/get?event_api_id=${eventId}`)).event;
    const cover_url = await uploadImage(file);
    const tint_color = await tintFor(cover_url);
    const body = { event_api_id: eventId, cover_url, ...(tint_color && { tint_color }) };
    const { event } = await api("/event/admin/update", { method: "POST", body: JSON.stringify(body) });
    if (event?.cover_url !== cover_url) throw new Error("update returned a different cover_url");
    return { name: event.name, url: `https://luma.com/${event.url}`, old: before.cover_url, new: cover_url };
  }

  // ---- panel -------------------------------------------------------------------------------
  document.getElementById("ctmtl-cover")?.remove();
  const panel = document.createElement("div");
  panel.id = "ctmtl-cover";
  panel.style.cssText =
    "position:fixed;top:16px;right:16px;z-index:2147483647;width:440px;max-height:80vh;overflow:auto;" +
    "background:#fff;color:#111;font:13px/1.45 system-ui,sans-serif;border:1px solid #ccc;" +
    "border-radius:10px;box-shadow:0 8px 30px rgba(0,0,0,.25);padding:14px";
  panel.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
      <b>Replace Luma cover images</b>
      <button data-close style="border:0;background:none;font-size:18px;cursor:pointer">×</button>
    </div>
    <input type="file" webkitdirectory data-files>
    <ul data-list style="padding-left:18px;margin:10px 0"></ul>
    <button data-go disabled style="padding:6px 14px;cursor:pointer">Upload</button>
    <pre data-log style="white-space:pre-wrap;margin:10px 0 0;font-size:12px"></pre>`;
  document.body.append(panel);

  const $ = (sel) => panel.querySelector(sel);
  const log = (msg) => { $("[data-log]").textContent += msg + "\n"; console.log(msg); };
  let jobs = [];

  $("[data-close]").onclick = () => panel.remove();
  $("[data-files]").onchange = (e) => {
    // webkitRelativePath looks like "data/100/img-open.jpg"; the event key is the folder name.
    jobs = [...e.target.files]
      .map((file) => ({ file, parts: file.webkitRelativePath.split("/") }))
      .filter(({ parts }) => parts.length >= 2 && parts.at(-1) === POSTER)
      .map(({ file, parts }) => ({ file, key: parts.at(-2), id: EVENTS[parts.at(-2)] }))
      .sort((a, b) => parseFloat(a.key) - parseFloat(b.key));
    $("[data-list]").innerHTML = jobs.length
      ? jobs.map((j, i) => `<li><label><input type="checkbox" data-pick="${i}" ${j.id ? "" : "disabled"}> ` +
          `${j.key}/${POSTER} → ${j.id ?? '<span style="color:#b00">no matching event</span>'}</label></li>`).join("")
      : `<li style="color:#b00">No */${POSTER} files found in that folder.</li>`;
    panel.querySelectorAll("[data-pick]").forEach((c) => (c.onchange = () => ($("[data-go]").disabled = !picked().length)));
    $("[data-go]").disabled = true;
  };
  const picked = () => [...panel.querySelectorAll("[data-pick]:checked")].map((c) => jobs[+c.dataset.pick]);
  $("[data-go]").onclick = async () => {
    $("[data-go]").disabled = true;
    for (const { file, key, id } of picked()) {
      try {
        const r = await setCover(id, file);
        log(`✓ ${key}: ${r.name}\n  ${r.url}\n  old: ${r.old}\n  new: ${r.new}`);
      } catch (err) {
        log(`✗ ${key} (${id}): ${err.message}`);
      }
    }
    log("Done.");
  };

  window.ctmtlSetCover = setCover; // also callable directly: await ctmtlSetCover("evt-…", file)
})();
