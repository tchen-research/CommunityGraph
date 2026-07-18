const puppeteer = require("puppeteer-core");

(async () => {
  const browser = await puppeteer.launch({
    executablePath: "/usr/bin/google-chrome",
    headless: "new",
    args: ["--no-sandbox", "--disable-gpu"],
    defaultViewport: { width: 1440, height: 900 },
  });
  const page = await browser.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push("pageerror: " + e.message));
  page.on("console", (m) => {
    if (m.type() === "error") errors.push("console: " + m.text());
  });
  await page.emulateMediaFeatures([{ name: "prefers-color-scheme", value: "light" }]);
  await page.goto("http://localhost:8741/index.html", { waitUntil: "networkidle0" });
  await new Promise((r) => setTimeout(r, 2500)); // let the simulation settle

  // 1. click Tyler Chen's node via bound data
  await page.evaluate(() => {
    const g = [...document.querySelectorAll("g.node")]
      .find((el) => el.__data__ && el.__data__.id === "tyler-chen");
    g.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));
  });
  await new Promise((r) => setTimeout(r, 300));
  const personPanel = await page.evaluate(() => {
    const d = document.getElementById("details");
    return { hidden: d.hidden, h2: d.querySelector("h2")?.textContent,
             conns: d.querySelectorAll(".conn-row").length,
             text: d.textContent.slice(0, 160) };
  });
  await page.screenshot({ path: "shot_person.png" });

  // 2. click the first connection row -> edge panel
  await page.click("#details .conn-row");
  await new Promise((r) => setTimeout(r, 300));
  const edgePanel = await page.evaluate(() => {
    const d = document.getElementById("details");
    return { hidden: d.hidden,
             names: d.querySelector("h2")?.textContent.trim(),
             factorRows: d.querySelectorAll(".factor-table tbody tr").length,
             total: d.querySelector(".factor-table tfoot td.num")?.textContent };
  });
  await page.screenshot({ path: "shot_edge.png" });

  // 3. drag the coauthorship weight to 0 and check stats/edge panel react
  const before = await page.$eval("#stats", (el) => el.textContent);
  await page.$eval("#weight-sliders input", (el) => {
    el.value = 0;
    el.dispatchEvent(new Event("input", { bubbles: true }));
  });
  await new Promise((r) => setTimeout(r, 300));
  const after = await page.$eval("#stats", (el) => el.textContent);
  const edgeAfter = await page.evaluate(() =>
    document.querySelector(".factor-table tfoot td.num")?.textContent);

  // 4. search
  await page.evaluate(() => select_dummy = null).catch(() => {});
  await page.type("#search", "martinsson");
  await new Promise((r) => setTimeout(r, 200));
  const hits = await page.evaluate(() =>
    [...document.querySelectorAll(".search-hit")].map((b) => b.textContent.trim()));

  // 5. legend toggle
  await page.click("#legend .legend-row");
  const fadedCount = await page.evaluate(() =>
    document.querySelectorAll("g.node.faded").length);

  await page.screenshot({ path: "shot_light.png" });
  console.log(JSON.stringify({ personPanel, edgePanel, before, after, edgeAfter,
    hits, fadedCount, errors }, null, 1));
  await browser.close();
})().catch((e) => { console.error("DRIVER FAIL:", e); process.exit(1); });
