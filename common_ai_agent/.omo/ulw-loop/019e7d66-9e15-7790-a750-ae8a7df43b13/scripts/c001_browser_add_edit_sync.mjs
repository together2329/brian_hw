import { chromium } from "playwright";
import { execFileSync } from "node:child_process";
import { chmodSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";

const required = (name) => {
  const value = process.env[name];
  if (!value) throw new Error(`${name} is required`);
  return value;
};

const baseUrl = required("ATLAS_BASE_URL");
const projectRoot = required("PROJECT_ROOT");
const ip = required("QA_IP");
const artifactJson = required("C001_ARTIFACT_JSON");
const screenshotPath = required("C001_SCREENSHOT");
const p4Port = required("P4PORT");
const p4User = required("P4USER");
const p4Client = required("P4CLIENT");
const p4Tickets = required("P4TICKETS");
const syncTarget = `${projectRoot}/${ip}/rtl/sync_target.sv`;
const expectedSyncContent = "module sync_target; initial begin $display(\"DEPOT_SYNC_TARGET\"); end endmodule\n";

mkdirSync(dirname(artifactJson), { recursive: true });
mkdirSync(dirname(screenshotPath), { recursive: true });

const actions = [];
const responses = [];
const result = {
  ok: false,
  baseUrl,
  ip,
  p4: { p4Port, p4User, p4Client },
  actions,
  responses,
  assertions: {},
  screenshotPath,
};

const log = (step, data = {}) => {
  actions.push({ step, at: new Date().toISOString(), ...data });
};

const countText = async (page, text) => page.getByText(text, { exact: true }).count();

const clickTextOccurrence = async (page, text, index) => {
  const locator = page.getByText(text, { exact: true });
  const count = await locator.count();
  if (count <= index) {
    throw new Error(`Expected occurrence ${index} for ${text}, saw ${count}`);
  }
  await locator.nth(index).click();
  log("click_text", { text, index, count });
};

const clickButton = async (page, name) => {
  const locator = page.getByRole("button", { name });
  const count = await locator.count();
  if (count < 1) throw new Error(`Button not found: ${name}`);
  await locator.first().click();
  log("click_button", { name, count });
};

const waitForPerforceTab = async (page) => {
  try {
    await page.getByText("LOCAL IP", { exact: true }).waitFor({ timeout: 5000 });
    return;
  } catch {}

  const candidates = [
    page.locator('[title^="SCM:"]'),
    page.getByRole("button", { name: /SCM|Perforce|source/i }),
    page.getByText("SCM", { exact: true }),
    page.getByText("Perforce", { exact: true }),
  ];
  for (const candidate of candidates) {
    const count = await candidate.count();
    if (count < 1) continue;
    await candidate.first().click();
    log("click_scm_tab", { count });
    break;
  }
  await page.getByText("LOCAL IP", { exact: true }).waitFor({ timeout: 20000 });
};

const p4Opened = () => {
  const env = {
    ...process.env,
    P4CONFIG: "",
    P4TICKETS: p4Tickets,
    P4PORT: p4Port,
    P4USER: p4User,
    P4CLIENT: p4Client,
  };
  return execFileSync(
    "p4",
    ["-p", p4Port, "-u", p4User, "-c", p4Client, "-d", projectRoot, "opened", `${ip}/...`],
    { env, encoding: "utf-8" },
  );
};

let browser;
try {
  browser = await chromium.launch({ headless: true });
} catch (error) {
  const chromePath = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
  if (!existsSync(chromePath)) throw error;
  browser = await chromium.launch({ headless: true, executablePath: chromePath });
}

try {
  const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
  page.on("response", (response) => {
    const url = response.url();
    if (url.includes("/api/scm/")) {
      responses.push({
        url,
        method: response.request().method(),
        status: response.status(),
      });
    }
  });

  const url = `${baseUrl}/?backend=live&ip=${encodeURIComponent(ip)}`;
  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 30000 });
  log("goto", { url });
  await page.waitForLoadState("networkidle", { timeout: 30000 }).catch(() => {});
  await waitForPerforceTab(page);
  log("perforce_tab_visible");

  await page.getByText("rtl/new_file.sv", { exact: true }).waitFor({ timeout: 20000 });
  await page.getByText("rtl/existing.sv", { exact: true }).waitFor({ timeout: 20000 });
  await page.getByText("rtl/sync_target.sv", { exact: true }).waitFor({ timeout: 20000 });
  result.assertions.initialRowsVisible = true;

  await clickTextOccurrence(page, "rtl/new_file.sv", 0);
  await Promise.all([
    page.waitForResponse((response) => response.url().includes("/api/scm/add") && response.request().method() === "POST", { timeout: 20000 }),
    clickButton(page, /Add/i),
  ]);
  await page.waitForTimeout(500);
  log("add_completed");

  await clickTextOccurrence(page, "rtl/existing.sv", 0);
  await Promise.all([
    page.waitForResponse((response) => response.url().includes("/api/scm/edit") && response.request().method() === "POST", { timeout: 20000 }),
    clickButton(page, /Edit/i),
  ]);
  await page.waitForTimeout(500);
  log("edit_completed");

  chmodSync(syncTarget, 0o644);
  writeFileSync(syncTarget, "module sync_target; initial begin $display(\"LOCAL_OVERWRITE\"); end endmodule\n", "utf-8");
  log("local_overwrite_written", { syncTarget });

  const syncTargetCount = await countText(page, "rtl/sync_target.sv");
  if (syncTargetCount < 2) {
    throw new Error(`Expected local and depot sync_target rows, saw ${syncTargetCount}`);
  }
  await clickTextOccurrence(page, "rtl/sync_target.sv", 1);
  await Promise.all([
    page.waitForResponse((response) => response.url().includes("/api/scm/sync") && response.request().method() === "POST", { timeout: 20000 }),
    clickButton(page, /Sync/i),
  ]);
  await page.waitForTimeout(500);
  log("sync_completed");

  const opened = p4Opened();
  const finalSyncContent = readFileSync(syncTarget, "utf-8");
  result.assertions.openedContainsAdd = /new_file\.sv#\d+ - add/.test(opened);
  result.assertions.openedContainsEdit = /existing\.sv#\d+ - edit/.test(opened);
  result.assertions.finalSyncContentMatchesDepot = finalSyncContent === expectedSyncContent;
  result.assertions.p4Opened = opened;
  result.assertions.finalSyncContent = finalSyncContent;
  result.ok = (
    result.assertions.initialRowsVisible
    && result.assertions.openedContainsAdd
    && result.assertions.openedContainsEdit
    && result.assertions.finalSyncContentMatchesDepot
  );

  await page.screenshot({ path: screenshotPath, fullPage: true });
  log("screenshot", { screenshotPath });
} catch (error) {
  result.error = error instanceof Error ? error.stack || error.message : String(error);
  try {
    if (browser) {
      const pages = browser.contexts().flatMap((context) => context.pages());
      if (pages[0]) await pages[0].screenshot({ path: screenshotPath, fullPage: true });
    }
  } catch {}
} finally {
  if (browser) await browser.close();
  log("browser_closed");
  writeFileSync(artifactJson, `${JSON.stringify(result, null, 2)}\n`, "utf-8");
}

if (!result.ok) {
  process.exitCode = 1;
}
