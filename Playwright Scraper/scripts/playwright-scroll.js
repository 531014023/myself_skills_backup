#!/usr/bin/env node
/**
 * Playwright Scroll Scraper
 * 適用：懒加载页面（微信等），需要滚动触发内容加载
 * 速度：慢（視內容量）
 */

const { chromium } = require('playwright');

const url = process.argv[2];
const waitTime = parseInt(process.env.WAIT_TIME || '5000'); // 每次滚动后等待时间
const maxScrolls = parseInt(process.env.MAX_SCROLLS || '30'); // 最大滚动次数

if (!url) {
    console.error('❌ 請提供 URL');
    console.error('用法: node playwright-scroll.js <URL>');
    process.exit(1);
}

(async () => {
    console.log('🔽 啟動滾動版爬蟲...');
    const startTime = Date.now();

    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    await page.setViewportSize({ width: 390, height: 844 }); // iPhone 14 Pro

    console.log(`📱 導航到: ${url}`);
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000); // 初始等待

    let lastHeight = 0;
    let scrollCount = 0;
    let noChangeCount = 0;
    const maxNoChange = 5; // 连续5次滚动内容不变则停止

    console.log('🔄 開始滾動加載...');
    while (scrollCount < maxScrolls && noChangeCount < maxNoChange) {
        // 滚动到页面底部
        await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
        await page.waitForTimeout(waitTime);

        const newHeight = await page.evaluate(() => document.body.scrollHeight);
        const currentText = await page.evaluate(() => document.body.innerText.length);

        if (newHeight === lastHeight) {
            noChangeCount++;
            console.log(`  ${scrollCount + 1}次滾動，高度不變(${currentText}字)，連續${noChangeCount}次`);
        } else {
            noChangeCount = 0;
            console.log(`  ${scrollCount + 1}次滾動，高度${lastHeight}→${newHeight}，內容${currentText}字`);
        }

        lastHeight = newHeight;
        scrollCount++;
    }

    console.log(`✅ 滾動完成，共${scrollCount}次，內容${await page.evaluate(() => document.body.innerText.length)}字`);

    // 获取完整内容
    const result = await page.evaluate(() => {
        return {
            title: document.title,
            url: window.location.href,
            content: document.body.innerText,
            metaDescription: document.querySelector('meta[name="description"]')?.content || '',
        };
    });

    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    result.elapsedSeconds = elapsed;
    result.scrollCount = scrollCount;

    console.log('\n✅ 爬取完成！');
    console.log(`內容長度: ${result.content.length} 字`);
    console.log(JSON.stringify(result, null, 2));

    await browser.close();
})();
