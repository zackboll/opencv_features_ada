'use strict';
// Chromium qualification of the enhanced Features site. Not a cross-browser or
// complete accessibility certification. Environment:
//   PLAYWRIGHT_MODULE  path of an installed playwright package
//   DOC_URL            http URL of the enhanced api/index.html
//   CHROME             optional Chromium executable
//   BROWSER_REPORT     optional JSON report path
const fs = require('fs');
const path = require('path');
const playwrightPath = process.env.PLAYWRIGHT_MODULE || 'playwright';
const { chromium } = require(playwrightPath);
const base = process.env.DOC_URL;
if (!base) throw new Error('DOC_URL is required');

const PACKAGES = ['OpenCV.Features', 'OpenCV.Features.Correspondences',
                  'OpenCV.Features.Matching', 'OpenCV.Features.ORB'];
const assertions = [];
function check(name, condition, detail) {
  assertions.push({ name, pass: Boolean(condition), detail: detail === undefined ? null : detail });
}
const url = (suffix) => new URL(suffix, base).href;
const frameOf = (page) => page.frame({ name: 'document-content' });

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

async function packageParameter(page) {
  return new URL(page.url()).searchParams.getAll('package');
}

async function desktop(browser, scheme) {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: scheme });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', (error) => errors.push(String(error)));
  page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()); });
  await page.goto(url('index.html'));
  await page.waitForSelector('#package-navigation:not([hidden])');
  const names = await page.$$eval('#compilation-units + ul a', (links) => links.map((a) => a.textContent));
  check(`${scheme}: index lists exactly the four public packages`, JSON.stringify(names) === JSON.stringify(PACKAGES), names);
  check(`${scheme}: default package loads in the frame`, await frameHeading(page, PACKAGES[0]) === PACKAGES[0]);
  check(`${scheme}: default package is bookmarked with replaceState`,
        JSON.stringify(await packageParameter(page)) === JSON.stringify([PACKAGES[0]]), page.url());
  check(`${scheme}: aria-current marks the selected package`,
        await page.$eval('a[aria-current="page"]', (a) => a.textContent) === PACKAGES[0]);
  const background = await page.evaluate(() => getComputedStyle(document.documentElement).backgroundColor);
  check(`${scheme}: themed index background`, scheme === 'dark' ? background === 'rgb(20, 27, 38)'
        : background === 'rgb(255, 255, 255)', background);

  if (scheme === 'light') {
    await page.click('#compilation-units + ul a:text-is("OpenCV.Features.ORB")');
    check('navigation: package link loads ORB in the frame', await frameHeading(page, 'OpenCV.Features.ORB') === 'OpenCV.Features.ORB');
    check('navigation: package click pushes a ?package bookmark',
          JSON.stringify(await packageParameter(page)) === JSON.stringify(['OpenCV.Features.ORB']), page.url());
    await page.goBack();
    check('history: Back restores the previous package and URL',
          await frameHeading(page, PACKAGES[0]) === PACKAGES[0] &&
          JSON.stringify(await packageParameter(page)) === JSON.stringify([PACKAGES[0]]), page.url());
    await page.goForward();
    check('history: Forward returns to ORB',
          await frameHeading(page, 'OpenCV.Features.ORB') === 'OpenCV.Features.ORB' &&
          JSON.stringify(await packageParameter(page)) === JSON.stringify(['OpenCV.Features.ORB']), page.url());

    await page.fill('#package-search', 'match');
    const visible = await page.$$eval('#compilation-units + ul li', (items) =>
      items.filter((li) => !li.hidden).map((li) => li.textContent));
    check('search: filters the package list', JSON.stringify(visible) === JSON.stringify(['OpenCV.Features.Matching']), visible);
    check('search: announces the result count', (await page.textContent('#package-results')) === '1 results');
    await page.click('#package-clear');
    check('search: Clear restores every entry', (await page.textContent('#package-results')) === '5 results');

    await page.keyboard.press('Tab');
    let focus = null;
    for (let i = 0; i < 12 && !(focus && focus.tag === 'A'); i++) {
      focus = await page.evaluate(() => {
        const e = document.activeElement, s = getComputedStyle(e);
        return { tag: e.tagName, style: s.outlineStyle, width: s.outlineWidth, text: e.textContent };
      });
      if (!(focus && focus.tag === 'A')) await page.keyboard.press('Tab');
    }
    check('keyboard: a focused link shows a visible outline', focus && focus.tag === 'A' &&
          focus.style === 'solid' && focus.width === '3px', focus);
    check(`${scheme}: no page or console errors`, errors.length === 0, errors);
  } else {
    check(`${scheme}: no page or console errors`, errors.length === 0, errors);
  }
  await context.close();
}

async function bookmarks(browser) {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();
  await page.goto(url('index.html?package=OpenCV.Features.Matching'));
  await page.waitForSelector('#package-navigation:not([hidden])');
  check('bookmark: ?package opens that package directly',
        await frameHeading(page, 'OpenCV.Features.Matching') === 'OpenCV.Features.Matching');
  await page.goto(url('index.html?package=No.Such.Package'));
  await page.waitForSelector('#package-navigation:not([hidden])');
  check('bookmark: an unknown package falls back to the first package',
        await frameHeading(page, PACKAGES[0]) === PACKAGES[0]);
  await context.close();
}

