'use strict';
// Chromium qualification of the GitHub Pages artifact below the project-site
// prefix, as published at https://zackboll.github.io/opencv_features_ada/.
// Every route, reference and request must stay under the prefix. Not a
// cross-browser or complete accessibility certification. Environment:
//   PLAYWRIGHT_MODULE  path of an installed playwright package
//   PAGES_URL          http URL of the site root below a non-root prefix, ending in /
//   CHROME             optional Chromium executable
//   BROWSER_REPORT     optional JSON report path
const fs = require('fs');
const path = require('path');
const playwrightPath = process.env.PLAYWRIGHT_MODULE || 'playwright';
const { chromium } = require(playwrightPath);
const root = process.env.PAGES_URL;
if (!root || !root.endsWith('/') || new URL(root).pathname === '/') {
  throw new Error('PAGES_URL must be a site root below a non-root prefix, ending in /');
}
const { origin, pathname: prefix } = new URL(root);
const docs = path.join(__dirname, '../../docs');
const siteMap = JSON.parse(fs.readFileSync(path.join(docs, 'site-map.json')));
const anchors = JSON.parse(fs.readFileSync(path.join(docs, 'gnatdoc-native-anchors.json')));
const PACKAGES = Object.keys(anchors.packages).sort();
const ORB = `api/${anchors.packages['OpenCV.Features.ORB'].page}`;
// [route, label, expected h1]; the API index shows the first package in its frame.
const ROUTES = [['', 'portal', 'OpenCV Features for Ada'], ['api/index.html', 'API index', PACKAGES[0]],
  ...siteMap.guides.map((g) => [g.path, g.path, g.label]),
  ...PACKAGES.map((name) => [`api/${anchors.packages[name].page}`, name, name])];

const assertions = [];
function check(name, condition, detail) {
  assertions.push({ name, pass: Boolean(condition), detail: detail === undefined ? null : detail });
}
const under = (href) => { const u = new URL(href); return u.origin === origin && u.pathname.startsWith(prefix); };
const frameOf = (page) => page.frame({ name: 'document-content' });
const TITLES = new Map([['', 'OpenCV Features for Ada documentation'],
  ['api/index.html', 'API Reference — OpenCV Features Ada'],
  ...siteMap.guides.map((g) => [g.path, `${g.label} — OpenCV Features Ada`]),
  ...PACKAGES.map((name) => [`api/${anchors.packages[name].page}`, `${name} — OpenCV Features Ada`])]);

async function metadata(document, route, label) {
  await document.waitForFunction(() => document.documentElement && document.readyState === 'complete');
  const actual = await document.evaluate(() => ({ title: document.title,
    titles: document.querySelectorAll('title').length, lang: document.documentElement.lang,
    charset: document.characterSet, heads: document.querySelectorAll('head').length }));
  check(`metadata ${label}: source-owned title, language and UTF-8`,
        actual.title === TITLES.get(route) && actual.titles === 1 && actual.lang === 'en' &&
        actual.charset === 'UTF-8' && actual.heads === 1, actual);
}

async function frameHeading(page, expected) {
  const deadline = Date.now() + 10000;
  let last = null;
  while (Date.now() < deadline) {
    const frame = frameOf(page);
    try {
      last = frame && await frame.evaluate(() =>
        document.readyState === 'complete' ? (document.querySelector('h1') || {}).textContent : null);
    } catch (_) { last = null; }
    if (last === expected) return last;
    await page.waitForTimeout(50);
  }
  return last;
}

async function heading(page, route, expected) {
  if (route !== 'api/index.html') return page.textContent('h1');
  await page.waitForSelector('#package-navigation:not([hidden])');
  return frameHeading(page, expected);
}

