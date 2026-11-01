// QA: open index.html at desktop (1280) and phone (390) widths, record console errors, take screenshots to qa/.
// Run from the repo root with a static server on :8823 (python3 -m http.server 8823).
const { chromium } = require("playwright");
const path = require("path");
const OUT = path.join(__dirname, "..", "qa");
// Leaflet is served from a local npm copy (the CDN is not reachable from the build machine); tiles and fonts are skipped.
const LEAF = process.env.LEAFLET_DIST || "/tmp/claude-0/-home-claude/9791f396-0812-550b-8fd1-2ad33918f115/scratchpad/node_modules/leaflet/dist";
(async () => {
  const b = await chromium.launch();
  for (const [name, w, h] of [["desktop", 1280, 900], ["phone", 390, 844]]) {
    const p = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: name === "phone" ? 2 : 1 });
    await p.route(/arcgisonline|googleapis|gstatic/, r => r.abort());
    await p.route(/leaflet.min.js/, r => r.fulfill({ path: LEAF + "/leaflet.js" }));
    await p.route(/leaflet.min.css/, r => r.fulfill({ path: LEAF + "/leaflet.css" }));
    const errs = [];
    p.on("console", m => { if (m.type() === "error" && !/arcgisonline|net::ERR|Failed to load resource/.test(m.text())) errs.push(m.text()); });
    p.on("pageerror", e => errs.push("pageerror " + e.message));
    await p.goto("http://localhost:" + (process.env.QA_PORT || 8823) + "/index.html", { waitUntil: "networkidle", timeout: 60000 }).catch(() => {});
    await p.waitForTimeout(2500);
    await p.screenshot({ path: `${OUT}/${name}_top.png` });
    const at = async (sel, file) => { const e = await p.$(sel); if (e) { await e.scrollIntoViewIfNeeded(); await p.waitForTimeout(400); await e.screenshot({ path: `${OUT}/${name}_${file}.png` }); } };
    await at("#atlas", "map_all");
    await p.evaluate(() => setDec(1930)); await p.waitForTimeout(700); await at("#atlas", "map_1930");
    await p.click('#gRow .btn[data-g="w"]'); await p.evaluate(() => setDec(null)); await p.waitForTimeout(700); await at("#atlas", "map_women");
    await p.click('#gRow .btn[data-g="all"]');
    await p.evaluate(() => setPrizes([0, 1, 2, 3, 4, 5])); await p.waitForTimeout(700); await at("#atlas", "map_allsix");
    await p.evaluate(() => setPrizes([0, 1, 2, 3]));
    await p.fill("#q", "Hans Bethe"); await p.waitForTimeout(400); await at(".searchbox", "search");
    await p.keyboard.press("Enter"); await p.waitForTimeout(1500); await at("#atlas", "laureate");
    await p.evaluate(() => { clearSel(); map.setView([50, 10], 4); pickCountry("DEU", false); }); await p.waitForTimeout(900); await at("#atlas", "country");
    await p.evaluate(() => { LY.shade = true; LY.insts = true; applyLayers(); legend(); map.setView([40, -30], 2); }); await p.waitForTimeout(900); await at("#atlas", "shade_insts");
    await p.evaluate(() => { LY.shade = false; LY.insts = false; LY.colour = "prize"; applyLayers(); legend(); }); await p.waitForTimeout(700); await at("#atlas", "byprize");
    await p.evaluate(() => { LY.colour = "dest"; applyLayers(); legend(); });
    await p.click(".lyrBtn"); await p.waitForTimeout(300); await at("#map", "layers"); await p.click(".lyrBtn");
    // click a line in the middle of the Atlantic
    await p.evaluate(() => { clearSel(); map.setView([45, -40], 3); }); await p.waitForTimeout(900);
    const bb = await (await p.$("#map")).boundingBox();
    for (const [dx, dy] of [[0, 0], [0, 20], [0, -20], [20, 10]]) { await p.mouse.click(bb.x + bb.width / 2 + dx, bb.y + bb.height / 2 + dy); await p.waitForTimeout(300); if (await p.$(".leaflet-popup")) break; }
    await at("#atlas", "click_line");
    for (const id of ["netChart", "usShareChart", "flowChart", "deChart", "deTable", "jpChart", "uniChart", "abChart", "womenChart"]) await at("#" + id, id);
    await p.click("#theme"); await p.waitForTimeout(800); await at("#atlas", "dark"); await at("#netChart", "dark_net"); await p.click("#theme");
    await p.screenshot({ path: `${OUT}/${name}_full.png`, fullPage: true });
    const over = await p.evaluate(() => document.documentElement.scrollWidth - innerWidth);
    const fs = await p.evaluate(() => document.querySelectorAll(".mfs-btn").length);
    console.log(name, "errors:", JSON.stringify(errs), "horizontal overflow:", over, "fullscreen buttons:", fs);
    await p.close();
  }
  await b.close();
})();