async function declarations(browser, scheme, anchors) {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: scheme });
  const page = await context.newPage();
  const orb = anchors.packages['OpenCV.Features.ORB'].page;
  const create = Object.entries(anchors.declarations)
    .find(([identity]) => identity.startsWith('OpenCV.Features.ORB.Create|'))[1].anchor;
  const configuration = Object.entries(anchors.declarations)
    .find(([identity]) => identity.startsWith('OpenCV.Features.ORB.Configuration|'))[1].anchor;
  await page.goto(url(`${orb}#${create}`));
  const target = await page.evaluate((id) => {
    const h = document.getElementById(id);
    const r = h.getBoundingClientRect();
    return { matches: h.matches(':target'), top: r.top, height: innerHeight, text: h.textContent };
  }, create);
  check(`${scheme}: declaration bookmark targets and scrolls to Create`,
        target.matches && target.text === 'Create' && target.top >= 0 && target.top < target.height, target);
  const keyword = await page.evaluate(() => {
    const k = document.querySelector('.ada-code-snippet .ada-keyword');
    const c = document.querySelector('.ada-code-snippet');
    return k && { keyword: getComputedStyle(k).color, code: getComputedStyle(c).color,
                  weight: getComputedStyle(k).fontWeight, count: document.querySelectorAll('.ada-code-snippet .ada-keyword').length };
  });
  check(`${scheme}: Ada keywords are highlighted`, keyword && keyword.count > 0 &&
        keyword.keyword !== keyword.code && keyword.weight === '700', keyword);
  const pageBackground = await page.evaluate(() => getComputedStyle(document.documentElement).backgroundColor);
  check(`${scheme}: themed declaration page background`, scheme === 'dark' ? pageBackground === 'rgb(20, 27, 38)'
        : pageBackground === 'rgb(255, 255, 255)', pageBackground);
  if (scheme === 'light') {
    await page.click(`a.type-reference[href$="#${configuration}"]`);
    await page.waitForFunction((id) => location.hash === `#${id}`, configuration);
    check('type link: navigates to the Configuration declaration anchor',
          await page.evaluate((id) => document.getElementById(id).matches(':target') &&
            document.getElementById(id).textContent === 'Configuration', configuration));
    const scripts = await page.$$eval('script', (list) => list.length);
    check('declaration pages run no scripts', scripts === 0, scripts);
  }
  await context.close();
}

async function mobile(browser, scheme, anchors) {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, colorScheme: scheme,
                                             isMobile: true, hasTouch: true, deviceScaleFactor: 2 });
  const page = await context.newPage();
  await page.goto(url('index.html'));
  await page.waitForSelector('#package-navigation:not([hidden])');
  const layout = await page.evaluate(() => ({
    display: getComputedStyle(document.body).display,
    overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    frame: document.querySelector('iframe').getBoundingClientRect().height,
  }));
  check(`${scheme} mobile: stacked layout without horizontal page overflow`,
        layout.display === 'flex' && layout.overflow <= 0 && layout.frame > 100, layout);
  check(`${scheme} mobile: package frame loads`, await frameHeading(page, PACKAGES[0]) === PACKAGES[0]);
  const orb = anchors.packages['OpenCV.Features.ORB'].page;
  await page.goto(url(orb));
  const content = await page.evaluate(() => ({
    overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    snippetScroll: getComputedStyle(document.querySelector('.ada-code-snippet')).overflowX,
  }));
  check(`${scheme} mobile: declaration page has no horizontal page overflow`,
        content.overflow <= 0 && content.snippetScroll === 'auto', content);
  await context.close();
}

async function noJavaScript(browser, anchors) {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto(url('index.html'));
  check('no JavaScript: search controls stay hidden', await page.$eval('#package-navigation', (e) => e.hidden));
  await page.click('#compilation-units + ul a:text-is("OpenCV.Features.Matching")');
  const deadline = Date.now() + 10000;
  let frameUrl = '';
  while (Date.now() < deadline && !frameUrl.endsWith(anchors.packages['OpenCV.Features.Matching'].page)) {
    frameUrl = frameOf(page).url();
    await page.waitForTimeout(50);
  }
  check('no JavaScript: native package link loads the page into the frame',
        frameUrl.endsWith(anchors.packages['OpenCV.Features.Matching'].page), frameUrl);
  const tagged = await page.$eval('#tagged-types + ul a', (a) => a.getAttribute('href'));
  check('no JavaScript: tagged-type link keeps its native fragment',
        tagged.endsWith(`#${anchors.declarations[Object.keys(anchors.declarations)
          .find((k) => k.startsWith('OpenCV.Features.ORB.Detector|'))].anchor}`), tagged);
  await context.close();
}

(async () => {
  const anchors = JSON.parse(fs.readFileSync(path.join(__dirname, '../../docs/gnatdoc-native-anchors.json')));
  const browser = await chromium.launch(process.env.CHROME ? { executablePath: process.env.CHROME } : {});
  const versions = {
    chromium: browser.version(),
    playwright: JSON.parse(fs.readFileSync(path.join(path.dirname(require.resolve(`${playwrightPath}/package.json`)), 'package.json'))).version,
    node: process.version,
  };
  try {
    for (const scheme of ['light', 'dark']) {
      await desktop(browser, scheme);
      await declarations(browser, scheme, anchors);
      await mobile(browser, scheme, anchors);
    }
    await bookmarks(browser);
    await noJavaScript(browser, anchors);
  } finally {
    await browser.close();
  }
  const failed = assertions.filter((a) => !a.pass);
  const report = { versions, url: base, passed: assertions.length - failed.length, failed: failed.length, assertions };
  if (process.env.BROWSER_REPORT) fs.writeFileSync(process.env.BROWSER_REPORT, JSON.stringify(report, null, 2) + '\n');
  for (const a of assertions) console.log(`${a.pass ? 'PASS' : 'FAIL'} ${a.name}${a.pass ? '' : ' ' + JSON.stringify(a.detail)}`);
  console.log(`Chromium ${versions.chromium}, Playwright ${versions.playwright}: ${report.passed}/${assertions.length} assertions passed`);
  process.exit(failed.length ? 1 : 0);
})().catch((error) => { console.error(error); process.exit(1); });