function monitor(page) {
  const seen = { requests: [], failures: [], errors: [] };
  page.on('request', (r) => seen.requests.push(r.url()));
  page.on('requestfailed', (r) => seen.failures.push(r.url()));
  page.on('response', (r) => { if (r.status() >= 400) seen.failures.push(`${r.status()} ${r.url()}`); });
  page.on('pageerror', (e) => seen.errors.push(String(e)));
  page.on('console', (m) => { if (m.type() === 'error') seen.errors.push(m.text()); });
  return seen;
}

async function routes(browser, scheme) {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: scheme });
  const page = await context.newPage();
  const seen = monitor(page);
  const themed = scheme === 'dark' ? 'rgb(20, 27, 38)' : 'rgb(255, 255, 255)';
  for (const [route, label, expected] of ROUTES) {
    for (const list of Object.values(seen)) list.length = 0;
    const response = await page.goto(root + route);
    const h1 = await heading(page, route, expected);
    await metadata(page, route, `${scheme} ${label}`);
    if (route === 'api/index.html')
      await metadata(frameOf(page), `api/${anchors.packages[expected].page}`, `${scheme} loaded iframe`);
    check(`${scheme} ${label}: ${prefix}${route} loads with its heading`,
          response.status() === 200 && page.url().startsWith(root + route) && h1 === expected,
          { status: response.status(), url: page.url(), h1 });
    const style = await page.evaluate(() => ({
      linked: document.querySelectorAll('link[rel=stylesheet]').length,
      sheets: Array.from(document.styleSheets, (s) => {
        let rules = -1;
        try { rules = s.cssRules.length; } catch (_) { /* not readable */ }
        return { href: s.href, rules };
      }),
      background: getComputedStyle(document.documentElement).backgroundColor,
    }));
    check(`${scheme} ${label}: stylesheets load from the prefix and the theme applies`,
          style.linked > 0 && style.sheets.length === style.linked && style.background === themed &&
          style.sheets.every((s) => s.href && under(s.href) && s.rules > 0), style);
    check(`${scheme} ${label}: every request stays under the prefix, without failures or errors`,
          seen.requests.length > 0 && seen.requests.every(under) && seen.failures.length === 0 &&
          seen.errors.length === 0, { outside: seen.requests.filter((u) => !under(u)),
                                      failures: [...seen.failures], errors: [...seen.errors] });
  }
  await context.close();
}

async function crawl(browser) {
  const context = await browser.newContext();
  const page = await context.newPage();
  const documents = new Map();
  async function load(target) {
    if (!documents.has(target)) {
      documents.set(target, await page.evaluate(async (url) => {
        const response = await fetch(url);
        const text = await response.text();
        const ids = response.headers.get('content-type').startsWith('text/html')
          ? Array.from(new DOMParser().parseFromString(text, 'text/html').querySelectorAll('[id]'), (e) => e.id)
          : [];
        return { status: response.status, redirected: response.redirected, ids };
      }, target));
    }
    return documents.get(target);
  }
  let total = 0;
  for (const [route, label] of ROUTES) {
    await page.goto(root + route);
    const references = await page.$$eval('[href], [src]', (elements) => elements.map((e) => {
      const value = e.getAttribute(e.hasAttribute('href') ? 'href' : 'src');
      return { value, url: new URL(value, document.baseURI).href };
    }));
    const problems = [];
    for (const { value, url } of references) {
      if (!under(url)) { problems.push(`${value} leaves the prefix`); continue; }
      const target = new URL(url);
      const fragment = decodeURIComponent(target.hash.slice(1));
      target.hash = '';
      const loaded = await load(target.href);
      if (loaded.status !== 200 || loaded.redirected) problems.push(`${value}: ${loaded.status}`);
      else if (fragment && !loaded.ids.includes(fragment)) problems.push(`${value}: no fragment`);
    }
    total += references.length;
    check(`links ${label}: all ${references.length} references resolve under the prefix`,
          references.length > 0 && problems.length === 0, problems);
  }
  check(`links: ${total} references from ${ROUTES.length} pages crawled`, total > 0, total);
  await context.close();
}

