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
    // remote photo hotlinks may 404/403; only count same-origin resource errors
    if (m.type() === "error" && !m.text().includes("Failed to load resource"))
      errors.push("console: " + m.text());
  });
  await page.emulateMediaFeatures([{ name: "prefers-color-scheme", value: "light" }]);
  await page.goto("http://localhost:8741/index.html", { waitUntil: "networkidle2" });
  await new Promise((r) => setTimeout(r, 2500));

  const stats = await page.$eval("#stats", (el) => el.textContent);

  // person panel: Tyler Chen — photo, website, advisors, students?, papers
  await page.evaluate(() => {
    const g = [...document.querySelectorAll("g.node")]
      .find((el) => el.__data__ && el.__data__.id === "tyler-chen");
    g.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  });
  await new Promise((r) => setTimeout(r, 400));
  const person = await page.evaluate(() => {
    const d = document.getElementById("details");
    const heads = [...d.querySelectorAll("h3")].map((h) => h.textContent);
    return {
      name: d.querySelector("h2")?.textContent,
      hasPhoto: !!d.querySelector("img.photo"),
      website: d.querySelector("a[href^='http']")?.href,
      sections: heads,
      advisors: heads.includes("Advisors")
        ? [...d.querySelectorAll("ul.plain")][0].textContent.trim() : null,
      nPapers: d.querySelectorAll("ul.papers li").length,
      conns: d.querySelectorAll(".conn-row").length,
    };
  });
  await page.screenshot({ path: "shot2_person.png" });

  // edge panel via first connection
  await page.click("#details .conn-row");
  await new Promise((r) => setTimeout(r, 300));
  const edge = await page.evaluate(() => {
    const d = document.getElementById("details");
    return {
      names: d.querySelector("h2")?.textContent.trim().replace(/\s+/g, " "),
      hasAdvising: [...d.querySelectorAll("h3")].some((h) => h.textContent === "Advising"),
      jointPapers: d.querySelectorAll("ul.papers li").length,
      total: d.querySelector(".factor-table tfoot td.num")?.textContent,
    };
  });
  await page.screenshot({ path: "shot2_edge.png" });

  // advising view
  await page.click("#advising-toggle");
  await new Promise((r) => setTimeout(r, 800));
  const advising = await page.evaluate(() => ({
    visibleEdges: [...document.querySelectorAll("g.linkg")]
      .filter((g) => g.style.display !== "none").length,
    arrowEdges: document.querySelectorAll("line.link[marker-end]").length,
    stats: document.getElementById("stats").textContent,
  }));
  await page.screenshot({ path: "shot2_advising.png" });
  await page.click("#advising-toggle");

  console.log(JSON.stringify({ stats, person, edge, advising, errors }, null, 1));
  await browser.close();
})().catch((e) => { console.error("DRIVER FAIL:", e); process.exit(1); });