async function bareRoot(browser) {
  const context = await browser.newContext();
  const page = await context.newPage();
  const response = await page.goto(root.slice(0, -1));
  check(`redirect: ${prefix.slice(0, -1)} without a slash reaches the portal`,
        response.status() === 200 && page.url() === root &&
        (await page.textContent('h1')) === 'OpenCV Features for Ada', page.url());
  await page.click('header nav a:text-is("API Reference")');
  await page.waitForSelector('#package-navigation:not([hidden])');
  check('redirect: relative navigation from the redirected portal stays under the prefix',
        new URL(page.url()).pathname === `${prefix}api/index.html` &&
        await frameHeading(page, PACKAGES[0]) === PACKAGES[0], page.url());
  await context.close();
}

async function portalNavigation(browser) {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();
  for (const guide of siteMap.guides) {
    await page.goto(root);
    await page.click(`header nav a:text-is("${guide.label}")`);
    check(`navigation: portal opens ${guide.path} under the prefix`,
          page.url() === root + guide.path && (await page.textContent('h1')) === guide.label, page.url());
  }
  await page.click('header nav a:text-is("Home")');
  check('navigation: guide Home returns to the portal under the prefix',
        under(page.url()) && (await page.textContent('h1')) === 'OpenCV Features for Ada', page.url());
  await context.close();
}

async function apiNavigation(browser) {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();
  const errors = monitor(page).errors;
  const state = () => ({ path: new URL(page.url()).pathname, packages: new URL(page.url()).searchParams.getAll('package'),
                         frame: frameOf(page).url() });
  await page.goto(`${root}api/index.html`);
  await page.waitForSelector('#package-navigation:not([hidden])');
  await frameHeading(page, PACKAGES[0]);
  let now = state();
  check('JavaScript: the default package bookmark keeps the prefixed path',
        now.path === `${prefix}api/index.html` && JSON.stringify(now.packages) === JSON.stringify([PACKAGES[0]]) &&
        under(now.frame), now);
  await page.click('#compilation-units + ul a:text-is("OpenCV.Features.ORB")');
  const orb = await frameHeading(page, 'OpenCV.Features.ORB');
  now = state();
  check('JavaScript: package navigation pushes ?package on the prefixed path and loads ORB',
        orb === 'OpenCV.Features.ORB' && now.path === `${prefix}api/index.html` &&
        JSON.stringify(now.packages) === JSON.stringify(['OpenCV.Features.ORB']) && now.frame === root + ORB, now);
  await page.goBack();
  const back = await frameHeading(page, PACKAGES[0]);
  now = state();
  check('JavaScript: Back restores the previous package on the prefixed path',
        back === PACKAGES[0] && now.path === `${prefix}api/index.html` &&
        JSON.stringify(now.packages) === JSON.stringify([PACKAGES[0]]), now);
  await page.goto(`${root}api/index.html?package=OpenCV.Features.Matching`);
  await page.waitForSelector('#package-navigation:not([hidden])');
  check('bookmark: a prefixed ?package URL opens that package',
        await frameHeading(page, 'OpenCV.Features.Matching') === 'OpenCV.Features.Matching', page.url());
  check('JavaScript: no page or console errors', errors.length === 0, errors);
  await context.close();
}

async function anchorsUnderPrefix(browser) {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();
  const masked = Object.entries(anchors.declarations).filter(([identity]) =>
    identity.startsWith('OpenCV.Features.ORB.Detect_And_Compute|')).map(([, v]) => v.anchor);
  await page.goto(`${root}guides/orb-extraction.html`);
  await page.click('main a:text-is("masked overload")');
  await page.waitForFunction(() => location.hash.length > 1);
  const landed = await page.evaluate(() => {
    const h = document.getElementById(location.hash.slice(1));
    return { path: location.pathname, id: h && h.id, text: h && h.textContent,
             target: h && h.matches(':target'), code: h && h.nextElementSibling.textContent };
  });
  check('overload: the masked Detect_And_Compute link lands on its section under the prefix',
        landed.path === prefix + ORB && masked.includes(landed.id) && landed.text === 'Detect_And_Compute' &&
        landed.target && landed.code.includes('Image, Mask'), landed);
  const create = Object.entries(anchors.declarations)
    .find(([identity]) => identity.startsWith('OpenCV.Features.ORB.Create|'))[1].anchor;
  await page.goto(`${root}${ORB}#${create}`);
  const target = await page.evaluate((id) => {
    const h = document.getElementById(id);
    const r = h.getBoundingClientRect();
    return { matches: h.matches(':target'), top: r.top, height: innerHeight, text: h.textContent };
  }, create);
  check('bookmark: a prefixed declaration URL targets and scrolls to Create',
        target.matches && target.text === 'Create' && target.top >= 0 && target.top < target.height, target);
  await context.close();
}

async function metadataNavigation(browser) {
  for (const javaScriptEnabled of [true, false]) {
    const context = await browser.newContext({ javaScriptEnabled, viewport: { width: 390, height: 844 } });
    const page = await context.newPage();
    const seen = monitor(page);
    for (const [route, label] of ROUTES) {
      await page.goto(root + route);
      await metadata(page, route, `mobile JS=${javaScriptEnabled} ${label}`);
      await page.reload();
      await metadata(page, route, `reload JS=${javaScriptEnabled} ${label}`);
    }
    await page.goto(root);
    await page.click('header nav a:text-is("Getting started")');
    await metadata(page, 'guides/getting-started.html', `guide navigation JS=${javaScriptEnabled}`);
    await page.goBack();
    await metadata(page, '', `Back JS=${javaScriptEnabled}`);
    await page.goForward();
    await metadata(page, 'guides/getting-started.html', `Forward JS=${javaScriptEnabled}`);
    await page.goto(root + 'api/index.html');
    await page.click('#compilation-units + ul a:text-is("OpenCV.Features.Matching")');
    const deadline = Date.now() + 10000;
    while (!frameOf(page).url().endsWith(anchors.packages['OpenCV.Features.Matching'].page) && Date.now() < deadline)
      await page.waitForTimeout(50);
    await metadata(frameOf(page), `api/${anchors.packages['OpenCV.Features.Matching'].page}`,
                   `loaded native iframe JS=${javaScriptEnabled}`);
    check(`metadata navigation JS=${javaScriptEnabled}: no errors or prefix escapes`,
          seen.errors.length === 0 && seen.failures.length === 0 && seen.requests.every(under), seen);
    await context.close();
  }
}

(async () => {
  const browser = await chromium.launch(process.env.CHROME ? { executablePath: process.env.CHROME } : {});
  const versions = {
    chromium: browser.version(),
    playwright: JSON.parse(fs.readFileSync(path.join(path.dirname(require.resolve(`${playwrightPath}/package.json`)), 'package.json'))).version,
    node: process.version,
  };
  try {
    for (const scheme of ['light', 'dark']) await routes(browser, scheme);
    await crawl(browser);
    await bareRoot(browser);
    await portalNavigation(browser);
    await apiNavigation(browser);
    await anchorsUnderPrefix(browser);
    await metadataNavigation(browser);
  } finally {
    await browser.close();
  }
  const failed = assertions.filter((a) => !a.pass);
  const report = { versions, url: root, passed: assertions.length - failed.length, failed: failed.length, assertions };
  if (process.env.BROWSER_REPORT) fs.writeFileSync(process.env.BROWSER_REPORT, JSON.stringify(report, null, 2) + '\n');
  for (const a of assertions) console.log(`${a.pass ? 'PASS' : 'FAIL'} ${a.name}${a.pass ? '' : ' ' + JSON.stringify(a.detail)}`);
  console.log(`Chromium ${versions.chromium}, Playwright ${versions.playwright}: ${report.passed}/${assertions.length} assertions passed`);
  process.exit(failed.length ? 1 : 0);
})().catch((error) => { console.error(error); process.exit(1); });
